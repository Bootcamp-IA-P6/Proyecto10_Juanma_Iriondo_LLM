import os
import sys
# import requests
import streamlit as st
# from dotenv import load_dotenv
# from groq import Groq

# Añade la carpeta superior al path de búsqueda de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.utils import get_groq_api_key
from llm.llm_stream import *
from llm.llm_call import *

# =====================================================
# CONFIG
# =====================================================
ruta_actual = os.path.dirname(__file__)

st.set_page_config(
    page_title="AI Chat",
    page_icon=os.path.join(ruta_actual, "..", "logos", "irla_logo.png"),
    layout="wide"
)

MODELS = {
    "llama3.2:1b": {
        "provider": "ollama",
        "label": "Llama 3.2 1B (Local)"
    },
    "llama-3.3-70b-versatile": {
        "provider": "groq1",
        "label": "Llama 3.3 70B (Groq)"
    },
    "groq/compound-mini": {
        "provider": "groq2",
        "label": "Groq/Compound-mini (Groq)"
    }
}


# =====================================================
# CSS
# =====================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #0f172a;
    }

    [data-testid="stSidebar"] {
        /*background-color: #111827;*/
        background-color: #008B8B;
    }

    [data-testid="stSidebar"] * {
        color: white;
    }

    .main-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .model-badge {
        padding: 0.5rem;
        border-radius: 10px;
        background-color: #1e293b;
        margin-bottom: 1rem;
    }

    .welcome-box {
        text-align: center;
        padding: 3rem;
        border-radius: 12px;
        background-color: #111827;
        margin-top: 2rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# SESSION STATE
# =====================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "selected_model" not in st.session_state:
    st.session_state.selected_model = "llama3.2:1b"

if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7

if "max_tokens" not in st.session_state:
    st.session_state.max_tokens = 2048

if "hashtags" not in st.session_state:
    st.session_state.hashtags = 2

if "words" not in st.session_state:
    st.session_state.words = 50


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:
    col1, col2 = st.columns([2, 4])  # Ajusta las proporciones según el tamaño de tu logo

    with col1:
        ruta_logo = os.path.join(ruta_actual, "..", "logos", "irla_logo.png")
        st.image(ruta_logo, width=50)

    with col2:
        st.markdown("# IRLA Chat")
    

    if st.button("➕ Nuevo chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    menu = st.radio(
        "Navegación",
        [
            "💬 Chat",
            "📚 Historial",
            "👽 Modelos",
            "⚙️ Configuración"
        ]
    )

    st.divider()

    st.selectbox(
        "Modelo",
        options=list(MODELS.keys()),
        index=list(MODELS.keys()).index(
            st.session_state.selected_model
        ),
        key="selected_model",
        format_func=lambda x: MODELS[x]["label"]
    )


# =====================================================
# CHAT
# =====================================================

if menu == "💬 Chat":
    st.markdown(
        '<div class="main-title">💬 Chat</div>',
        unsafe_allow_html=True
    )

    provider = MODELS[
        st.session_state.selected_model
    ]["provider"]

    badge = (
        "🖥️ Local"
        if provider == "ollama"
        else "☁️ Groq"
    )

    st.markdown(
        f"""
        <div class="model-badge">
        {badge} |
        <b>{st.session_state.selected_model}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not st.session_state.messages:
        col11, col12 = st.columns([1, 5])  # Ajusta las proporciones según el tamaño de tu logo

        with col11:
            ruta_logo3 = os.path.join(ruta_actual, "..", "logos", "irla_logo_transparente.png")
            st.image(ruta_logo3, width=500)

        with col12:
            st.markdown(
                """
                <div class="welcome-box">  
                    <h2>Bienvenido a Inteligencia Rápida Ligera Artificial</h2>
                    <p>
                        Selecciona un modelo y comienza
                        una conversación.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

    for msg in st.session_state.messages:

        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input(
        "Escribe tu mensaje..."
    )

    if prompt:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            placeholder = st.empty()

            full_response = ""

            try:

                for chunk in stream_response(prompt, MODELS, st.session_state):

                    full_response += chunk

                    placeholder.markdown(
                        full_response + "▌"
                    )

                placeholder.markdown(
                    full_response
                )

            except Exception as e:

                full_response = (
                    f"❌ Error: {str(e)}"
                )

                placeholder.error(
                    full_response
                )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": full_response
            }
        )

# =====================================================
# HISTORIAL
# =====================================================

elif menu == "📚 Historial":

    st.title("📚 Historial")

    st.write(
        f"Mensajes almacenados en memoria: "
        f"{len(st.session_state.messages)}"
    )

    if st.session_state.messages:

        for i, msg in enumerate(
            st.session_state.messages,
            start=1
        ):
            st.write(
                f"{i}. "
                f"{msg['role']} → "
                f"{msg['content'][:100]}"
            )
    else:
        st.info(
            "No hay mensajes todavía."
        )

# =====================================================
# MODELOS
# =====================================================

elif menu == "👽 Modelos":

    st.title("👽 👾 🗿 ⛵ 🚤 🏴‍☠️ 🏝️ Modelos")

    for model_name, config in MODELS.items():

        st.markdown(
            f"""
            ### {config['label']}

            - Modelo: `{model_name}`
            - Proveedor: `{config['provider']}`
            """
        )

# =====================================================
# CONFIGURACIÓN
# =====================================================

elif menu == "⚙️ Configuración":

    st.title("⚙️ Configuración")

    st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.temperature,
        key="temperature",
        step=0.1
    )

    st.slider(
        "Max Tokens",
        min_value=256,
        max_value=8192,
        value=st.session_state.max_tokens,
        key="max_tokens",
        step=256
    )

    st.divider()

    # Filtro plataforma
    plataforma = st.radio(
        "Plataforma",
        [
            "Twitter",
            "Instagram",
            "Medium",
            "Reddit"
        ]
    )

    st.divider()

    # Filtro idioma
    idioma = st.radio(
        "Idioma",
        [
            "Español",
            "Ingles",
            "Frances",
            "Italiano"
        ]
    )

    st.divider()

    # Filtro tema
    tema = st.text_input(
        "Escribe el tema para el artículo..."
    )

    st.divider()

    # Filtro Hashtags
    st.slider(
        "Hashtags",
        min_value=1,
        max_value=4,
        value=st.session_state.hashtags,
        key="hashtags",
        step=1
    )

    st.divider()

    # Filtro Número palabras
    st.slider(
        "Words",
        min_value=20,
        max_value=200,
        value=st.session_state.words,
        key="words",
        step=10
    )

    st.divider()

    if st.button('Haz clic aquí'):
        if tema:
            # Hacer try except para la funcion de llamada
            prompt_call = f"Crea un artículo en idioma {idioma} para {plataforma} con {st.session_state.words} palabras sobre {tema} con {st.session_state.hashtags} hashtags"
            st.info(prompt_call)

            with st.spinner("Procesando información, por favor espere..."):
                with st.container(border=True):
                    st.write(call_response(prompt_call, MODELS, st.session_state))
                    
        else:
            st.info("Debes escribir un tema")

    st.divider()

    # if st.button('Probando ollama cloud'):
    #      with st.spinner("Procesando información, por favor espere..."):
    #             with st.container(border=True):
    #                 # st.write(call_ollama_cloud())
    #                 pass

                    
