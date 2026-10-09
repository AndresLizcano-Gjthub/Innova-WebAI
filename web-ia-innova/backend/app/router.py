"""Reglas de ruteo del orquestador.

Basado en la matriz de delegación del informe. Las reglas son explícitas y
tienen PRIORIDAD: se evalúan de menor a mayor número y gana la primera que coincide.
Así, si dos reglas se contradicen, el resultado es siempre el mismo (determinista).

PENDIENTE: los nombres de modelo son los del informe y deben validarse
contra los proveedores reales antes de usarlos en producción.
"""
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable

# Nombres lógicos de modelos (según el informe)
SOL = "gpt-5.6-sol"
TERRA = "gpt-5.6-terra"
LUNA = "gpt-5.6-luna"
CLAUDE = "claude-sonnet-5"
NEMOTRON = "nemotron-3-ultra"

LONG_CONTEXT_CHARS = 8000
SHORT_TASK_CHARS = 200

PRIVATE_CATEGORY = "procesamiento_privado"

# Orden de respaldo si el modelo elegido falla (nunca incluye al propio modelo fallido).
FALLBACK_ORDER = [TERRA, CLAUDE, NEMOTRON]


@dataclass(frozen=True)
class Rule:
    priority: int                      # menor = se evalúa primero
    name: str                          # categoría que se devuelve al frontend
    model: str
    reason: str
    matches: Callable[[str], bool]


# Letras cirílicas y griegas que se ven como una letra latina (código Unicode -> letra latina).
# Tabla corta a propósito (no es la lista UTS #39 completa). Las claves están en minúscula
# porque el texto ya pasó por casefold(). Se usan códigos numéricos para que no haya dudas
# sobre qué letra es cuál.
_CONFUNDIBLES = {
    # Cirílico: а е о р с х у і ј к м н т в
    0x0430: "a", 0x0435: "e", 0x043E: "o", 0x0440: "p", 0x0441: "c", 0x0445: "x", 0x0443: "y",
    0x0456: "i", 0x0458: "j", 0x043A: "k", 0x043C: "m", 0x043D: "h", 0x0442: "t", 0x0432: "b",
    # Griego: ο α ε ι κ ν ρ τ υ χ
    0x03BF: "o", 0x03B1: "a", 0x03B5: "e", 0x03B9: "i", 0x03BA: "k", 0x03BD: "v", 0x03C1: "p",
    0x03C4: "t", 0x03C5: "u", 0x03C7: "x",
}


def _escrituras(palabra: str) -> set[str]:
    """Escrituras (LATIN / CYRILLIC / GREEK) de las letras de una palabra."""
    encontradas = set()
    for c in palabra:
        nombre = unicodedata.name(c, "")
        for escritura in ("LATIN", "CYRILLIC", "GREEK"):
            if nombre.startswith(escritura):
                encontradas.add(escritura)
    return encontradas


def _es_mixta(palabra: str) -> bool:
    """True si la palabra mezcla latín con cirílico o griego (hay confusión posible)."""
    escrituras = _escrituras(palabra)
    return "LATIN" in escrituras and len(escrituras) > 1


def _desconfundir(coincidencia: re.Match[str]) -> str:
    """Convierte a latín SOLO las palabras mixtas; el ruso o el griego normales no se tocan."""
    palabra = coincidencia.group(0)
    return palabra.translate(_CONFUNDIBLES) if _es_mixta(palabra) else palabra


@lru_cache(maxsize=4)
def _limpiar(text: str) -> str:
    """Minúsculas, sin caracteres invisibles de formato y sin tildes (aún sin colapsar espacios).

    Se quitan primero los caracteres de formato Unicode (categoría Cf: guion suave U+00AD,
    ancho cero U+200B/C/D, BOM U+FEFF...) que trae el texto pegado de PDF/Word y que partirían
    una palabra clave. Luego NFKD separa las tildes (marcas combinantes) y se descartan.
    """
    plegado = "".join(c for c in text.casefold() if unicodedata.category(c) != "Cf")
    descompuesto = unicodedata.normalize("NFKD", plegado)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


@lru_cache(maxsize=4)  # Una petición normaliza el mismo texto en varias reglas: se calcula una vez.
def _normalize(text: str) -> str:
    """Quita tildes y pasa a minúsculas ("Información" -> "informacion").

    Analogía Java: como Normalizer.normalize(s, Form.NFD) + replaceAll("\\p{M}", "").
    Sin esto, "informacion privada" (sin tilde) se escaparía de la regla de privacidad.
    """
    limpio = _limpiar(text)
    # Las palabras que mezclan escrituras se "desconfunden" a latín (ver _CONFUNDIBLES).
    limpio = re.sub(r"[^\W\d_]+", _desconfundir, limpio)
    # "_" cuenta como separador, y los espacios, saltos de línea y tabs se colapsan en uno
    # solo, para que las frases clave coincidan aunque vengan partidas.
    return re.sub(r"[\s_]+", " ", limpio)


