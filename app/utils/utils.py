from dotenv import load_dotenv
import os
import requests

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

def get_unsplash_api_key():
    load_dotenv()
    unsplash_api_key = os.getenv("UNSPLASH_ACCESS_KEY")

    if not unsplash_api_key:
        raise RuntimeError(
            "No se encontró UNSPLASH_ACCESS_KEY"
        )

    return unsplash_api_key


def get_prices_openai_anthropic():
    url = "https://openrouter.ai/api/v1/models"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        try:
            data = response.json()
        except ValueError:
            print("Error: El servidor no respondió con un formato JSON válido.")
            return

        # Inicializa datos de salida
        precios=[]
        
        for model in data.get('data', []):
            id_modelo = model.get('id')
            
            # Filtro estricto: solo IDs que comiencen con openai/ o anthropic/
            if id_modelo.startswith("openai/gpt-5.5") or id_modelo.startswith("anthropic/claude-opus-4.8"):

                precio={
                    "modelo": "",
                    "precio_token_entrada": "",
                    "precio_token_salida": ""
                }

                pricing = model.get('pricing', {})

                # Precio por token
                prompt_price = float(pricing.get('prompt', 0))
                completion_price = float(pricing.get('completion', 0))

                # Convertir id_modelo a str
                modelo_str = f"{id_modelo}"

                # Añade datos a precios
                precio["modelo"] = modelo_str
                precio["precio_token_entrada"] = f"{prompt_price:.6f}"
                precio["precio_token_salida"] = f"{completion_price:.6f}"

                precios.append(precio)

        return precios
            
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")