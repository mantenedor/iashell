#!/usr/bin/env python3
import os
import sys
import glob
import atexit
import shlex
import readline
import subprocess

from connector import ask
from memory import load_memory, build_system_prompt, append_history
from knowledge import build_context_block, ingest_and_index

CMD_PREFIX = "!"
INGEST_PREFIX = ":add "
HISTORY_PATH = "/data/ia/.prompt_history"


def setup_readline():
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set editing-mode emacs")
    readline.set_completer_delims(" \t\n;")
    readline.set_completer(completer)

    if os.path.exists(HISTORY_PATH):
        try:
            readline.read_history_file(HISTORY_PATH)
        except Exception:
            pass

    atexit.register(save_history)


def save_history():
    try:
        readline.write_history_file(HISTORY_PATH)
    except Exception:
        pass


def complete_path(text):
    if not text:
        text = "."

    expanded = os.path.expanduser(text)
    matches = glob.glob(expanded + "*")

    results = []
    for match in matches:
        if os.path.isdir(match):
            results.append(match + "/")
        else:
            results.append(match)

    return sorted(results)


def completer(text, state):
    line = readline.get_line_buffer()
    stripped = line.lstrip()

    if stripped.startswith(INGEST_PREFIX):
        arg = stripped[len(INGEST_PREFIX):]

        try:
            parts = shlex.split(arg)
            if arg.endswith(" "):
                current = ""
            else:
                current = parts[-1] if parts else ""
        except ValueError:
            current = arg.strip()

        matches = complete_path(current)

        try:
            return matches[state]
        except IndexError:
            return None

    return None


setup_readline()

memory = load_memory()
system_prompt = build_system_prompt(memory)

print("IA pronta (!comando para shell, :add <arquivo> para indexar, q ou quit para sair)\n")

while True:
    try:
        q = input("> ").strip()

        if q.lower() in ("q", "quit"):
            print("encerrando")
            sys.exit(0)

        if not q:
            continue

        if q.startswith(INGEST_PREFIX):
            file_path = q[len(INGEST_PREFIX):].strip()
            if not file_path:
                print("Informe o caminho do arquivo.\n")
                continue

            file_path = os.path.expanduser(file_path)

            try:
                meta = ingest_and_index(file_path)
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

            prompt = f"Comando executado localmente: {cmd}\n\nSaída:\n{stdout}\n{stderr}"
            context_block = build_context_block(prompt, limit=5)

            if context_block:
                prompt = f"{prompt}\n\nContexto documental recuperado:\n{context_block}"

            resp = ask(prompt, system_prompt=system_prompt)
            print(resp)
            print()
            append_history(prompt, resp)
            continue

        context_block = build_context_block(q, limit=5)
        prompt = q

        if context_block:
            prompt = f"{q}\n\nContexto documental recuperado:\n{context_block}"

        resp = ask(prompt, system_prompt=system_prompt)
        print(resp)
        print()
        append_history(prompt, resp)

    except EOFError:
        print("\nencerrando")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\ninterrompido")
