from typing import List, Optional
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
from google.cloud import aiplatform

# Inicializar Vertex AI
aiplatform.init(project="dataton-2024-team-13-cofares", location="us-central1")


# Inicializa el cliente de la API de Gemini
gemini_client = aiplatform.gapic.PredictionServiceClient()

from typing import List, Optional
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
from google.cloud import aiplatform, bigquery, storage
import os
import pandas as pd
from IPython.display import display, Image as IPImage
from vertexai.preview.generative_models import GenerativeModel, Image

DEPLOYED_INDEX_ID = 'indice_solo_texto_8888_1732111168197'
INDEX_ENDPOINT_NAME = 'projects/160969173693/locations/us-central1/indexEndpoints/4416601869334347776'

def fetch_similar_products(
    query_text: str,
    num_neighbors: int = 10,
    model_name: str = "text-embedding-004",
    deployed_index_id: str = DEPLOYED_INDEX_ID,
    index_endpoint_name: str = INDEX_ENDPOINT_NAME,
    bigquery_table: str = "dataton-2024-team-13-cofares.dataset.9000_values_table",
) -> pd.DataFrame:
    """
    Consulta un índice vectorial para encontrar productos similares y recupera detalles desde BigQuery.

    Args:
        query_text (str): Texto de la consulta del usuario.
        num_neighbors (int): Número de vecinos más cercanos a recuperar.
        model_name (str): Nombre del modelo de embeddings.
        deployed_index_id (str): ID del índice vectorial desplegado.
        index_endpoint_name (str): Nombre del endpoint del índice vectorial.
        bigquery_table (str): Tabla de BigQuery para recuperar datos.

    Returns:
        pd.DataFrame: DataFrame con los resultados relevantes desde BigQuery, o None si no hay resultados.
    """
    try:
        # Generar el embedding para la consulta
        print(f"Generando embeddings para: {query_text}")
        model = TextEmbeddingModel.from_pretrained(model_name)
        input_text = TextEmbeddingInput(query_text, "RETRIEVAL_QUERY")
        query_embedding = model.get_embeddings([input_text], output_dimensionality=512)[0].values

        # Consultar el índice vectorial
        print("Consultando el índice vectorial...")
        index_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name)
        response = index_endpoint.find_neighbors(
            deployed_index_id=deployed_index_id,
            queries=[query_embedding],
            num_neighbors=num_neighbors
        )

        # Extraer IDs de los vecinos
        id_resultados = [neighbor.id for neighbor in response[0]]
        print(f"IDs encontrados: {id_resultados}")

        if not id_resultados:
            print("No se encontraron vecinos cercanos.")
            return pd.DataFrame()  # Devolver un DataFrame vacío

        # Consultar BigQuery usando "codigo web_original"
        print("Consultando BigQuery...")
        client = bigquery.Client(project=PROJECT_ID)
        query = f"""
            SELECT *
            FROM `{bigquery_table}`
            WHERE `codigo web_original` IN UNNEST(@id_lista)
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ArrayQueryParameter("id_lista", "STRING", id_resultados)]
        )
        resultados = client.query(query, job_config=job_config).result()
        df_resultados = resultados.to_dataframe()

        if df_resultados.empty:
            print(f"No se encontraron resultados en la tabla para los IDs: {id_resultados}")
            return pd.DataFrame()  # Devolver un DataFrame vacío

        print(f"Resultados obtenidos: {df_resultados.shape[0]} filas.")
        return df_resultados

    except Exception as e:
        print(f"Error en fetch_similar_products: {e}")
        return pd.DataFrame()



import vertexai

# Inicializar el entorno
PROJECT_ID = "dataton-2024-team-13-cofares"
REGION = "us-central1"
vertexai.init(project=PROJECT_ID, location=REGION)

# Inicializar el entorno
PROJECT_ID = "dataton-2024-team-13-cofares"
REGION = "us-central1"
vertexai.init(project=PROJECT_ID, location=REGION)

# Inicializar el modelo generativo
generative_model = GenerativeModel("gemini-1.5-flash-001")

# Función para descargar imágenes temporalmente
def descargar_imagen_de_gcs(gcs_uri, local_path):
    """Descargar una imagen desde GCS a una ruta local."""
    from google.cloud import storage
    client = storage.Client()
    bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)
    return local_path

from google.cloud import bigquery

# Inicializar cliente de BigQuery
client = bigquery.Client()

def consultar_bigquery(query_text, expandir_busqueda=False):
    """Consulta BigQuery y devuelve un DataFrame con los productos relevantes."""
    # Si expandir_busqueda es True, reducimos las restricciones de búsqueda
    fraction_lists_to_search = 0.05 if expandir_busqueda else 0.01

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
        top_k => 5, options => '{{"fraction_lists_to_search": 0.01}}'
      )
    )
    SELECT
      original_table.*
    FROM `dataset_us.test_table_9k` AS original_table
    JOIN top_results
    ON REGEXP_EXTRACT(original_table.`codigo web`, r'[0-9]+$') = top_results.result_id;
    """
    # Ejecutar la consulta en BigQuery
    query_job = client.query(query)
    return query_job.to_dataframe()


