# Configuración de Google Cloud
PROJECT_ID = "dataton-2024-team-13-cofares"
REGION = "us-central1"
BUCKET = "dataton-2024-team-13-cofares-vector-search-bucket-ht-10291125"

# Identificadores de Google Cloud Matching Engine
INDEX_ID = "7424724945441128448"
ENDPOINT_ID = "4942256388341497856"

# Query base para BigQuery
BASE_QUERY = """
SELECT
  codigo_web as id,
  nombre_material,
  nombre_material_largo,
  nombre_proveedor
FROM dataton-2024-team-13-cofares.dataset.img_n_txt
"""
