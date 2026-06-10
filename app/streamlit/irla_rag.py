import os
import sys
import streamlit as st
import pandas as pd

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# Añade la carpeta superior al path de búsqueda de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.utils import *
from llm.llm_stream import *
from llm.llm_call import *
from llm.llm_images import *


# =====================================================
# FUNCIONES
# =====================================================
def gen_article():
    result = call_response(prompt_call, MODELS, st.session_state)
    st.write(result)

    # --------------------------------------------------------------------------------------------------------------
    # Comienza a trabajar con langchain
    # --------------------------------------------------------------------------------------------------------------

    texto = result['text']

    # 1. Ajustamos el Prompt para que sea extremadamente estricto
    template = """Eres un traductor profesional automático muy preciso.
    Traduce el texto del {idioma_entrada} al {idioma_salida}.

    REGLA CRÍTICA: Devuelve ÚNICAMENTE el texto traducido final. No agregues introducciones, no saludes, no des explicaciones, ni agregues notas al final. Si el usuario dice "Hola", tú solo traduces esa palabra.

    Texto a traducir:
    {texto}"""

    # Usamos ChatPromptTemplate que se lleva mejor con ChatGroq y LCEL
    prompt_template = ChatPromptTemplate.from_template(template)

    # 2. Inicializar el Modelo con TEMPERATURE = 0.0 (Clave para evitar que se enrolle)
    llm_traduccion = ChatGroq(
        temperature=0.0,  # <-- 0.0 hace que sea directo y no invente texto extra
        groq_api_key=get_groq_api_key(), 
        model_name="llama-3.3-70b-versatile"
    )

    # 3. Creación de la cadena usando el operador LCEL (|)
    cadena = prompt_template | llm_traduccion

    # 4. Ejecución de la cadena
    traduccion = cadena.invoke(input={
        "idioma_entrada": "español",  
        "idioma_salida": idioma, 
        "texto": texto
    })

    # 4. EXTRACCIÓN DE TOKENS
    # Groq guarda los tokens dentro del diccionario 'response_metadata'
    metadata = traduccion.response_metadata
    tokens_info = metadata.get("token_usage", {})

    tokens_input = tokens_info.get("prompt_tokens", 0)       # Enviados
    tokens_output = tokens_info.get("completion_tokens", 0)  # Recibidos
    tokens_totales = tokens_info.get("total_tokens", 0)

    # 5. EXTRAER EL TEXTO
    traduccion = traduccion.content

    # --- MOSTRAR EN STREAMLIT ---
    st.write(traduccion)

    st.info("Tokens de la Traducción")

    # Mostramos las métricas de tokens de forma elegante en la interfaz
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Tokens Enviados (Prompt)", value=tokens_input)
    with col2:
        st.metric(label="Tokens Recibidos (Completion)", value=tokens_output)
    with col3:
        st.metric(label="Tokens Totales", value=tokens_totales)

    # ------------------------------------ Código para mostrar precios--------------------------------------------
    # 1. Convertir el array a un DataFrame de Pandas
    df = pd.DataFrame(precios_modelos)

    # 2. Convertir las columnas necesarias a float
    df['precio_token_entrada'] = df['precio_token_entrada'].astype(float)
    df['precio_token_salida'] = df['precio_token_salida'].astype(float)

    # 2.- Hacer las operaciones
    df['precio_tokens_entrada'] = df['precio_token_entrada'] * (result['stats']['tokens_enviados'] + tokens_input)
    df['precio_tokens_salida'] = df['precio_token_salida'] * (result['stats']['tokens_recibidos'] + tokens_output)

    # 3. Mostrar en pantalla como tabla interactiva
    df_result = df[['modelo', 'precio_tokens_entrada', 'precio_tokens_salida']]
    df_result['precio_tokens_total'] = df_result['precio_tokens_entrada'] + df_result['precio_tokens_salida']
    st.subheader("Tabla Interactiva")
    st.dataframe(df_result)
    st.write('* Precios en dolares')

    return traduccion


def prueba_article():
    articulo = "Hola que tal estas"
    st.write(articulo)

    return articulo

