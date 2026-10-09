"""Casos mínimos del informe (sección 16.1). Se ejecutan con: python -m unittest -v"""
import unittest

from app.router import CLAUDE, LUNA, NEMOTRON, SOL, TERRA, choose_route, fallback_models


class TestRouter(unittest.TestCase):
    def test_razonamiento_complejo_va_a_sol(self):
        self.assertEqual(choose_route("Necesito depurar un error intermitente de concurrencia en mi servicio").model, SOL)

    def test_tarea_breve_va_a_luna(self):
        self.assertEqual(choose_route("¿Qué horario de atención tienen?").model, LUNA)

    def test_contexto_largo_va_a_claude(self):
        self.assertEqual(choose_route("a" * 9000).model, CLAUDE)

    def test_repositorio_va_a_claude(self):
        self.assertEqual(choose_route("Revisa este código del repositorio y busca relaciones entre módulos, por favor").model, CLAUDE)

    def test_automatizacion_va_a_terra(self):
        msg = "Necesito que me ayudes a crear un script que automatice la descarga diaria de reportes del servidor"
        self.assertEqual(choose_route(msg).model, TERRA)

    def test_lote_privado_va_a_nemotron(self):
        self.assertEqual(choose_route("Procesar un lote de documentos confidencial que no debe salir de la infraestructura").model, NEMOTRON)

    def test_reglas_contradictorias_son_deterministas(self):
        # Coincide con privacidad (10) y con razonamiento complejo (30): gana la de menor número.
        msg = "Audita la arquitectura de este sistema con datos sensibles"
        first = choose_route(msg)
        self.assertEqual(first.model, NEMOTRON)
        self.assertEqual(first, choose_route(msg))

    def test_fallback_excluye_modelo_fallido(self):
        self.assertNotIn(TERRA, fallback_models(TERRA))
        self.assertTrue(len(fallback_models(SOL)) > 0)


class TestNormalizacion(unittest.TestCase):
    """R-02: tildes y mayúsculas no deben dejar escapar un texto privado."""

    def test_sin_tilde_sigue_siendo_privado(self):
        self.assertEqual(choose_route("informacion privada del cliente").category, "procesamiento_privado")

    def test_tilde_descompuesta_nfd_sigue_siendo_privado(self):
        self.assertEqual(choose_route("información privada del cliente").category, "procesamiento_privado")

    def test_mayusculas_con_tilde_son_privado(self):
        self.assertEqual(choose_route("INFORMACIÓN PRIVADA del cliente").category, "procesamiento_privado")


if __name__ == "__main__":
    unittest.main()
