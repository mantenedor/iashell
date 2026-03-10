#!/usr/bin/env python3
import json
import os
from pathlib import Path

from dotenv import load_dotenv


def load_local_env():
    env_file = Path(os.environ.get("IA_ENV_FILE", "conf/.env"))
    if env_file.exists():
        load_dotenv(env_file)
    return env_file


ENV_FILE = load_local_env()

BASE_MEMORY_FILE = os.environ["BASE_MEMORY_FILE"]
OVERLAY_MEMORY_FILE = os.environ["OVERLAY_MEMORY_FILE"]
HISTORY_FILE = os.environ["HISTORY_FILE"]
CONTEXT_URLS_FILE = os.environ.get("CONTEXT_URLS_FILE", "")


def ensure_parent(path_str: str):
    Path(path_str).parent.mkdir(parents=True, exist_ok=True)


def deep_merge(base, overlay):
    if isinstance(base, dict) and isinstance(overlay, dict):
        result = dict(base)
        for k, v in overlay.items():
            if k in result:
                result[k] = deep_merge(result[k], v)
            else:
                result[k] = v
        return result
    return overlay


def build_base_memory(nome_agente, diretrizes_texto, estilo_resposta):
    return {
        "identidade": {
            "nome_agente": nome_agente
        },
        "diretrizes": {
            "texto": diretrizes_texto
        },
        "resposta": {
            "estilo": estilo_resposta
        },
        "controles": {
            "base_imutavel": True
        }
    }


def save_base_memory(memory: dict):
    ensure_parent(BASE_MEMORY_FILE)
    with open(BASE_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def save_overlay_memory(memory: dict):
    ensure_parent(OVERLAY_MEMORY_FILE)
    with open(OVERLAY_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def load_context_urls():
    if not CONTEXT_URLS_FILE:
        return []

    path = Path(CONTEXT_URLS_FILE)
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ask_bootstrap_questions():
    print("\nNenhuma memória local encontrada. Vamos criar a primeira.\n")

    nome_agente = input("Qual o meu nome? ").strip()
    diretrizes_texto = input("Quais as minha diretrizes? ").strip()
    estilo_resposta = input("Como gostaria que eu respondesse? ").strip()

    memory = build_base_memory(
        nome_agente=nome_agente,
        diretrizes_texto=diretrizes_texto,
        estilo_resposta=estilo_resposta
    )

    save_base_memory(memory)

    if not Path(OVERLAY_MEMORY_FILE).exists():
        save_overlay_memory({})

    return load_memory()


def load_base_memory():
    if not Path(BASE_MEMORY_FILE).exists():
        return ask_bootstrap_questions()

    with open(BASE_MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_overlay_memory():
    if not Path(OVERLAY_MEMORY_FILE).exists():
        save_overlay_memory({})
        return {}

    with open(OVERLAY_MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_memory():
    return deep_merge(load_base_memory(), load_overlay_memory())


def build_system_prompt(memory: dict) -> str:
    context_urls = load_context_urls()

    return f"""Use a memória persistente local abaixo como fonte principal de contexto e comportamento.

MEMÓRIA:
{json.dumps(memory, ensure_ascii=False, indent=2)}

URLS_DE_CONTEXTO:
{json.dumps(context_urls, ensure_ascii=False, indent=2)}

Interpretação da memória:
- identidade.nome_agente = nome do agente
- identidade.nome_usuario = nome do usuário, se existir
- diretrizes.texto = diretrizes do agente
- resposta.estilo = forma como o agente deve responder

Regras de execução:
- Siga estritamente a memória carregada.
- Não invente fatos, endpoints, campos, valores ou comportamentos.
- Se perguntarem seu nome e identidade.nome_agente existir, responda com esse valor.
- Se perguntarem o nome do usuário e identidade.nome_usuario existir, responda com esse valor.
- Nunca confunda nome_agente com nome_usuario.
- Se houver incerteza, declare claramente.
- Para ações destrutivas, peça confirmação explícita.
- A memória base original nunca deve ser alterada.
- Ajustes incrementais e correções devem ir apenas para o arquivo overlay.
"""


def append_history(user_text: str, assistant_text: str):
    ensure_parent(HISTORY_FILE)
    entry = {"user": user_text, "assistant": assistant_text}
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
