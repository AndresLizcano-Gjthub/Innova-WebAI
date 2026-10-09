"""Aislamiento de las pruebas: NUNCA deben usar una clave real ni tocar la red.

El código no lee el .env (lo hace uvicorn con --env-file), pero si alguien ejecuta las pruebas desde
una terminal que ya tiene GEMINI_API_KEY en el entorno, aquí se descarta y se fuerza el modo por reglas.
Se ejecuta antes de importar cualquier módulo de la app.
"""
import os

os.environ["GESTORA_MODE"] = "rules"
os.environ.pop("GEMINI_API_KEY", None)