def gen_image():
    if ia_imagen == "Unsplash":
        # ----------------------------------------------------
        # Código de Unsplash
        # ----------------------------------------------------
        img_uns, autor = get_image_unsplash(tema)

        if img_uns:
            # Mostrar la imagen en Streamlit
            st.image(img_uns, caption=f"Foto por {autor}", width=500)
            
            # Botón para descargar la imagen directamente
            st.markdown(f"[Descargar imagen original]({img_uns})", unsafe_allow_html=True)
        else:
            st.error("No se pudo obtener la imagen.")
        
    elif ia_imagen == "Hugging Face":
        # st.write("Has seleccionado **Hugging Face**. que no tiene tokens")
        # ----------------------------------------------------
        # Código de Hugging Face
        # ----------------------------------------------------
        client = InferenceClient(
            provider="wavespeed",
            api_key=get_hf_token(),
        )

        # output is a PIL.Image object
        image_hf = client.text_to_image(
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
        image_hf = image_hf.resize((500, 500))

        image_hf = get_image_hugging_face(tema)

        st.image(image_hf, caption=tema)

        # Permite descargarla
        image_hf.save("temp.png")

        with open("temp.png", "rb") as f:
            st.download_button(
                "Descargar imagen",
                f,
                file_name=f"{tema}.png",
                mime="image/png"
            )
    else:
        # ----------------------------------------------------
        # Código de Pollinations
        # ----------------------------------------------------
        image_pol = get_image_pollinations(tema, width=500, height=500)

        st.image(image_pol, caption=tema)

        # Permite descargarla
        image_pol.save("temp.png")

        with open("temp.png", "rb") as f:
            st.download_button(
                "Descargar imagen",
                f,
                file_name=f"{tema}.png",
                mime="image/png"
            )




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
# CARGAR PRECIOS DE LOS MODELOS
# =====================================================
precios_modelos = get_prices_openai_anthropic()


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

    st.title("👽 Modelos")

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

    # Filtro ia_imagen
    ia_imagen = st.radio(
        "IA de la imagen",
        [
            "Unsplash",
            "Hugging Face",
            "Pollinations"
        ]
    )

    st.divider()

    if st.button('Crear Articulo'):
        if tema:
            # Hacer try except para la funcion de llamada
            # prompt_call = f"Crea un artículo en idioma {idioma} para {plataforma} con {st.session_state.words} palabras sobre {tema} con {st.session_state.hashtags} hashtags"
            prompt_call = f"Crea un artículo para {plataforma} con {st.session_state.words} palabras sobre {tema} con {st.session_state.hashtags} hashtags"
            st.info(prompt_call)

            with st.spinner("Preparando articulo, por favor espere..."):
                with st.container(border=True):

                    article = gen_article()
                    # article = prueba_article()

            with st.spinner("Preparando imagen, por favor espere..."):
                with st.container(border=True):

                    gen_image()


                  
        else:
            st.info("Debes escribir un tema")

    # st.divider()

    # if st.button('Probando ollama cloud'):
    #      with st.spinner("Procesando información, por favor espere..."):
    #             with st.container(border=True):
    #                 # st.write(call_ollama_cloud())
    #                 pass

    st.divider()

    if st.button('Crear Imagen'):
         with st.spinner("Preparando imagen, por favor espere..."):
                with st.container(border=True):

                    gen_image()

                    # ----------------------------------------------------
                    # Código de Google
                    # ----------------------------------------------------
                    # query="Un gato astronauta estilo acuarela"

                    # # Llamamos a nuestra función pasándole el prompt
                    # image_bytes = get_image_google(query)
                    
                    # if image_bytes:
                    #     # Convertimos los bytes a un objeto de imagen PIL para mostrarlo
                    #     imagen_pil = Image.open(BytesIO(image_bytes))
                        
                    #     # Mostramos la imagen en pantalla con ancho limitado
                    #     st.image(imagen_pil, caption="Resultado de Nano Banana AI", width=550)
                    #     st.success("¡Imagen creada!")
                        
                    #     # Botón para descargar la imagen directamente
                    #     st.download_button(
                    #         label="💾 Descargar Imagen (PNG)",
                    #         data=image_bytes,
                    #         file_name="nano_banana_output.png",
                    #         mime="image/png"
                    #     )
                    # else:
                    #     st.error("No se pudo generar la imagen. Inténtalo con otra descripción.")
