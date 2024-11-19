# Usa una imagen base de Python
FROM python:3.12-slim

# Instalación de dependencias del sistema necesarias para Google Cloud SDK y Streamlit
RUN apt-get update && apt-get install -y \
    curl \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | tee /etc/apt/trusted.gpg.d/google.asc \
    && echo "deb [signed-by=/etc/apt/trusted.gpg.d/google.asc] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update \
    && apt-get install -y google-cloud-sdk

# Instalar Streamlit
RUN pip install --no-cache-dir streamlit

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar los archivos del proyecto al contenedor
COPY requirements.txt ./
COPY src/ ./src/
COPY app.py ./
COPY img/ ./img/  
# Copia la carpeta img y sus contenidos

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto 8501 para Streamlit
EXPOSE 8501

# Ejecutar Streamlit cuando se inicie el contenedor
CMD ["streamlit", "run", "app.py"]
