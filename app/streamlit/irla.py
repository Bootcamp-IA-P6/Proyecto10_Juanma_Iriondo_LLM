import os
import requests
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

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
        "provider": "groq",
        "label": "Llama 3.3 70B (Groq)"
    }
}

OLLAMA_URL = "http://localhost:11434/api/generate"

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
        background-color: #111827;
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

# =====================================================
# CLIENTS
# =====================================================

def stream_ollama(prompt, model):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True
    }

    response = requests.post(
        OLLAMA_URL,
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


def stream_groq(prompt, model):

    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "No se encontró GROQ_API_KEY"
        )

    client = Groq(api_key=api_key)

    stream = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=st.session_state.temperature,
        max_tokens=st.session_state.max_tokens,
        stream=True
    )

    for chunk in stream:

        delta = chunk.choices[0].delta.content

        if delta:
            yield delta


def stream_response(prompt):

    model = st.session_state.selected_model

    provider = MODELS[model]["provider"]

    if provider == "ollama":
        yield from stream_ollama(prompt, model)

    elif provider == "groq":
        yield from stream_groq(prompt, model)

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
            "🤖 Modelos",
            "⚙️ Configuración"
        ]
    )

    st.divider()

    selected = st.selectbox(
        "Modelo",
        options=list(MODELS.keys()),
        index=list(MODELS.keys()).index(
            st.session_state.selected_model
        ),
        format_func=lambda x: MODELS[x]["label"]
    )

    st.session_state.selected_model = selected

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

                for chunk in stream_response(prompt):

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

elif menu == "🤖 Modelos":

    st.title("🤖 Modelos")

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

    st.session_state.temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.temperature,
        step=0.1
    )

    st.session_state.max_tokens = st.slider(
        "Max Tokens",
        min_value=256,
        max_value=8192,
        value=st.session_state.max_tokens,
        step=256
    )

    st.info(
        "Estos parámetros se aplican a Groq. "
        "Ollama puede requerir parámetros "
        "adicionales según el modelo."
    )