import os
import sys
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# Añade la carpeta superior al path de búsqueda de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.utils import *
from llm.llm_stream import *
from llm.llm_call import *
from llm.llm_images import *
from llm.editorial_graph import construir_grafo_editorial


# =====================================================
# FUNCIONES
# =====================================================
def animacion():
    # Código HTML/CSS con la lancha fuera de borda 🚤
    codigo_animacion = """
    <div class="contenedor-oceano">
        <!-- Isla fija a la izquierda -->
        <div class="isla">🏝️</div>
        
        <!-- Lancha fuera borda que se desplaza desde la derecha -->
        <div class="fueraborda">🚤</div>
    </div>

    <style>
    body {
        margin: 0;
        padding: 0;
        background-color: transparent;
    }

    .contenedor-oceano {
        position: relative;
        width: 100%;
        height: 180px;
        background: linear-gradient(180deg, #74b9ff, #0984e3);
        overflow: hidden;
        border-radius: 10px;
    }

    .isla {
        position: absolute;
        left: 20px;
        bottom: 20px;
        font-size: 70px;
        z-index: 2;
        line-height: 1;
    }

    .fueraborda {
        position: absolute;
        bottom: 35px;
        font-size: 50px; /* Tamaño del emoji de la lancha */
        z-index: 1;
        line-height: 1;
        
        /* Animación configurada para la fuera borda (un poco más rápida: 4 segundos) */
        animation-name: navegar;
        animation-duration: 4s;
        animation-timing-function: ease-out;
        animation-fill-mode: forwards; 
    }

    @keyframes navegar {
        0% {
            transform: translateX(100vw); /* Empieza fuera de la pantalla a la derecha */
        }
        100% {
            transform: translateX(120px); /* Se detiene justo al lado de la isla */
        }
    }
    </style>
    """

    # Inyectamos el componente HTML aislado
    components.html(codigo_animacion, height=200, scrolling=False)


def gen_article():
    # 1. Compilar e inicializar el Grafo Editorial
    grafo = construir_grafo_editorial()
    
    # Preparamos el diccionario de estado con los inputs capturados de Streamlit
    config_inicial = {
        "modelo_redactor": st.session_state.selected_model,
        "temperature": st.session_state.temperature,
        "max_tokens": st.session_state.max_tokens,
        "plataforma": plataforma,        # Variable global de tu st.radio de plataforma
        "words": st.session_state.words,
        "tema": tema,                    # Variable global de tu st.text_input de tema
        "hashtags": st.session_state.hashtags,
        "quien": quien,                  # Variable global de tu st.text_input de quien publica
        "idioma": idioma,                # Variable global de tu st.radio de idioma
        "revision_history": [],
        "texto_final": "",
        "tokens_input": 0,
        "tokens_output": 0
    }
    
    # Ejecutamos el flujo multi-agente
    resultado_grafo = grafo.invoke(config_inicial)
    
    # Recuperamos el artículo final pulido y los tokens totales acumulados por los agentes
    texto_espanol = resultado_grafo["texto_final"]
    agent_tokens_in = resultado_grafo["tokens_input"]
    agent_tokens_out = resultado_grafo["tokens_output"]
    
    # Mostramos el resultado original de los agentes en pantalla
    st.subheader("Artículo Generado (Español)")
    st.write(texto_espanol)

    st.info("Tokens Utilizados en la Fase de Redacción")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Tokens Redac. Enviados", value=agent_tokens_in)
    with col2:
        st.metric(label="Tokens Redac. Recibidos", value=agent_tokens_out)
    with col3:
        st.metric(label="Tokens Redac. Totales", value=agent_tokens_in + agent_tokens_out)
    
    # Inicialización de variables para la traducción condicional
    traduccion_final = texto_espanol
    tokens_trans_input = 0
    tokens_trans_output = 0

    # 2. FLUJO DE TRADUCCIÓN: Solo si el idioma seleccionado no es Español
    if idioma != "Español":
        template = """Eres un traductor profesional automático muy preciso.
        Traduce el texto del español al {idioma_salida}.

        REGLA CRÍTICA: Devuelve ÚNICAMENTE el texto traducido final. No agregues introducciones, no saludes, no des explicaciones, ni agregues notas al final.

        Texto a traducir:
        {texto}"""

        prompt_template = ChatPromptTemplate.from_template(template)

        llm_traduccion = ChatGroq(
            temperature=0.0,  
            groq_api_key=get_groq_api_key(), 
            model_name="llama-3.3-70b-versatile"
        )

        cadena = prompt_template | llm_traduccion
        
        # Ejecutamos la traducción
        respuesta_traduccion = cadena.invoke(input={
            "idioma_salida": idioma, 
            "texto": texto_espanol
        })

        # Extraemos métricas de tokens de la traducción
        metadata_trans = respuesta_traduccion.response_metadata.get("token_usage", {})
        tokens_trans_input = metadata_trans.get("prompt_tokens", 0)
        tokens_trans_output = metadata_trans.get("completion_tokens", 0)
        tokens_trans_totales = metadata_trans.get("total_tokens", 0)

        traduccion_final = respuesta_traduccion.content

        # Mostramos la traducción y sus métricas independientes en la interfaz
        st.subheader(f"Traducción Final ({idioma})")
        st.write(traduccion_final)

        st.info("Tokens Utilizados en la Fase de Traducción")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Tokens Trad. Enviados", value=tokens_trans_input)
        with col2:
            st.metric(label="Tokens Trad. Recibidos", value=tokens_trans_output)
        with col3:
            st.metric(label="Tokens Trad. Totales", value=tokens_trans_totales)

    # 3. CÁLCULO FINANCIERO Y TABLA DE PRECIOS UNIFICADA
    # Convertimos la matriz de precios a un DataFrame de Pandas
    df = pd.DataFrame(precios_modelos)
    df['precio_token_entrada'] = df['precio_token_entrada'].astype(float)
    df['precio_token_salida'] = df['precio_token_salida'].astype(float)

    # Suma global de tokens: (Tokens totales de Agentes) + (Tokens de Traducción si existió)
    total_entrada_global = agent_tokens_in + tokens_trans_input
    total_salida_global = agent_tokens_out + tokens_trans_output

    # Operaciones matemáticas multiplicando costes por volumen real de tokens
    df['precio_tokens_entrada'] = df['precio_token_entrada'] * total_entrada_global
    df['precio_tokens_salida'] = df['precio_token_salida'] * total_salida_global

    # Generamos la tabla limpia e interactiva
    df_result = df[['modelo', 'precio_tokens_entrada', 'precio_tokens_salida']].copy()
    df_result['precio_tokens_total'] = df_result['precio_tokens_entrada'] + df_result['precio_tokens_salida']
    
    st.subheader("Tabla de Costes Totales de la Operación ($)")
    st.dataframe(df_result)
    st.write('* Precios expresados en dólares. Incluyen el coste acumulado del proceso de Agentes (Redacción + Revisión) más la Traducción.')

    return traduccion_final



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
        try:
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

        except Exception as e:
            status = getattr(getattr(e, "response", None), "status_code", None)

            if status == 402:
                st.error("Se han agotado los créditos de Hugging Face.")
            elif status == 401:
                st.error("API Key incorrecta.")
            elif status == 429:
                st.error("Demasiadas peticiones. Inténtalo más tarde.")
            else:
                st.error(f"Error: {e}")

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
            "⚙️ Configuración",
            "👨‍💻 Créditos"
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

    # Filtro tema
    quien = st.text_input(
        "Escribe quien publica el artículo..."
    )

    st.divider()

    if st.button('Crear Articulo'):
        if tema:
            if quien:
                # prompt_call = f"Crea un artículo en idioma {idioma} para {plataforma} con {st.session_state.words} palabras sobre {tema} con {st.session_state.hashtags} hashtags"
                #prompt_call = f"Crea un artículo para {plataforma} con {st.session_state.words} palabras sobre {tema} con {st.session_state.hashtags} hashtags"
                
                prompt_call = f"""Crea un artículo para {plataforma} con {st.session_state.words} palabras sobre {tema} 
                                    con {st.session_state.hashtags} hashtags y 3 emojis, 
                                    al principio que ponga creado por {quien} y genera un titulo que resuma el articulo"""

                # prompt_call = f"""Crea un artículo para {plataforma} con {st.session_state.words} palabras sobre {tema} 
                #                     con {st.session_state.hashtags} hashtags y 3 emojis, 
                #                     al principio que ponga creado por {quien} y genera un titulo que resuma el articulo
                #                     y devuelve la salida en un json dividida en quien publica, titulo y articulo"""
                st.info(prompt_call)

                with st.spinner("Preparando articulo, por favor espere..."):
                    with st.container(border=True):

                        article = gen_article()

                with st.spinner("Preparando imagen, por favor espere..."):
                    with st.container(border=True):

                        gen_image()
            else:
                st.info("Debes escribir quien publica el artículo")
        else:
            st.info("Debes escribir un tema")

            
