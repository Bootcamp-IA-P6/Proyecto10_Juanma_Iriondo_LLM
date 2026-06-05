import os
import sys
import requests
from dotenv import load_dotenv
from groq import Groq

# Añade la carpeta superior al path de búsqueda de Python
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.utils import *


def stream_ollama(prompt, model, temperature, max_tokens):
    payload = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True
    }

    ollama_url = get_ollama_url()

    response = requests.post(
        ollama_url,
        json=payload,
        stream=True,
        timeout=300
    )

    response.raise_for_status()

    for line in response.iter_lines():
        if not line:
            continue

        try:
            data = requests.models.complexjson.loads(line)

            if "response" in data:
                yield data["response"]

        except Exception:
            pass


def stream_groq(prompt, model, temperature, max_tokens):

    client = Groq(api_key=get_groq_api_key())

    stream = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True
    )

    for chunk in stream:

        delta = chunk.choices[0].delta.content

        if delta:
            yield delta


def stream_response(prompt, MODELS, session_state):

    model = session_state.selected_model

    provider = MODELS[model]["provider"]

    if provider == "ollama":
        yield from stream_ollama(prompt, model, session_state.temperature, session_state.max_tokens)

    elif provider == "groq1" or provider == "groq2":
        yield from stream_groq(prompt, model, session_state.temperature, session_state.max_tokens)