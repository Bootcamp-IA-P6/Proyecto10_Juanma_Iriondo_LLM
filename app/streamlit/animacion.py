import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("Animación: La fuera borda viaja a la isla 🏝️")

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

# Botón para reiniciar la animación
if st.button("¡A toda máquina! 🔄"):
    st.rerun()