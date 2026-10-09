"""Fase 6: datos personales sin palabra clave en español tampoco deben llegar a Gemini. Sin red."""
import unittest

from app.router import decide


class ClasificadorFalso:
    enabled = True

    def __init__(self):
        self.llamadas = []

    def classify(self, text):
        self.llamadas.append(text)
        return "general"


class TestPatronesSensibles(unittest.TestCase):
    def _es_privado_sin_gemini(self, frase: str) -> bool:
        falso = ClasificadorFalso()
        d = decide(frase, falso)
        return d.category == "procesamiento_privado" and d.decided_by == "regla" and not falso.llamadas

    def test_correo_electronico(self):
        self.assertTrue(self._es_privado_sin_gemini("Escríbele a juan.perez@example.com por favor"))

    def test_telefono_con_prefijo_y_espacios(self):
        self.assertTrue(self._es_privado_sin_gemini("Llámame al +57 300 123 4567"))

    def test_numero_de_documento_o_cuenta(self):
        self.assertTrue(self._es_privado_sin_gemini("Mi documento es 1234567890"))

    def test_iban_sin_espacios_y_con_espacios(self):
        self.assertTrue(self._es_privado_sin_gemini("Transfiere a ES9121000418450200051332"))
        self.assertTrue(self._es_privado_sin_gemini("IBAN ES91 2100 0418 4502 0005 1332"))

    def test_tarjeta_de_credito_con_guiones(self):
        self.assertTrue(self._es_privado_sin_gemini("Pagué con 4111-1111-1111-1111"))

    def test_vocabulario_ampliado_en_espanol_e_ingles(self):
        for frase in ("mi clave es abc", "my password is abc", "this is confidential", "el diagnóstico del paciente",
                      "mi salario mensual", "mi iban", "mi pasaporte", "mi dni", "tarjeta de crédito vencida"):
            with self.subTest(frase=frase):
                self.assertTrue(self._es_privado_sin_gemini(frase))

    def test_numeros_normales_no_se_marcan(self):
        for frase in ("Tengo 3 gatos y 12 años", "La versión 1.2.3 salió en 2026-10-09", "Son 150 mil pesos"):
            with self.subTest(frase=frase):
                falso = ClasificadorFalso()
                d = decide(frase, falso)
                self.assertNotEqual(d.category, "procesamiento_privado")
                self.assertEqual(len(falso.llamadas), 1)  # un mensaje ambiguo normal SÍ consulta a Gemini


class TestSinReDoS(unittest.TestCase):
    """Las expresiones regulares nuevas deben ser lineales: un mensaje de 32.000 caracteres no puede tardar."""

    def test_entradas_patologicas_son_rapidas(self):
        import time

        entradas = {
            "a_repetida": "a" * 32_000,
            "palabras_con_punto": "a." * 16_000,
            "arrobas_sin_dominio": "a@" * 16_000,
            "digitos_con_separadores": "1 " * 4 + "x " * 15_000,
            "guiones": "-" * 32_000,
        }
        for nombre, texto in entradas.items():
            with self.subTest(entrada=nombre):
                inicio = time.perf_counter()
                decide(texto, ClasificadorFalso())
                self.assertLess(time.perf_counter() - inicio, 1.0)


if __name__ == "__main__":
    unittest.main()
