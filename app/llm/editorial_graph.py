import operator
from typing import TypedDict, Annotated, List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from utils.utils import get_groq_api_key  # Asegúrate de que esta importación apunte correctamente a tu utils

# 1. DEFINICIÓN DEL ESTADO DEL GRAFO
class AgentState(TypedDict):
    modelo_redactor: str
    temperatura: float
    max_tokens: int
    plataforma: str
    words: int
    tema: str
    hashtags: int
    quien: str
    idioma: str
    revision_history: List[dict]
    texto_final: str
    # Los tokens se van acumulando sumándose aritméticamente en cada iteración
    tokens_input: Annotated[int, operator.add]
    tokens_output: Annotated[int, operator.add]

# 2. NODO DEL AGENTE REDACTOR
def agente_redactor(state: AgentState):
    # Ver que modelo usa para saber la api key a usar
    if state['modelo_redactor'] == "llama3.2:1b":
        modelo = "llama-3.3-70b-versatile"
    else:
        modelo = state['modelo_redactor']

    llm = ChatGroq(
        #temperature=0.7,
        temperature=state['temperatura'],
        max_tokens=state['max_tokens'],
        groq_api_key=get_groq_api_key(), 
        #model_name="llama-3.3-70b-versatile"
        model_name=modelo
    )
    
    # Guías de estilo personalizadas para forzar la diferenciación de plataformas
    guia_estilo = {
        "Twitter": "Formato tipo hilo o tweet individual de impacto. Frases cortas, ganchos fuertes en la primera línea, directo y con saltos de línea estratégicos.",
        "Instagram": "Texto visualmente limpio con espacios. Tono empático, cercano y dinámico, ideal para captions que inviten a guardar o comentar.",
        "Medium": "Estilo artículo de opinión o post de blog profesional. Párrafos estructurados, tono analítico, fluido, narrativo y formal.",
        "Reddit": "Tono comunitario, conversacional, honesto y directo. Evita a toda costa sonar corporativo o publicitario, fomenta el debate y la discusión."
    }
    
    sistema = f"""Eres un redactor experto en {state['plataforma']}. {guia_estilo.get(state['plataforma'], '')}
    
    REGLAS ESTRICTAS DE CONTENIDO:
    1. Genera OBLIGATORIAMENTE un título atractivo que resuma el artículo en la primera línea.
    2. Al principio del texto (debajo del título) debe figurar exactamente: "Creado por {state['quien']}".
    3. Escribe un cuerpo de texto que tenga aproximadamente {state['words']} palabras sobre el tema: "{state['tema']}".
    4. Incluye exactamente {state['hashtags']} hashtags relacionados al final.
    5. Distribuye exactamente 3 emojis a lo largo de todo el artículo.
    6. El texto DEBE generarse originalmente en idioma Español."""

    msg_historial = state.get("revision_history", [])
    
    # Si el corrector envió correcciones, las concatenamos al historial
    if msg_historial:
        prompt_mensajes = [SystemMessage(content=sistema)] + msg_historial + [HumanMessage(content="Por favor, corrige el artículo aplicando estrictamente el feedback del editor.")]
    else:
        prompt_mensajes = [SystemMessage(content=sistema), HumanMessage(content=f"Redacta el artículo sobre el tema: {state['tema']}")]

    respuesta = llm.invoke(prompt_mensajes)
    
    # Tracking de tokens consumidos en esta llamada
    metadata = respuesta.response_metadata.get("token_usage", {})
    
    return {
        "texto_final": respuesta.content,
        "tokens_input": metadata.get("prompt_tokens", 0),
        "tokens_output": metadata.get("completion_tokens", 0)
    }

# 3. NODO DEL AGENTE CORRECTOR (EDITOR EN JEFE)
def agente_corrector(state: AgentState):
    llm = ChatGroq(
        temperature=0.0,  # Temperatura 0 para una auditoría determinista y estricta
        groq_api_key=get_groq_api_key(), 
        model_name="llama-3.3-70b-versatile"
    )
    
    sistema = f"""Eres el Editor en Jefe de la plataforma {state['plataforma']}. Tu única misión es auditar que el texto cumpla con TODAS las reglas:
    1. ¿Tiene un título claro al inicio?
    2. ¿Dice exactamente "Creado por {state['quien']}" al principio?
    3. ¿Se acerca al objetivo de {state['words']} palabras?
    4. ¿Contiene exactamente {state['hashtags']} hashtags?
    5. ¿Tiene exactamente 3 emojis?

    CRITERIO DE SALIDA:
    Si el artículo cumple perfectamente con todos los puntos, responde ÚNICAMENTE con la palabra: APROBADO
    Si no cumple con alguna regla, describe con precisión qué falta o qué corregir para que el redactor lo arregle."""
    
    respuesta = llm.invoke([
        SystemMessage(content=sistema),
        HumanMessage(content=state['texto_final'])
    ])
    
    metadata = respuesta.response_metadata.get("token_usage", {})
    
    # Almacenamos la secuencia de feedback en el estado
    nuevo_historial = [
        HumanMessage(content=f"Borrador propuesto por el redactor:\n{state['texto_final']}"),
        SystemMessage(content=f"Resultado de la auditoría:\n{respuesta.content}")
    ]
    
    return {
        "revision_history": nuevo_historial,
        "tokens_input": metadata.get("prompt_tokens", 0),
        "tokens_output": metadata.get("completion_tokens", 0)
    }

# 4. FUNCIÓN ROUTER (DECISIÓN)
def decidir_continuar(state: AgentState):
    ultimo_feedback = state["revision_history"][-1].content
    if "APROBADO" in ultimo_feedback:
        return "finalizar"
    return "redactar"

# 5. COMPILACIÓN DEL GRAFO
def construir_grafo_editorial():
    workflow = StateGraph(AgentState)
    
    # Definir Nodos
    workflow.add_node("redactor", agente_redactor)
    workflow.add_node("corrector", agente_corrector)
    
    # Definir Flujo
    workflow.set_entry_point("redactor")
    workflow.add_edge("redactor", "corrector")
    
    # Enrutamiento condicional (bucle de feedback)
    workflow.add_conditional_edges(
        "corrector",
        decidir_continuar,
        {
            "redactar": "redactor",
            "finalizar": END
        }
    )
    
    return workflow.compile()