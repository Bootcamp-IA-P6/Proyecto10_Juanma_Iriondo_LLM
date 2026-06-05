import os
import sys
import requests
from dotenv import load_dotenv
from groq import Groq

from utils.utils import *

def call_ollama(prompt, model):

    ollama_url = get_ollama_url()

    response = requests.post(
        ollama_url,
        json={
            "model": model,
            "prompt": prompt,
            # "options": {"temperature": 0.2}
            "stream": False
        }
    )

    response.raise_for_status()

    return response.json()["response"]


def call_groq(prompt, model):

    client = Groq(api_key=get_groq_api_key())

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return completion.choices[0].message.content


def call_response(prompt, MODELS, session_state):

    model = session_state.selected_model

    provider = MODELS[model]["provider"]

    if provider == "ollama":
        return call_ollama(prompt, model)

    elif provider == "groq":
        return call_groq(prompt, model)