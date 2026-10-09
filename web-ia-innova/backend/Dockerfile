FROM python:3.12-slim

# Logs sin buffer y sin archivos .pyc dentro de la imagen
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# Usuario sin privilegios (UID 1000, el que recomienda Hugging Face Spaces).
# Analogía Java: no ejecutar la aplicación como root, igual que no correr Tomcat como administrador.
RUN useradd -m -u 1000 appuser

WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

USER appuser

# El puerto sale de $PORT si el hosting lo define; por defecto 7860 (Hugging Face Spaces, Docker).
ENV PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
