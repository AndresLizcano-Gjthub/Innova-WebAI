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
        self.assertNotIn(TERRA, fallback_models("general", TERRA))
        self.assertTrue(len(fallback_models("razonamiento_complejo", SOL)) > 0)

    def test_fallback_orden_exacto(self):
        self.assertEqual(fallback_models("general", TERRA), [CLAUDE, NEMOTRON])
        self.assertEqual(fallback_models("razonamiento_complejo", SOL), [TERRA, CLAUDE, NEMOTRON])


class TestNormalizacion(unittest.TestCase):
    """R-02: tildes y mayúsculas no deben dejar escapar un texto privado."""

    def test_sin_tilde_sigue_siendo_privado(self):
        self.assertEqual(choose_route("informacion privada del cliente").category, "procesamiento_privado")

    def test_tilde_descompuesta_nfd_sigue_siendo_privado(self):
        self.assertEqual(choose_route("información privada del cliente").category, "procesamiento_privado")

    def test_mayusculas_con_tilde_son_privado(self):
        self.assertEqual(choose_route("INFORMACIÓN PRIVADA del cliente").category, "procesamiento_privado")


def _largo(texto: str) -> str:
    """Rellena con palabras neutras hasta pasar SHORT_TASK_CHARS, para que no gane 'tarea_breve'."""
    return texto + " " + "texto neutro " * 20


class TestPalabraCompleta(unittest.TestCase):
    """R-03: una palabra clave solo cuenta si es una palabra completa, no un trozo de otra."""

    def test_capital_no_activa_api(self):
        self.assertEqual(choose_route(_largo("¿Cuál es la capital de Francia?")).category, "general")

    def test_terapia_y_rapidez_no_activan_api(self):
        self.assertEqual(choose_route(_largo("hablemos de terapia y rapidez")).category, "general")

    def test_pilote_no_activa_lote(self):
        self.assertEqual(choose_route(_largo("El pilote de cimentación del puente")).category, "general")

    def test_loteria_no_activa_lote(self):
        self.assertEqual(choose_route(_largo("Resultados de la lotería de hoy")).category, "general")

    def test_pilote_no_le_gana_a_depurar(self):
        self.assertEqual(choose_route(_largo("Quiero depurar el pilote")).category, "razonamiento_complejo")

    def test_plurales_siguen_coincidiendo(self):
        self.assertEqual(choose_route(_largo("Procesa estos lotes de facturas")).category, "trabajo_masivo")
        self.assertEqual(choose_route(_largo("Documenta estas apis internas")).category, "automatizacion_cotidiana")

    def test_verbos_conjugados_siguen_coincidiendo(self):
        self.assertEqual(choose_route(_largo("Quiero automatizar esta tarea")).category, "automatizacion_cotidiana")
        self.assertEqual(choose_route(_largo("Redactar un mensaje formal")).category, "automatizacion_cotidiana")


class TestVocabularioPrivado(unittest.TestCase):
    """R-07: términos que deben activar la regla 10 (procesamiento_privado), uno por prueba."""

    def _es_privado(self, frase: str) -> bool:
        return choose_route(_largo(frase)).category == "procesamiento_privado"

    def test_sensible(self):
        self.assertTrue(self._es_privado("Este dato es sensible"))

    def test_datos_privados(self):
        self.assertTrue(self._es_privado("Revisa los datos privados del cliente"))

    def test_contrasena(self):
        self.assertTrue(self._es_privado("Mi contraseña es 1234"))
        self.assertTrue(self._es_privado("Mi contrasena es 1234"))

    def test_historia_clinica(self):
        self.assertTrue(self._es_privado("Resume la historia clínica del paciente"))
        self.assertTrue(self._es_privado("Resume las historias clinicas"))

    def test_cedula(self):
        self.assertTrue(self._es_privado("Mi cédula es 123456"))

    def test_numero_de_cuenta(self):
        self.assertTrue(self._es_privado("Mi número de cuenta es 998877"))

    def test_nomina(self):
        self.assertTrue(self._es_privado("Resume esta nómina"))

    def test_falso_positivo_cae_en_ruta_privada(self):
        # Decisión de diseño: ante la duda se prefiere la ruta controlada (conservador).
        self.assertTrue(self._es_privado("Esto NO es confidencial, es una consulta pública"))

    def test_palabra_parecida_no_activa(self):
        self.assertFalse(self._es_privado("Hablemos de la sensibilidad del sensor"))


class TestFallbackPrivado(unittest.TestCase):
    """R-01: lo privado NUNCA se reenvía a un proveedor externo como respaldo."""

    def test_fallback_de_categoria_privada_es_vacio(self):
        self.assertEqual(fallback_models("procesamiento_privado", NEMOTRON), [])

    def test_privado_sin_externos_aunque_falle_otro_modelo(self):
        for externo in (TERRA, CLAUDE, SOL, LUNA):
            self.assertNotIn(externo, fallback_models("procesamiento_privado", NEMOTRON))

    def test_flujo_privado_que_falla_termina_en_502_sin_reenviar(self):
        from unittest.mock import MagicMock, patch

        from fastapi import HTTPException

        from app.main import orchestrate
        from app.providers import ProviderError
        from app.schemas import OrchestrateRequest

        proveedor = MagicMock()
        proveedor.generate.side_effect = ProviderError("caído")
        with patch("app.main.get_provider", return_value=proveedor):
            with self.assertRaises(HTTPException) as ctx:
                orchestrate(OrchestrateRequest(message="Resume este texto confidencial de nómina"))
        self.assertEqual(ctx.exception.status_code, 502)
        # Solo se intentó el modelo controlado: el texto no salió a ningún otro proveedor.
        self.assertEqual(proveedor.generate.call_count, 1)
        self.assertEqual(proveedor.generate.call_args.args[0], NEMOTRON)


if __name__ == "__main__":
    unittest.main()
