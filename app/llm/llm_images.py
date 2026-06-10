import os
import sys
from dotenv import load_dotenv

# Añade la carpeta superior al path de búsqueda de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.utils import *

# Libreria de Hugging Face
from huggingface_hub import InferenceClient
# Libreria para Unsplash
import requests
# Libreria de Pollinations
from urllib.parse import quote
from PIL import Image
from io import BytesIO

# Librerias para Google
from google import genai
# from io import BytesIO
# from PIL import Image
# Libreria de Google 2
import google.generativeai as genai

def get_image_unsplash(tema):
    # 1. Usamos el dominio correcto de la API y el endpoint de búsqueda
    url = "https://api.unsplash.com/search/photos"
    
    # 2. Pasamos los parámetros de forma limpia en un diccionario
    params = {
        "query": tema,
        "client_id": get_unsplash_api_key(),
        "per_page": 1 # Solo le pedimos 1 imagen para ir rápido
    }
    
    try:
        # requests se encarga de juntar la URL y los params correctamente con '?' y '&'
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # 3. Al buscar, Unsplash devuelve una lista en la propiedad 'results'
            if data['results']:
                primera_imagen = data['results'][0] # Tomamos el primer resultado
                
                #image_url = primera_imagen['urls']['regular'] # de 1080px
                #image_url = primera_imagen['urls']['thumb'] # de 200px
                image_url = primera_imagen['urls']['small'] # de 400px, ideal para web
                author = primera_imagen['user']['name']
                return image_url, author
            else:
                print(f"No se encontraron imágenes para: '{tema}'")
                return None, None
        else:
            print(f"Error {response.status_code} al conectar con Unsplash. Revisa tu Access Key.")
            return None, None
            
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return None, None   

def get_image_hugging_face(tema):
    client = InferenceClient(
        provider="wavespeed",
        api_key=get_hf_token(),
    )

    # output is a PIL.Image object
    image = client.text_to_image(
        # "A cute alien creature in a spaceship",
        # "elefante con alas volando",
        # "elephant with wings flying",
        # "imagen de un robot",
        tema,
        model="black-forest-labs/FLUX.1-dev",
        # width=500,
        # height=500,
    )

    # Redimensionar a 500x500 píxeles
    image = image.resize((500, 500))

def get_image_pollinations(tema, width=500, height=500):
    """
    Genera una imagen con Pollinations y devuelve un objeto PIL.Image.
    """

    POLLINATIONS_API_KEY = get_pollinations_api_key()

    url = (
        f"https://gen.pollinations.ai/image/"
        f"{quote(tema)}"
        f"?model=flux"
        f"&width={width}"
        f"&height={height}"
    )

    headers = {
        "Authorization": f"Bearer {POLLINATIONS_API_KEY}"
    }

    response = requests.get(url, headers=headers, timeout=120)

    if response.status_code != 200:
        raise Exception(
            f"Error {response.status_code}: {response.text}"
        )

    return Image.open(BytesIO(response.content))


def get_image_google(busqueda):
    """
    Conecta con la API de Google Gen AI usando el modelo Nano Banana
    y devuelve los bytes de la imagen generada.
    """
    
    # 1. Configurar la API Key de Google AI Studio
    GOOGLE_API_KEY = get_google_api_key() 

    try:
        # Inicializamos el cliente con la API Key
        client = genai.Client(api_key=GOOGLE_API_KEY)

        # for m in client.models.list():
        #     print(m.name)
        #     st.write(m.name)

        # for m in client.models.list():
        #     if "image" in m.name:
        #         print(m.name)
        #         print(m.supported_actions)
        #         print("------")
        
        # Llamada al modelo nativo de imágenes (Nano Banana 2)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[busqueda]
        )
        
        # Buscamos los bytes de la imagen en la respuesta de la IA
        for part in response.parts:
            if part.inline_data:
                # Retornamos los bytes puros de la imagen
                return part.inline_data.data
                
        return None
    except Exception as e:
        print(f"Error en la API de Google: {e}")
        return None