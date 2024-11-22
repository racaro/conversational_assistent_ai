import streamlit as st
from google.cloud import bigquery, storage
from vertexai.language_models import TextEmbeddingModel
from vertexai.preview.generative_models import GenerativeModel
from PIL import Image as PILImage
from io import BytesIO
import requests
import pandas as pd

# Inicializar Vertex AI y BigQuery
PROJECT_ID = "dataton-2024-team-13-cofares"
REGION = "us-central1"

from google.cloud import aiplatform
import vertexai

aiplatform.init(project=PROJECT_ID, location=REGION)
vertexai.init(project=PROJECT_ID, location=REGION)
client = bigquery.Client()
generative_model = GenerativeModel("gemini-1.5-flash-001")


# Función para consultar BigQuery
def consultar_bigquery(query_text, expandir_busqueda=False):
    fraction_lists_to_search = 0.05 if expandir_busqueda else 0.01
    query = f"""
    WITH top_results AS (
      SELECT
        CAST(base.codigo_web AS STRING) AS result_id,
        results.distance AS distance
      FROM VECTOR_SEARCH(
        TABLE `dataset_us.embeddings`,
        'ml_generate_embedding_result',
        (
          SELECT ml_generate_embedding_result, content AS query
          FROM ML.GENERATE_EMBEDDING(
            MODEL `dataset_us.embedding_model`,
            (SELECT '{query_text}' AS content))
        ),
        top_k => 5,
        options => '{{"fraction_lists_to_search": {fraction_lists_to_search}}}'
      ) AS results
    )
    SELECT
      original_table.*,
      top_results.distance
    FROM `dataset_us.test_table_9k` AS original_table
    JOIN top_results
      ON REGEXP_EXTRACT(original_table.`codigo web`, r'[0-9]+$') = top_results.result_id;
    """
    query_job = client.query(query)
    return query_job.to_dataframe()


# Función principal para generar respuesta
def generar_respuesta_con_imagenes_gemini(query_text, historial=None):
    """Genera una respuesta basada en la consulta del usuario y descarga la imagen del producto recomendado."""
    if historial is None:
        historial = []

    # Añadir la consulta actual al historial como diccionario
    historial.append({"usuario": query_text})

    # Consultar BigQuery para obtener productos relevantes
    resultados_bigquery = consultar_bigquery(query_text)

    # Si hay menos de 3 productos, realizar una nueva consulta con rango ampliado
    if len(resultados_bigquery) < 3:
        resultados_bigquery = consultar_bigquery(query_text, expandir_busqueda=True)

    # Ordenar resultados por distancia coseno (score más bajo primero)
    resultados_bigquery = resultados_bigquery.sort_values(by="distance", ascending=True)

    # Contexto inicial para el modelo generativo
    contexto = """
    Eres un asistente conversacional experto en productos, que ayuda a los usuarios a encontrar opciones basadas en sus necesidades específicas.
    Mantén un lenguaje natural, fluido y profesional.
    Recuerda la conversación previa y refina tus respuestas basándote en las preguntas adicionales o nuevos datos del usuario.
    Si no encuentras información relevante, solicita más detalles al usuario de manera educada.
    """

    # Agregar historial de interacción
    for interaccion in historial:
        contexto += f"\nUsuario: {interaccion.get('usuario', '')}"
        if "asistente" in interaccion:
            contexto += f"\nAsistente: {interaccion['asistente']}"

    # Incluir productos relevantes encontrados
    contexto += "\n\nProductos relevantes encontrados:"
    for _, row in resultados_bigquery.iterrows():
        contexto += f"""
    Producto: {row['nombre del producto']}
    Descripción: {row['informacion del producto']}
    Código Web: {row['codigo web']}
    Distancia Coseno: {row['distance']}
    Imagen: {row['imagen_uri']}
    ---
    """

    # Generar pregunta para el asistente
    pregunta = """
    Basándote en la consulta actual del usuario y el historial previo:
    1. Responde de manera específica y directa a la pregunta del usuario.
    2. Si no tienes suficientes datos, muestra las opciones disponibles sin pedir más información adicional.
    3. Si es necesario, recomienda un producto relevante y explica por qué es adecuado.
    4. Descartar otros productos solo si es útil para la pregunta actual.
    5. Si necesitas más información, solicita datos adicionales de forma clara y educada.
    6. Al final, pregunta: "¿Es lo que buscabas?" para fomentar la interacción.
    """

    # Generar contenido con el texto
    response = generative_model.generate_content([contexto + pregunta])

    # Determinar producto recomendado
    producto_recomendado = resultados_bigquery.iloc[0] if not resultados_bigquery.empty else None
    imagen_recomendada = None

    # Mostrar todos los productos y descargar imágenes
    for _, row in resultados_bigquery.iterrows():
        imagen_uri = row.get("imagen_uri", None)

        if imagen_uri and pd.notna(imagen_uri):
            img_id = imagen_uri.replace("gs://datahub_chiliprofeno/", "")
            img_url = f"https://storage.googleapis.com/datahub_chiliprofeno/{img_id.strip()}"

            try:
                response_img = requests.get(img_url)
                response_img.raise_for_status()
                img_data = response_img.content
                img = PILImage.open(BytesIO(img_data)).resize((300, 300))
                st.image(img, caption=row["nombre del producto"], use_container_width=True)

                # Si es el producto recomendado, guardarlo
                if producto_recomendado is not None and row["codigo web"] == producto_recomendado["codigo web"]:
                    imagen_recomendada = f"/tmp/imagen_{row['codigo web']}.png"
                    img.save(imagen_recomendada)

            except Exception as ex:
                st.error(f"No se pudo descargar la imagen del producto {row['codigo web']}: {ex}")

    # Agregar respuesta generada al historial
    if response and response.text:
        historial[-1]["asistente"] = response.text

    return response.text if response else "No se pudo generar respuesta.", imagen_recomendada, resultados_bigquery, historial


