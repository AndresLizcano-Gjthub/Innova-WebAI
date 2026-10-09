"""Lógica híbrida de decide(): reglas fuertes primero, Gemini solo en lo ambiguo. Cliente falso, sin red."""
import unittest

from app.gestora import NullClassifier
from app.router import CLAUDE, LUNA, NEMOTRON, SOL, TERRA, choose_route, decide


class ClasificadorFalso:
    """Registra cuántas veces se le llamó y con qué texto (como un mock de Mockito)."""

    enabled = True

    def __init__(self, respuesta=None, error=None):
        self.respuesta, self.error, self.llamadas = respuesta, error, []

    def classify(self, text):
        self.llamadas.append(text)
        if self.error:
            raise self.error
        return self.respuesta


def _largo(texto: str) -> str:
    return texto + " " + "texto neutro " * 20


class TestPrivadoNuncaLlegaALlm(unittest.TestCase):
    def test_privado_no_llama_a_gemini(self):
        falso = ClasificadorFalso("tarea_breve")
        d = decide("Resume este texto confidencial de nómina", falso)
        self.assertEqual((d.category, d.model, d.decided_by), ("procesamiento_privado", NEMOTRON, "regla"))
        self.assertEqual(falso.llamadas, [])

    def test_privado_con_homoglifo_no_llama_a_gemini(self):
        falso = ClasificadorFalso("tarea_breve")
        d = decide("Esto es c" + chr(0x43E) + "nfidencial", falso)
        self.assertEqual(d.category, "procesamiento_privado")
        self.assertEqual(falso.llamadas, [])

    def test_privado_con_texto_pegado_de_pdf_no_llama_a_gemini(self):
        falso = ClasificadorFalso("tarea_breve")
        decide("Historia" + chr(10) + "clínica del paciente", falso)
        decide("confi" + chr(0xAD) + "dencial", falso)
        self.assertEqual(falso.llamadas, [])

    def test_privado_gana_aunque_haya_otras_senales(self):
        falso = ClasificadorFalso("general")
        d = decide("x" * 9000 + " confidencial", falso)
        self.assertEqual(d.category, "procesamiento_privado")
        self.assertEqual(falso.llamadas, [])


class TestSenalFuerteDecideLaRegla(unittest.TestCase):
    def test_cada_senal_fuerte_no_llama_a_gemini(self):
        casos = {
            "trabajo_masivo": _largo("Procesa este lote"),
            "razonamiento_complejo": _largo("Hay que depurar un error"),
            "contexto_extenso": "x" * 9000,
            "automatizacion_cotidiana": _largo("Escribe un script"),
        }
        for categoria, mensaje in casos.items():
            with self.subTest(categoria=categoria):
                falso = ClasificadorFalso("tarea_breve")
                d = decide(mensaje, falso)
                self.assertEqual((d.category, d.decided_by), (categoria, "regla"))
                self.assertEqual(falso.llamadas, [])

    def test_ruta_de_la_regla_coincide_con_choose_route(self):
        mensaje = _largo("Hay que depurar un error")
        d, r = decide(mensaje, ClasificadorFalso("general")), choose_route(mensaje)
        self.assertEqual((d.category, d.model), (r.category, r.model))
        self.assertEqual(d.model, SOL)


class TestAmbiguoLoDecideElLlm(unittest.TestCase):
    def test_mensaje_breve_usa_la_categoria_del_llm(self):
        falso = ClasificadorFalso("razonamiento_complejo")
        d = decide("¿Cómo va el plan?", falso)
        self.assertEqual((d.category, d.model, d.decided_by), ("razonamiento_complejo", SOL, "gestora_llm"))
        self.assertEqual(len(falso.llamadas), 1)

    def test_mensaje_sin_regla_usa_la_categoria_del_llm(self):
        d = decide("x" * 300, ClasificadorFalso("contexto_extenso"))
        self.assertEqual((d.category, d.model, d.decided_by), ("contexto_extenso", CLAUDE, "gestora_llm"))

    def test_el_llm_puede_confirmar_tarea_breve(self):
        d = decide("Hola, ¿qué hora es en Tokio?", ClasificadorFalso("tarea_breve"))
        self.assertEqual((d.model, d.decided_by), (LUNA, "gestora_llm"))

    def test_si_el_llm_dice_privado_se_acepta_y_falla_seguro(self):
        d = decide("Hola", ClasificadorFalso("procesamiento_privado"))
        self.assertEqual((d.category, d.model, d.decided_by), ("procesamiento_privado", NEMOTRON, "gestora_llm"))


class TestRespaldoDeReglas(unittest.TestCase):
    def _comprobar(self, falso, mensaje="Hola", esperado_categoria="tarea_breve", esperado_modelo=LUNA):
        d = decide(mensaje, falso)
        self.assertEqual((d.category, d.model, d.decided_by), (esperado_categoria, esperado_modelo, "regla_respaldo"))

    def test_categoria_invalida(self):
        self._comprobar(ClasificadorFalso("inventada"))

    def test_none(self):
        self._comprobar(ClasificadorFalso(None))

    def test_excepcion(self):
        self._comprobar(ClasificadorFalso(error=RuntimeError("boom")))

    def test_timeout(self):
        self._comprobar(ClasificadorFalso(error=TimeoutError()))

    def test_respaldo_en_mensaje_sin_regla_usa_general(self):
        self._comprobar(ClasificadorFalso(None), mensaje="x" * 300, esperado_categoria="general", esperado_modelo=TERRA)

    def test_respuesta_no_str_se_trata_como_invalida(self):
        self._comprobar(ClasificadorFalso(123))


class TestSinClasificador(unittest.TestCase):
    def test_modo_reglas_decide_la_regla(self):
        d = decide("Hola", NullClassifier())
        self.assertEqual((d.category, d.decided_by), ("tarea_breve", "regla"))

    def test_sin_clasificador_none(self):
        d = decide("Hola", None)
        self.assertEqual((d.category, d.decided_by), ("tarea_breve", "regla"))


if __name__ == "__main__":
    unittest.main()
