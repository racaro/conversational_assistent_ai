import streamlit as st
import base64

def set_logo_title(logo_url, title="Chat de Búsqueda de Materiales"):
    """
    Esta función agrega un logo junto al título de la aplicación.
    El logo se coloca a la izquierda del título.
    """
    with open(logo_url, "rb") as image_file:
        logo_base64 = base64.b64encode(image_file.read()).decode()

    st.markdown(f"""
        <style>
            .header-container {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .header-title {{
                font-size: 2em;
                font-weight: bold;
                margin: 0;
            }}
            .header-logo {{
                display: block;
                margin: 0 auto;
                width: 200px;
            }}
        </style>
        <div class="header-container">
            <h1 class="header-title">{title}</h1>
            <img class="header-logo" src="data:image/jpg;base64,{logo_base64}" alt="Logo">
        </div>
    """, unsafe_allow_html=True)

def render_input_box():
    """
    Función que renderiza el cuadro de entrada de consulta centrado en la parte superior.
    """
    # Añadir espacio en blanco entre el logo y la consulta
    st.write("\n\n\n")

    # Título de la consulta centrado
    st.markdown("<div style='text-align: center; margin-top: 20px;'><h3>Consulta de productos farmacéuticos</h3></div>", unsafe_allow_html=True)

    # Campo de entrada de consulta centrado
    user_query = st.text_input("Escribe tu consulta:", key="consulta", help="Consulta de productos farmacéuticos")

    return user_query

def render_followup_message():
    """
    Función que muestra el mensaje de seguimiento debajo de la conversación e imágenes.
    """
    st.markdown("<div style='text-align: center; font-size: 14px; margin-top: 30px;'>Puedes seguir preguntando más cosas o escribir nuevas consultas.</div>", unsafe_allow_html=True)
