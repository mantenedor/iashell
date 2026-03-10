#!/usr/bin/env python3
import os
import sys
import glob
import atexit
import shlex
import readline
import re
import subprocess
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(os.environ.get("IA_ENV_FILE", "conf/.env"))
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

PROMPT_HISTORY_FILE = os.environ.get("PROMPT_HISTORY_FILE", "base/profile/.prompt_history")

from connector import ask
from memory import load_memory, build_system_prompt, append_history
from knowledge import (
    build_context_block,
    ingest_and_index,
    build_doc_context,
    sync_all_sources,
    format_document_catalog,
    list_documents,
)

CMD_PREFIX = "!"
INGEST_PREFIX = ":add "
DOCS_PREFIX = ":docs"

session_state = {
    "active_doc_id": None,
    "active_doc_name": None,
    "preferred_summary_style": None,
}


def ensure_parent(path_str: str):
    Path(path_str).parent.mkdir(parents=True, exist_ok=True)


def setup_readline():
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set editing-mode emacs")
    readline.set_completer_delims(" \t\n;")
    readline.set_completer(completer)

    history_path = Path(PROMPT_HISTORY_FILE)
    ensure_parent(str(history_path))

    if history_path.exists():
        try:
            readline.read_history_file(str(history_path))
        except Exception:
            pass

    atexit.register(save_history)


def save_history():
    history_path = Path(PROMPT_HISTORY_FILE)
    ensure_parent(str(history_path))
    try:
        readline.write_history_file(str(history_path))
    except Exception:
        pass


def complete_path(text):
    if not text:
        text = "."
    expanded = os.path.expanduser(text)
    matches = glob.glob(expanded + "*")
    out = []
    for item in matches:
        if os.path.isdir(item):
            out.append(item + "/")
        else:
            out.append(item)
    return sorted(out)


def completer(text, state):
    line = readline.get_line_buffer().lstrip()

    if line.startswith(INGEST_PREFIX):
        arg = line[len(INGEST_PREFIX):]
        try:
            parts = shlex.split(arg)
            current = "" if arg.endswith(" ") else (parts[-1] if parts else "")
        except ValueError:
            current = arg.strip()

        matches = complete_path(current)
        try:
            return matches[state]
        except IndexError:
            return None

    return None


def get_single_document():
    docs = list_documents()
    if len(docs) == 1:
        return docs[0]
    return None


def set_active_document(doc):
    if not doc:
        return
    session_state["active_doc_id"] = doc.get("doc_id")
    session_state["active_doc_name"] = doc.get("filename_original")


def find_doc_by_text(text: str):
    docs = list_documents()
    text_l = text.lower()

    for doc in docs:
        doc_id = str(doc.get("doc_id", "")).lower()
        name = str(doc.get("filename_original", "")).lower()
        if doc_id and doc_id in text_l:
            return doc
        if name and name in text_l:
            return doc

    return None


def infer_active_document(user_text: str):
    explicit = find_doc_by_text(user_text)
    if explicit:
        set_active_document(explicit)
        return explicit

    single = get_single_document()
    if single:
        set_active_document(single)
        return single

    if session_state.get("active_doc_id"):
        docs = list_documents()
        for doc in docs:
            if doc.get("doc_id") == session_state["active_doc_id"]:
                return doc

    return None


def is_list_docs_request(text: str) -> bool:
    t = text.lower()
    triggers = [
        "liste seus documentos",
        "liste os documentos",
        "quais documentos",
        "quais são seus documentos",
        "mostre os documentos",
        "listar documentos",
    ]
    return any(x in t for x in triggers)


def is_summary_request(text: str) -> bool:
    t = text.lower().strip()
    if t in {"resuma", "resumo", "sumarize", "sumário"}:
        return True
    triggers = [
        "resuma",
        "faça um resumo",
        "gere um resumo",
        "me dê um resumo",
        "resumo do documento",
        "resuma o documento",
    ]
    return any(x in t for x in triggers)


def maybe_update_summary_style(text: str) -> bool:
    t = text.lower().strip()
    if "seja objetivo" in t or "resumo mais breve" in t or "resumo breve" in t:
        session_state["preferred_summary_style"] = "breve e genérico"
        return True
    if "detalhado" in t:
        session_state["preferred_summary_style"] = "detalhado"
        return True
    if "executivo" in t:
        session_state["preferred_summary_style"] = "executivo"
        return True
    return False


