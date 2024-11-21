import streamlit as st
from PIL import Image
import requests
from src.search import display_material_images, retriever
from src.background import set_logo_title, render_input_box, render_followup_message

# Título de la aplicación y logo
logo_url = "./img/cofares_logo.jpg"  # Asegúrate de que el logo esté en la carpeta correcta
title = "ChiliPharma - Tu Asistente Farmacéutico."
set_logo_title(logo_url, title)

# Inicializar el historial de conversación en la sesión
if "history" not in st.session_state:
    st.session_state.history = []  # Almacenar el historial de la conversación

# Llamar a la función para renderizar el campo de entrada de consulta
user_query = render_input_box()

# Mostrar el historial de la conversación en la barra lateral
with st.sidebar:
    st.title("Historial de Conversación")
    for chat in st.session_state.history:
        if chat["sender"] == "user":
            st.write(f"**Tú:** {chat['message']}")
        else:
            st.write(f"**Bot:** {chat['message']}")

# Función para agregar mensajes al historial
def add_message(message, sender):
    st.session_state.history.append({"message": message, "sender": sender})

# Procesar la consulta solo si el usuario ha ingresado algo
if user_query:
    # Añadir mensaje del usuario al historial
    add_message(user_query, "user")
    
    # Realizar la búsqueda con el retriever (esto devolverá productos relacionados)
    resultados = display_material_images(retriever, user_query)
    
    # Preparar el mensaje del bot
    if resultados is None or not isinstance(resultados, list):
        bot_message = "No entendí bien tu consulta. ¿Podrías reformularla?"
        resultados = []  # Asegurar que resultados sea una lista vacía
    else:
        bot_message = "Aquí están los productos encontrados:\n"
        for nombre, _ in resultados:
            bot_message += f"**Producto:** {nombre}\n"

    # Agregar mensaje del bot al historial
    add_message(bot_message, "bot")

    # Mostrar los resultados debajo de la consulta, centrados con badges
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    for nombre, images in resultados:
        st.markdown(
            f"""
            <div style="display: inline-block; text-align: center; margin-bottom: 20px;">
                <span style="
                    background-color: #E50871;
                    color: white;
                    font-size: 14px;
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-weight: bold;">
                    {nombre}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for img_url in images:
            try:
                # Reducir el tamaño de la imagen a la mitad y centrarla
                st.image(
                    img_url,
                    width=150,  # Puedes ajustar este valor según lo necesites (ancho de la imagen reducido a la mitad)
                    use_container_width=True,
                )
            except Exception as e:
                st.write(f"Error al cargar la imagen: {e}")
    st.markdown("</div>", unsafe_allow_html=True)
