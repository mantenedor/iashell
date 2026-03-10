#!/usr/bin/env python3
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


def load_local_env():
    env_file = Path(os.environ.get("IA_ENV_FILE", "conf/.env"))
    if env_file.exists():
        load_dotenv(env_file)


load_local_env()

if "OPENAI_API_KEY" not in os.environ:
    raise RuntimeError("OPENAI_API_KEY ausente em conf/.env")

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def ask(prompt, system_prompt=None):
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

    r = client.responses.create(
        model="gpt-5",
        input=input_data
    )
    return r.output_text
