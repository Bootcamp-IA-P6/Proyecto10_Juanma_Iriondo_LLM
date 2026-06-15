# 🏝️ IRLA Chat - Generador de Contenido Multiplataforma

¡Bienvenido a **IRLA Chat** (Inteligencia Rápida Ligera Artificial)! 🚀

Articulo en Medium -> https://medium.com/@juanmanuel.iriondo/creando-un-generador-de-contenidos-multiplataforma-inteligente-y-low-cost-con-streamlit-y-langchain-2c83a6eb7ddd

Este proyecto es una **Prueba de Concepto (PoC)** diseñada para la empresa *Digital Content*. Su objetivo es automatizar la generación de contenidos (texto e imágenes) para diversos medios como Blogs, Twitter/X, Instagram, Medium y Reddit, optimizando al máximo los costes de infraestructura.

La aplicación permite elegir entre modelos locales, APIs de inferencia gratuitas (o con capas gratuitas generosas) y generadores de imágenes *Zero-Cost*, ofreciendo además un control transparente del gasto en tokens a través de una interfaz gráfica intuitiva.

---

## ✨ Características Principales

* **Multiplataforma y Flexible:** Configura el tema, objetivo de palabras, número de hashtags e idioma para redes como Twitter, Instagram, Medium, etc.
* **Orquestación con LangChain:** Arquitectura limpia y extensible mediante LCEL (*LangChain Expression Language*).
* **Filosofía Low-Cost:**
    * Soporte para modelos locales con **Ollama** (`llama3.2:1b`).
    * Inferencia en la nube ultra rápida y gratuita con **Groq** (`llama-3.3-70b-versatile`) y (`groq/compound-mini`).
* **Generación de Imágenes Integrada:** Tres motores a elegir sin coste adicional: *Unsplash*, *Hugging Face* y *Pollinations*.
* **Traducción Estricta:** Módulo de traducción automática de alta precisión controlado mediante ingeniería de prompts y temperatura fija (`0.0`).
* **Métricas de Coste en Tiempo Real:** Cálculo automatizado del consumo de tokens y costes asociados mediante un DataFrame de Pandas en pantalla.

---

## 🛠️ Tecnologías Utilizadas

* **Frontend:** [Streamlit](https://streamlit.io/)
* **Framework LLM:** [LangChain](https://www.langchain.com/)
* **Proveedores de IA:** Groq, Ollama, Hugging Face, Pollinations
* **APIs usadas:** Open_Meteo, Unsplash, OpenRouter
* **Gestor de Entorno:** [uv](https://github.com/astral-sh/uv) (Inmensamente rápido)

---

## 🚀 Instalación y Configuración

Este proyecto utiliza **`uv`** para una gestión de dependencias y entornos virtuales de Python ultrarrápida.

### 1. Clonar el repositorio
```bash
git clone https://github.com/Bootcamp-IA-P6/Proyecto10_Juanma_Iriondo_LLM.git

cd irla-chat
```

### 2. Instalar dependencias
```bash
uv sync
```

### 3. Configurar variables de entorno
Crea un archivo .env en la raíz del proyecto copiando el fichero .env.example donde se indican las API_KEYS necesarias.

💻 Ejecución en Local

Para lanzar la interfaz de la aplicación, ejecuta el siguiente comando desde la raíz del proyecto:

```bash
uv run streamlit run app/streamlit/irla_main.py ó
streamlit run app/streamlit/irla_main.py
```

📂 Estructura del Proyecto

A grandes rasgos, el proyecto mantiene una estructura modular para facilitar su escalabilidad:

```bash
├── app/
│   └── streamlit/
│       └── irla_main.py       # Punto de entrada de la aplicación Streamlit
├── llm/
│   ├── llm_call.py            # Llamadas síncronas a los modelos
│   ├── llm_images.py          # Lógica de APIs de imágenes (Unsplash, HF, etc.)
│   └── llm_stream.py          # Inferencia en streaming para el chat
├── utils/
│   └── utils.py               # Funciones auxiliares y cálculo de precios
└── logos/                     # Recursos visuales de la interfaz
```

## 📈 Próximos Pasos (Fase 2)

    [ ] Integración de Bases de Datos Vectoriales para búsquedas semánticas.

    [ ] Implementación de arquitecturas RAG para nutrir los artículos con fuentes externas.

    [ ] Adición de Agentes Autónomos (ej. CrewAI / LangGraph) para flujos de revisión editorial automatizados.

## 👨‍💻 Créditos

Desarrollado por **Juan Manuel Iriondo Ortega** *(Data Analyst & AI Developer)* como solución funcional y escalable para la automatización inteligente de contenidos.