def build_runtime_context(user_text: str, doc_context: str | None = None, force_mode: str | None = None) -> str:
    catalog = format_document_catalog(limit=30)
    context_block = build_context_block(user_text, limit=5)

    runtime_payload = {
        "user_request": user_text,
        "document_catalog": catalog,
        "document_focus": {
            "doc_id": session_state.get("active_doc_id"),
            "name": session_state.get("active_doc_name"),
            "context": doc_context or "",
        },
        "session_state": {
            "preferred_summary_style": session_state.get("preferred_summary_style"),
            "force_mode": force_mode,
        },
        "retrieved_context": context_block,
    }

    return f"RUNTIME_CONTEXT:\n{runtime_payload}"


setup_readline()

sync_all_sources()

memory = load_memory()
system_prompt = build_system_prompt(memory)

print("IA pronta (!comando para shell, :add <arquivo> para indexar, :docs para listar documentos, q ou quit para sair)\n")

while True:
    try:
        sync_all_sources()

        q = input("> ").strip()

        if q.lower() in ("q", "quit"):
            print("encerrando")
            sys.exit(0)

        if not q:
            continue

        if q == DOCS_PREFIX or is_list_docs_request(q):
            catalog = format_document_catalog(limit=100)
            docs = list_documents()
            if len(docs) == 1:
                set_active_document(docs[0])
            print(catalog if catalog else "Nenhum documento indexado.")
            print()
            continue

        if q.startswith(INGEST_PREFIX):
            file_path = os.path.expanduser(q[len(INGEST_PREFIX):].strip())
            if not file_path:
                print("Informe o caminho do arquivo.\n")
                continue

            try:
                meta = ingest_and_index(file_path, source_mode="manual")
                set_active_document(meta)
                print(f"Documento indexado: {meta['doc_id']} ({meta['type']})\n")
            except Exception as e:
                print(f"Erro ao indexar arquivo: {e}\n")
            continue

        if q.startswith(CMD_PREFIX):
            cmd = q[1:].strip()

            r = subprocess.run(
                cmd,
                shell=True,
                executable="/bin/bash",
                capture_output=True,
                text=True
            )

            stdout = r.stdout or ""
            stderr = r.stderr or ""

            print("\n--- saída do comando ---")
            if stdout:
                print(stdout, end="" if stdout.endswith("\n") else "\n")
            if stderr:
                print(stderr, end="" if stderr.endswith("\n") else "\n")
            if not stdout and not stderr:
                print("(sem saída)")
            print("--- fim ---\n")

            try:
                input("Pressione ENTER para enviar à IA ou Ctrl+C para cancelar: ")
            except KeyboardInterrupt:
                print("\ncancelado\n")
                continue

            shell_prompt = f"Comando executado localmente: {cmd}\n\nSaída:\n{stdout}\n{stderr}"
            prompt = build_runtime_context(shell_prompt)

            resp = ask(prompt, system_prompt=system_prompt)
            print(resp)
            print()
            append_history(prompt, resp)
            continue

        style_changed = maybe_update_summary_style(q)

        active_doc = infer_active_document(q)
        doc_context = None
        if active_doc:
            doc_context = build_doc_context(active_doc["doc_id"])

        if is_summary_request(q) and active_doc and doc_context:
            requested_style = session_state.get("preferred_summary_style")
            summary_request = f"Resumo do documento em foco: {active_doc['filename_original']}"
            if requested_style:
                summary_request += f" | estilo_preferido: {requested_style}"

            prompt = build_runtime_context(
                summary_request,
                doc_context=doc_context,
                force_mode="summary",
            )
            resp = ask(prompt, system_prompt=system_prompt)
            print(resp)
            print()
            append_history(prompt, resp)
            continue

        if style_changed and active_doc and doc_context:
            reformulation_request = f"Reformular resumo do documento em foco: {active_doc['filename_original']}"
            if session_state.get("preferred_summary_style"):
                reformulation_request += f" | estilo_preferido: {session_state['preferred_summary_style']}"

            prompt = build_runtime_context(
                reformulation_request,
                doc_context=doc_context,
                force_mode="summary",
            )
            resp = ask(prompt, system_prompt=system_prompt)
            print(resp)
            print()
            append_history(prompt, resp)
            continue

        prompt = build_runtime_context(q, doc_context=doc_context)

        resp = ask(prompt, system_prompt=system_prompt)
        print(resp)
        print()
        append_history(prompt, resp)

    except EOFError:
        print("\nencerrando")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\ninterrompido")