@lru_cache(maxsize=4)
def _hay_palabra_mixta(text: str) -> bool:
    """True si ALGUNA palabra mezcla letras latinas con cirílicas o griegas (P-01).

    Es la huella de un homoglifo ("cоnfidencial" con una 'о' cirílica). Falla seguro: la regla 10
    la trata como privada. Un mensaje normal en ruso NO cuenta: ahí cada palabra es de una
    sola escritura. Tampoco cuenta mezclar escrituras entre palabras distintas.
    """
    return any(_es_mixta(w) for w in re.findall(r"[^\W\d_]+", _limpiar(text)))


@lru_cache(maxsize=None)
def _patron(word: str) -> re.Pattern[str]:
    """Compila (una sola vez) la palabra clave como regex de PALABRA COMPLETA.

    - "lote"       -> acepta "lote" y "lotes", pero NO "pilote" ni "lotería".
    - "automatiz*" -> prefijo explícito: acepta automatizar, automatiza, automatización...
    Analogía Java: Pattern.compile("\\blote(?:e?s)?\\b"), cacheado como un static final.
    """
    if word.endswith("*"):
        return re.compile(rf"\b{re.escape(_normalize(word[:-1]))}\w*")
    return re.compile(rf"\b{re.escape(_normalize(word))}(?:e?s)?\b")


def _has(text: str, words: list[str]) -> bool:
    t = _normalize(text)
    return any(_patron(w).search(t) for w in words)


# Vocabulario de la regla 10. Se compara sin tildes y por palabra completa (plural incluido).
# Ante la duda se prefiere la ruta controlada: un falso positivo es seguro, un falso negativo no.
PALABRAS_PRIVADAS = [
    # Con "*" = prefijo: cubre derivados (confidencialidad, confidencialmente, contraseña123).
    "confidencial*", "sensible", "datos sensibles", "información privada", "datos privados",
    "no debe salir", "contraseñ*", "credencial*", "historia clínica", "historias clínicas", "cédula",
    "número de cuenta", "números de cuenta", "nómina",
]

RULES: list[Rule] = [
    # Privacidad primero: lo sensible no debe salir a proveedores externos.
    Rule(10, PRIVATE_CATEGORY, NEMOTRON,
         "Contenido sensible o privado: ruta controlada",
         lambda m: _hay_palabra_mixta(m) or _has(m, PALABRAS_PRIVADAS)),
    Rule(20, "trabajo_masivo", NEMOTRON,
         "Gran volumen de datos: ruta económica",
         lambda m: _has(m, ["miles de registros", "lote", "procesar todos los documentos"])),
    Rule(30, "razonamiento_complejo", SOL,
         "Tarea de alta dificultad o riesgo",
         lambda m: _has(m, ["arquitectura", "depur*", "error intermitente", "concurrencia", "audit*", "revisión crítica"])),
    Rule(40, "contexto_extenso", CLAUDE,
         "Código o contexto extenso",
         lambda m: len(m) > LONG_CONTEXT_CHARS or _has(m, ["repositorio", "refactoriz*", "revisa este código", "revisa esta función"])),
    Rule(50, "automatizacion_cotidiana", TERRA,
         "Tarea normal y variada",
         lambda m: _has(m, ["script", "automatiz*", "informe", "correo", "redact*", "api"])),
    Rule(60, "tarea_breve", LUNA,
         "Tarea sencilla que exige rapidez",
         lambda m: len(m) < SHORT_TASK_CHARS),
]

# Se ordena una sola vez al cargar el módulo (como un static final), no en cada llamada.
_RULES_ORDENADAS = sorted(RULES, key=lambda r: r.priority)

DEFAULT_RULE = Rule(999, "general", TERRA, "Sin regla específica: modelo por defecto", lambda m: True)


@dataclass(frozen=True)
class Decision:
    category: str
    model: str
    reason: str


def choose_route(message: str) -> Decision:
    """Devuelve la decisión de la primera regla (por prioridad) que coincida."""
    for rule in _RULES_ORDENADAS:
        if rule.matches(message):
            return Decision(rule.name, rule.model, rule.reason)
    return Decision(DEFAULT_RULE.name, DEFAULT_RULE.model, DEFAULT_RULE.reason)


def fallback_models(category: str, failed_model: str) -> list[str]:
    """Modelos de respaldo para una categoría.

    Privacidad: si la categoría es "procesamiento_privado" NO hay respaldo (lista vacía).
    Reenviar el texto sensible a un proveedor externo anularía la regla 10; es preferible
    un error 502 controlado. (Excepción explícita a "el respaldo nunca es vacío".)
    """
    if category == PRIVATE_CATEGORY:
        return []
    return [m for m in FALLBACK_ORDER if m != failed_model]
