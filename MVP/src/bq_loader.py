from google.cloud import bigquery
from src.config import BASE_QUERY

class BigQueryLoader:
    def __init__(self, query, page_content_columns, metadata_columns):
        self.query = query
        self.page_content_columns = page_content_columns
        self.metadata_columns = metadata_columns

    def load(self):
        client = bigquery.Client()
        query_job = client.query(self.query)
        results = query_job.result()

        data = []
        for row in results:
            content = {col: row[col] for col in self.page_content_columns}
            metadata = {col: row[col] for col in self.metadata_columns}
            data.append({"content": content, "metadata": metadata})
        return data

# Crear el cargador y cargar los datos
loader = BigQueryLoader(
    BASE_QUERY,
    page_content_columns=["nombre_material"],
    metadata_columns=["id"],
)

data = loader.load()
