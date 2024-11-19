import subprocess

def authenticate_with_gcloud():
    # Ejecutar el comando de gcloud para autenticar al usuario
    try:
        print("Iniciando el proceso de autenticación con Google Cloud...")
        subprocess.run(["gcloud", "auth", "login"], check=True)
        print("Autenticación completada exitosamente con Google Cloud.")
    except subprocess.CalledProcessError as e:
        print(f"Hubo un error al intentar autenticarte: {e}")

# Llamar la función para autenticarte
authenticate_with_gcloud()
