"""Validación de entrada de /orchestrate (B-09). Se ejecutan con: python -m unittest -v"""
import unittest

from pydantic import ValidationError

from app.schemas import MAX_MESSAGE_CHARS, OrchestrateRequest


class TestOrchestrateRequest(unittest.TestCase):
    def test_limite_es_32000(self):
        # Debe ser mayor que LONG_CONTEXT_CHARS (8000) para que la regla 40 por longitud sea alcanzable.
        self.assertEqual(MAX_MESSAGE_CHARS, 32_000)

    def test_solo_espacios_se_rechaza(self):
        with self.assertRaises(ValidationError):
            OrchestrateRequest(message="    \n\t ")

    def test_recorta_espacios_en_los_bordes(self):
        self.assertEqual(OrchestrateRequest(message="  hola  ").message, "hola")

    def test_acepta_exactamente_el_limite(self):
        self.assertEqual(len(OrchestrateRequest(message="a" * MAX_MESSAGE_CHARS).message), MAX_MESSAGE_CHARS)

    def test_rechaza_mas_del_limite(self):
        with self.assertRaises(ValidationError):
            OrchestrateRequest(message="a" * (MAX_MESSAGE_CHARS + 1))


if __name__ == "__main__":
    unittest.main()
