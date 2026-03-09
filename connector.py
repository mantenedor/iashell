import os
from openai import OpenAI

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
