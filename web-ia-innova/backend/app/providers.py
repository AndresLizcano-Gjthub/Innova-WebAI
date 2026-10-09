"""Adaptadores de proveedores: una interfaz común para todos.

Para añadir un proveedor nuevo, se crea una clase con generate() y se registra en get_provider().
El resto del sistema no cambia.
"""
import os


class ProviderError(Exception):
    """Fallo al llamar a un proveedor (sirve para activar el fallback)."""


class MockProvider:
    """Respuestas simuladas. Útil para desarrollar el frontend sin gastar créditos."""

    def generate(self, model: str, message: str) -> str:
        return f"[RESPUESTA SIMULADA de {model}] Recibí: {message}"


class RealProvider:
    """PENDIENTE: llamar a OpenAI / Anthropic / NVIDIA.

    Cada uno necesita su SDK y su clave (variables de entorno / Secrets de Hugging Face).
    Hasta que se implemente, lanza error para no aparentar que funciona.
    """

    def generate(self, model: str, message: str) -> str:
        raise ProviderError(f"Proveedor real para '{model}' aún no implementado")


def modo_real() -> bool:
    """ÚNICA fuente de verdad sobre si estamos en modo real (la usan main.py y get_provider).

    Si dos sitios decidieran por su cuenta, uno podría quedar en real y otro en mock sin que
    nadie lo note. Es como un único `isProduction()` en Java en vez de comparar el String en cada clase.
    """
    return os.getenv("PROVIDER_MODE", "mock").lower() == "real"


def get_provider():
    return RealProvider() if modo_real() else MockProvider()
