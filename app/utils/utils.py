from dotenv import load_dotenv
import os

def get_groq_api_key():
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "No se encontró GROQ_API_KEY"
        )

    return api_key

def get_ollama_url():
    load_dotenv()
    ollama_url = os.getenv("OLLAMA_URL")

    if not ollama_url:
        raise RuntimeError(
            "No se encontró OLLAMA_URL"
        )

    return ollama_url

def get_ollama_api_key():
    load_dotenv()
    ollama_api_key = os.getenv("OLLAMA_API_KEY")

    if not ollama_api_key:
        raise RuntimeError(
            "No se encontró OLLAMA_API_KEY"
        )

    return ollama_api_key