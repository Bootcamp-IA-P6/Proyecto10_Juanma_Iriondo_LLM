from groq import Groq
import streamlit as st
from torch import chunk

from dotenv import load_dotenv
import os

# Inicializar el cliente de Groq
load_dotenv()
client = Groq(api_key=os.environ["GROQ_API_KEY"])

def get_ai_response(messages):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        # entre 0 -> menos y 2 -> mas creatico
        temperature=0.7,
        max_tokens=1024,
        stream=True
    )

    # chunk son los pedazos de texto que va dando el modelo
    response = "".join(chunk.choices[0].delta.content or "" for chunk in completion)
    return response

def chat():
    st.title("Chat con llama 3.3")
    st.write("¡Bienvenido al chat con AI! Escribe 'exit' para terminar la conversación.")

    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

    def submit():
        user_input = st.session_state.user_input
        if user_input.lower() == 'exit':
            st.write("¡Gracias por chatear! ¡Adios!")
            st.stop()

        st.session_state['messages'].append({"role": "user", "content": user_input})

        with st.spinner("Obteniendo respuesta..."):
            ai_response = get_ai_response(st.session_state['messages'])
            st.session_state['messages'].append({"role": "assistant", "content": ai_response})

        st.session_state.user_input = ""

    # Mostrar el historial del chat
    for message in st.session_state['messages']:
        role = "Tu" if message["role"] == "user" else "Bot"
        st.write(f"**{role}:** {message['content']}")

    with st.form(key='chat_form', clear_on_submit=True):
        st.text_input("Tu:", key="user_input")
        submit_button = st.form_submit_button(label='Enviar', on_click=submit)

if __name__ == "__main__":
    chat()