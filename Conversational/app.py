import streamlit as st
from google.cloud import bigquery, storage
from google.cloud import aiplatform as vertexai
from vertexai.language_models import TextEmbeddingModel
from vertexai.preview.generative_models import GenerativeModel
import pandas as pd

# Configuración inicial
PROJECT_ID = "dataton-2024-team-13-cofares"
REGION = "us-central1"
DEPLOYED_INDEX_ID = 'indice_solo_texto_8888_1732111168197'
INDEX_ENDPOINT_NAME = 'projects/160969173693/locations/us-central1/indexEndpoints/4416601869334347776'
vertexai.init(project=PROJECT_ID, location=REGION)

# Inicializar modelo generativo
generative_model = GenerativeModel("gemini-1.5-flash-001")

# Función para descargar imagen desde GCS
def descargar_imagen_de_gcs(gcs_uri, local_path):
    client = storage.Client()
    bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)
    return local_path

# Función para consultar BigQuery
def consultar_bigquery(query_text, expandir_busqueda=False):
    client = bigquery.Client(project=PROJECT_ID)
    fraction_lists_to_search = 0.05 if expandir_busqueda else 0.01

    # Consulta BigQuery con el valor interpolado directamente
    query = f"""
    WITH top_results AS (
      SELECT
        CAST(base.codigo_web AS STRING) AS result_id
      FROM VECTOR_SEARCH(
        TABLE `dataset_us.embeddings`,
        'ml_generate_embedding_result',
        (
          SELECT ml_generate_embedding_result, content AS query
          FROM ML.GENERATE_EMBEDDING(
            MODEL `dataset_us.embedding_model`,
            (SELECT '{query_text}' AS content))
        ),
        top_k => 5, options => '{{"fraction_lists_to_search": {fraction_lists_to_search}}}'
      )
    )
    SELECT
      original_table.*
    FROM `dataset_us.test_table_9k` AS original_table
    JOIN top_results
    ON REGEXP_EXTRACT(original_table.`codigo web`, r'[0-9]+$') = top_results.result_id;
    """

    query_job = client.query(query)

    # Convertir los resultados en un DataFrame
    return query_job.to_dataframe()

# Función principal de respuesta
def generar_respuesta_con_imagenes_gemini(query_text, historial=None):
    if historial is None:
        historial = []

    historial.append(f"Usuario: {query_text}")
    resultados_bigquery = consultar_bigquery(query_text)
    if len(resultados_bigquery) < 3:
        resultados_bigquery = consultar_bigquery(query_text, expandir_busqueda=True)

    contexto = """
Eres un asistente conversacional experto en productos, que ayuda a los usuarios a encontrar opciones basadas en sus necesidades específicas.
Mantén un lenguaje natural, fluido y profesional.
Recuerda la conversación previa y refina tus respuestas basándote en las preguntas adicionales o nuevos datos del usuario.
"""
    for interaccion in historial:
        contexto += f"\n{interaccion}"

    contexto += "\n\nProductos relevantes encontrados:"
    for _, row in resultados_bigquery.iterrows():
        contexto += f"""
    Producto: {row['nombre del producto']}
    Descripción: {row['informacion del producto']}
    Composición: {row['composicion']}
    Código Web: {row['codigo web']}
    ---"""

    pregunta = """
Basándote en la consulta actual del usuario y el historial previo:
1. Responde de manera específica y directa a la pregunta del usuario.
2. Si no tienes suficientes datos, muestra las opciones disponibles sin pedir más información adicional.
3. Si es necesario, recomienda un producto relevante y explica por qué es adecuado.
"""

    response = generative_model.generate_content([contexto + pregunta])
    producto_recomendado = None
    imagen_uri = None
    for _, row in resultados_bigquery.iterrows():
        if str(row['codigo web']) in response.text:
            producto_recomendado = row['codigo web']
            imagen_uri = row.get("imagen_uri", None)
            break

    imagen_recomendada = None
    if producto_recomendado and imagen_uri:
        local_path = f"/tmp/imagen_{producto_recomendado}.jpg"
        try:
            descargar_imagen_de_gcs(imagen_uri, local_path)
            imagen_recomendada = local_path
        except Exception as e:
            st.error(f"Error al descargar la imagen del producto recomendado ({imagen_uri}): {e}")

    historial.append(f"Asistente: {response.text}")
    return response.text, imagen_recomendada, historial

# Interfaz en Streamlit
st.title("Chilipharma - Tu Asistente Farmacéutico")

# Inicializar historial de conversación en la sesión
if "historial" not in st.session_state:
    st.session_state.historial = []

# Mostrar historial de conversación
st.write("### Historial de conversación:")
for mensaje in st.session_state.historial:
    st.write(mensaje)

# Entrada del usuario
query_text = st.text_input("Escribe tu consulta aquí:")

if query_text:
    with st.spinner("Generando respuesta..."):
        respuesta, imagen, st.session_state.historial = generar_respuesta_con_imagenes_gemini(query_text, st.session_state.historial)
        st.write("### Respuesta del asistente:")
        st.write(respuesta)
        if imagen:
            st.image(imagen, caption="Producto Recomendado", use_column_width=True)
        else:
            st.write("No hay imagen disponible para el producto recomendado.")