# Interfaz con Streamlit
st.set_page_config(page_title="Leonardi - Tu Asistente Farmacéutico by Chiliprofeno 🌶️", layout="wide")

st.title("Leonardi - Tu Asistente Farmacéutico by Chiliprofeno 🌶️")
st.write("Consulta cualquier duda sobre productos farmacéuticos y de salud.")

# Inicializar variables de sesión
if "historial" not in st.session_state:
    st.session_state["historial"] = []

if "respuesta_actual" not in st.session_state:
    st.session_state["respuesta_actual"] = ""

if "imagen_actual" not in st.session_state:
    st.session_state["imagen_actual"] = None

if "resultados_actuales" not in st.session_state:
    st.session_state["resultados_actuales"] = None

# Mostrar historial en la barra lateral
with st.sidebar:
    st.subheader("Historial de Conversación")
    for interaccion in st.session_state["historial"]:
        usuario = interaccion.get("usuario", "Consulta no especificada")
        asistente = interaccion.get("asistente", "Sin respuesta")
        st.write(f"**Usuario:** {usuario}")
        st.write(f"**Asistente:** {asistente}")
        st.markdown("---")

# Mostrar respuesta actual
st.subheader("Respuesta del Asistente")
if st.session_state["respuesta_actual"]:
    st.write(st.session_state["respuesta_actual"])

    # Mostrar producto recomendado
    if st.session_state["imagen_actual"]:
        st.image(
            st.session_state["imagen_actual"],
            caption="Producto Recomendado",
            use_container_width=True,
        )

# Formulario para la consulta
with st.form(key="consulta_form"):
    query_text = st.text_input("Escribe tu consulta aquí:")
    submitted = st.form_submit_button("Consultar")

if submitted and query_text:
    respuesta, imagen_recomendada, resultados, historial = generar_respuesta_con_imagenes_gemini(
        query_text, st.session_state["historial"]
    )
    # Actualizar historial con usuario y asistente
    st.session_state["historial"] = historial
    st.session_state["respuesta_actual"] = respuesta
    st.session_state["imagen_actual"] = imagen_recomendada
    st.session_state["resultados_actuales"] = resultados

    # Recargar la página para reflejar los cambios
    st.rerun()
