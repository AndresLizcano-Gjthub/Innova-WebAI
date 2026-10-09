"""Aislamiento de las pruebas: NUNCA deben leer el .env real ni tocar la red.

APP_ENV=test hace que app.main NO cargue el archivo .env (donde vive la clave de Gemini),
y se fuerza el modo por reglas. Se ejecuta antes de importar cualquier módulo de la app.
"""
import os

os.environ["APP_ENV"] = "test"
os.environ["GESTORA_MODE"] = "rules"
os.environ.pop("GEMINI_API_KEY", None)
