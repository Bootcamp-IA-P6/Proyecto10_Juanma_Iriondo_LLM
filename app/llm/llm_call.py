import os
import sys

import requests
from dotenv import load_dotenv
from groq import Groq

from ollama import Client


# from langchain_groq import ChatGroq
# from langchain_community.chat_models import ChatOllama
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser



# Añade la carpeta superior al path de búsqueda de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.utils import *


def call_ollama_cloud():
    # Inicializa el cliente apuntando a Ollama Cloud con tu API Key
    client = Client(
        host='https://ollama.com',
        headers={'Authorization': f"Bearer {get_ollama_api_key()}"}
    )

    response = client.chat(
        model='gemma4:31b-cloud', # Reemplaza con el modelo cloud deseado
        messages=[
            {
                'role': 'user',
                'content': 'Explícame qué es python en 50 palabras'
            }
        ]
    )

    return response['message']['content']


def call_ollama_estadisticas(prompt, model, temperature, max_tokens):
    # Asegúrate de que esta URL termine en /api/generate
    ollama_url = get_ollama_url() 

    response = requests.post(
        ollama_url,
        json={
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens  # Nota: Ollama usa 'num_predict' para max_tokens
            },
            "stream": False
        }
    )

    response.raise_for_status()
    data = response.json()

    # Estructuramos la salida para incluir las estadísticas
    resultado = {
        "text": data.get("response"),
        "stats": {
            "tokens_enviados": data.get("prompt_eval_count", 0),
            "tokens_recibidos": data.get("eval_count", 0),
            "tiempo_total_ms": data.get("total_duration", 0) / 1_000_000 # De nanosegundos a milisegundos
        }
    }

    return resultado


def call_groq_estadisticas(prompt, model, temperature, max_tokens):
    client = Groq(api_key=get_groq_api_key())

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False
    )

    # Extraemos el objeto de uso de tokens
    usage = completion.usage

    resultado = {
        "text": completion.choices[0].message.content,
        "stats": {
            "tokens_enviados": usage.prompt_tokens,      # Tokens del prompt
            "tokens_recibidos": usage.completion_tokens,  # Tokens generados
            "tokens_totales": usage.total_tokens,        # Suma de ambos
            "tiempo_total_seg": getattr(usage, 'total_time', None) # Tiempo si Groq lo incluye
        }
    }

    return resultado


def call_ollama(prompt, model, temperature, max_tokens):

    ollama_url = get_ollama_url()

    response = requests.post(
        ollama_url,
        json={
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
    )

    response.raise_for_status()

    return response.json()["response"]


def call_groq(prompt, model, temperature, max_tokens):

    client = Groq(api_key=get_groq_api_key())

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False
    )

    return completion.choices[0].message.content


def call_response(prompt, MODELS, session_state):

    model = session_state.selected_model

    provider = MODELS[model]["provider"]

    if provider == "ollama":
        # return call_ollama(prompt, model, session_state.temperature, session_state.max_tokens)
        return call_ollama_estadisticas(prompt, model, session_state.temperature, session_state.max_tokens)

    elif provider == "groq1" or provider == "groq2":
        # return call_groq(prompt, model, session_state.temperature, session_state.max_tokens)
        return call_groq_estadisticas(prompt, model, session_state.temperature, session_state.max_tokens)
    



# devuelve precios en $
def obtener_precios_modelos():
    url = "https://openrouter.ai/api/v1/models"
    
    # El User-Agent evita que los sistemas de seguridad bloqueen la petición de Python
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Lanza un error si el estatus HTTP no es 200
        
        # Validar si la respuesta realmente es un JSON válido
        try:
            data = response.json()
        except ValueError:
            print("Error: El servidor no respondió con un formato JSON válido.")
            print(f"Inicio de la respuesta del servidor:\n{response.text[:500]}")
            return

        # Procesar e imprimir los datos de los modelos
        for model in data.get('data', []):
            id_modelo = model.get('id')
            pricing = model.get('pricing', {})
            
            # Precios por millón de tokens (OpenRouter entrega el costo por token individual)
            prompt_price = float(pricing.get('prompt', 0)) * 1000000
            completion_price = float(pricing.get('completion', 0)) * 1000000
            
            print(f"Modelo: {id_modelo}")
            print(f"  - Entrada: ${prompt_price:.2f} por millón de tokens")
            print(f"  - Salida: ${completion_price:.2f} por millón de tokens")
            print("-" * 30)
            
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión o HTTP con la API: {e}")


def obtener_precios_openai_anthropic():
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

        print("=== LISTA DE MODELOS FILTRADOS ===")
        # Contador para saber cuántos modelos encontramos
        total_modelos = 0

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

                total_modelos += 1
                pricing = model.get('pricing', {})

                # Precio por token
                prompt_price = float(pricing.get('prompt', 0))
                completion_price = float(pricing.get('completion', 0))
                
                print(f"Modelo: {id_modelo}")

                modelo_str = f"{id_modelo}"
                print(modelo_str)

                print(f"  - Entrada: ${prompt_price:.6f} por token")
                print(f"  - Salida: ${completion_price:.6f} por token")
                print("-" * 30)

                # Añade datos a precios
                precio["modelo"] = modelo_str
                precio["precio_token_entrada"] = f"{prompt_price:.6f}"
                precio["precio_token_salida"] = f"{completion_price:.6f}"

                precios.append(precio)
                
        print(f"Se encontraron un total de {total_modelos} modelos de OpenAI y Anthropic.")

        print(precios)
        return precios
            
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")


if __name__ == "__main__":
    # obtener_precios_modelos()
    obtener_precios_openai_anthropic()