# =====================================================
# CREDITOS
# =====================================================
elif menu == "👨‍💻 Créditos":
    # st.title("👨‍💻 Créditos")

    # Poner las imagenes aquí
    col11, col12 = st.columns([1, 4])  # Ajusta las proporciones según el tamaño del avatar
    #col11, col12 = st.columns(2)

    with col11:
        ruta_avatar = os.path.join(ruta_actual, "..", "logos", "juanma.jpg")
        st.image(ruta_avatar, width=150)

    with col12:
        st.write("### Juan Manuel Iriondo Ortega")
        st.write("### Data Analyst & AI Developer")

    st.divider()

    # Diccionario de islas con sus coordenadas (Latitud, Longitud)
    ISLAS = {
        "islas maldivas": {"lat": 3.202778, "lon": 73.22068},
        "isla tortuga": {"lat": 9.77323, "lon": -84.89545},
        "Lanzarote": {"lat": 28.96302, "lon": -13.54769},
        "Menorca": {"lat": 39.88944, "lon": 4.26416},
        "Madeira": {"lat": 32.79673, "lon": -17.04323}
    }

    # Selector de isla en la interfaz
    isla_seleccionada = st.selectbox("Selecciona una isla para tus vacaciones:", list(ISLAS.keys()))

    # Obtener coordenadas de la ciudad elegida
    lat = ISLAS[isla_seleccionada]["lat"]
    lon = ISLAS[isla_seleccionada]["lon"]

    # URL de la API de Open-Meteo (pedimos temperatura actual y velocidad del viento)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"

    # Botón para actualizar el clima
    if st.button("Obtener Clima"):
        with st.spinner("Cargando datos..."):

            animacion()

            try:
                # Petición a la API
                respuesta = requests.get(url)
                datos = respuesta.json()
                
                # Extraer la información del clima actual
                clima_actual = datos["current_weather"]
                temperatura = clima_actual["temperature"]
                viento = clima_actual["windspeed"]
                
                st.success(# Separador visual
                    f"Datos actualizados para **{isla_seleccionada}**"
                )
                
                # Mostrar los datos estéticamente usando las "metrics" de Streamlit
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(label="Temperatura", value=f"{temperatura} °C")
                    
                with col2:
                    st.metric(label="Velocidad del Viento", value=f"{viento} km/h")
                    
            except Exception as e:
                st.error("Hubo un error al conectar con la API Open-Meteo. Inténtalo de nuevo.")

