import re
from google.cloud import bigquery
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_google_vertexai import VectorSearchVectorStore
from src.config import PROJECT_ID, REGION, BUCKET, INDEX_ID, ENDPOINT_ID
from src.bq_loader import loader
import requests
from PIL import Image

# Inicialización del modelo de embeddings
embedding_model = VertexAIEmbeddings(model_name="textembedding-gecko@003")

# Inicialización del almacén de vectores
vector_store = VectorSearchVectorStore.from_components(
    project_id=PROJECT_ID,
    region=REGION,
    gcs_bucket_name=BUCKET,
    index_id=INDEX_ID,
    endpoint_id=ENDPOINT_ID,
    embedding=embedding_model
)

# Convertir los datos cargados en un "retriever"
retriever = vector_store.as_retriever()

def display_material_images(retriever, query, project_id=PROJECT_ID, dataset="dataset", table="img_n_txt", k=5):
    try:
        results = retriever.invoke(query, k=k)
        return [result.id for result in results]  # Devuelve solo los IDs si se encuentran resultados

    except ValueError as e:
        error_message = str(e)
        if "Documents with ids:" in error_message:
            missing_ids = re.findall(r"'(\d+)'", error_message)
            client = bigquery.Client(project=project_id)
            table_ref = f"{project_id}.{dataset}.{table}"

            ids_str = ", ".join([f"'{id_}'" for id_ in missing_ids])
            query = f"""
                SELECT nombre_material, ids_imagenes
                FROM `{table_ref}`
                WHERE codigo_web IN ({ids_str})
            """

            query_job = client.query(query)
            results = query_job.result()

            material_images = []
            for row in results:
                nombre_material = row.nombre_material
                ids_imagenes = row.ids_imagenes if isinstance(row.ids_imagenes, list) else row.ids_imagenes.split(",")
                images = []
                for img_id in ids_imagenes:
                    img_url = f"https://storage.googleapis.com/datahub_chiliprofeno/{img_id.strip()}"
                    response = requests.get(img_url)
                    if response.status_code == 200:
                        images.append(img_url)
                material_images.append((nombre_material, images))
            return material_images
        else:
            raise
