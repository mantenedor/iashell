#!/usr/bin/env python3
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def load_local_env():
    """Procura .env em vários locais possíveis"""
    possible_paths = [
        Path(os.environ.get("IA_ENV_FILE", "conf/.env")),
        Path("conf/.env"),
        Path.home() / "iashell/conf/.env",
        Path(".env")
    ]
    
    for env_file in possible_paths:
        if env_file.exists():
            load_dotenv(env_file)
            print(f"✅ Carregado .env de: {env_file}")
            return
    
    print("⚠️ Arquivo .env não encontrado. Usando variáveis de ambiente do sistema.")


load_local_env()

if "OPENAI_API_KEY" not in os.environ:
    raise RuntimeError(
        "\n❌ OPENAI_API_KEY não encontrada!\n"
        "Você precisa configurar sua chave da OpenAI.\n\n"
        "Opções:\n"
        "  1. Criar arquivo conf/.env com: OPENAI_API_KEY=sk-...\n"
        "  2. Criar arquivo ~/iashell/conf/.env\n"
        "  3. Exportar variável: export OPENAI_API_KEY=sk-...\n"
    )

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def ask(prompt, system_prompt=None):
    """Envia prompt para a OpenAI e retorna resposta"""
    input_data = []

    if system_prompt:
        input_data.append({
            "role": "system",
            "content": [{"type": "input_text", "text": system_prompt}]
        })

    input_data.append({
        "role": "user",
        "content": [{"type": "input_text", "text": prompt}]
    })

    try:
        r = client.responses.create(
            model="gpt-4",  # ou "gpt-3.5-turbo" para economia
            input=input_data
        )
        return r.output_text
    except Exception as e:
        return f"❌ Erro na API OpenAI: {e}"