def generar_respuesta_con_imagenes_gemini(query_text, historial=None):
    """Genera una respuesta basada en la consulta del usuario y descarga solo la imagen del producto recomendado."""
    if historial is None:
        historial = []

    # Añadir la consulta actual al historial
    historial.append(f"Usuario: {query_text}")

    # Consultar BigQuery para obtener productos relevantes
    resultados_bigquery = consultar_bigquery(query_text)
    # Si hay menos de 3 productos, realizar una nueva consulta con rango ampliado
    if len(resultados_bigquery) < 3:
        resultados_bigquery = consultar_bigquery(query_text, expandir_busqueda=True)
    contexto = """
Eres un asistente conversacional experto en productos, que ayuda a los usuarios a encontrar opciones basadas en sus necesidades específicas.
Mantén un lenguaje natural, fluido y profesional.
Recuerda la conversación previa y refina tus respuestas basándote en las preguntas adicionales o nuevos datos del usuario.
Si no encuentras información relevante, solicita más detalles al usuario de manera educada.
"""

# Agregar historial de interacción
    for interaccion in historial:
        contexto += f"\n{interaccion}"

# Incluir productos relevantes encontrados
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
4. Descartar otros productos solo si es útil para la pregunta actual.
5. Si necesitas más información, solicita datos adicionales de forma clara y educada.
6. Al final, pregunta: "¿Es lo que buscabas?" para fomentar la interacción.
"""



    # Generar contenido con el texto
    response = generative_model.generate_content([contexto + pregunta])

    # Identificar el código web en la respuesta
    producto_recomendado = None
    for _, row in resultados_bigquery.iterrows():
        if str(row['codigo web']) in response.text:
            producto_recomendado = row['codigo web']
            imagen_uri = row.get("imagen_uri", None)
            break

    # Descargar la imagen del producto recomendado si existe
    imagen_recomendada = None
    if producto_recomendado and imagen_uri:
        local_path = f"/tmp/imagen_{producto_recomendado}.jpg"
        try:
            descargar_imagen_de_gcs(imagen_uri, local_path)
            imagen_recomendada = local_path
        except Exception as e:
            print(f"Error al descargar la imagen del producto recomendado ({imagen_uri}): {e}")


    historial.append(f"Asistente: {response.text}")


    return response.text, imagen_recomendada, historial


# Ejemplo de uso interactivo
if __name__ == "__main__":
    historial = []
    while True:
        query_text = input("Usuario: ")
        respuesta, imagen, historial = generar_respuesta_con_imagenes_gemini(query_text, historial)
        print(f"Asistente: {respuesta}")
        if imagen:
            print(f"Imagen recomendada guardada en: {imagen}")


respuesta_modelo, imagen_recomendada = generar_respuesta_con_imagenes_gemini(input())

# Mostrar la respuesta
print(respuesta_modelo)

# Mostrar la imagen correspondiente al producto recomendado
if imagen_recomendada:
        display(IPImage(filename=imagen_recomendada))
else:
        print("No hay imagen disponible para el producto recomendado.")


