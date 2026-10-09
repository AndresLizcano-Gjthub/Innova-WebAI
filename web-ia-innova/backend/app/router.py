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

# Orden de respaldo si el modelo elegido falla (nunca incluye al propio modelo fallido).
FALLBACK_ORDER = [TERRA, CLAUDE, NEMOTRON]


@dataclass(frozen=True)
class Rule:
    priority: int                      # menor = se evalúa primero
    name: str                          # categoría que se devuelve al frontend
    model: str
    reason: str
    matches: Callable[[str], bool]


def _normalize(text: str) -> str:
    """Quita tildes y pasa a minúsculas ("Información" -> "informacion").

    Analogía Java: como Normalizer.normalize(s, Form.NFD) + replaceAll("\\p{M}", "").
    Sin esto, "informacion privada" (sin tilde) se escaparía de la regla de privacidad.
    """
    descompuesto = unicodedata.normalize("NFKD", text)
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).casefold()


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
    "confidencial", "sensible", "datos sensibles", "información privada", "datos privados",
    "no debe salir", "contraseña", "historia clínica", "historias clínicas", "cédula",
    "número de cuenta", "números de cuenta", "nómina",
]

RULES: list[Rule] = [
    # Privacidad primero: lo sensible no debe salir a proveedores externos.
    Rule(10, "procesamiento_privado", NEMOTRON,
         "Contenido sensible o privado: ruta controlada",
         lambda m: _has(m, PALABRAS_PRIVADAS)),
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

DEFAULT_RULE = Rule(999, "general", TERRA, "Sin regla específica: modelo por defecto", lambda m: True)


@dataclass(frozen=True)
class Decision:
    category: str
    model: str
    reason: str


def choose_route(message: str) -> Decision:
    """Devuelve la decisión de la primera regla (por prioridad) que coincida."""
    for rule in sorted(RULES, key=lambda r: r.priority):
        if rule.matches(message):
            return Decision(rule.name, rule.model, rule.reason)
    return Decision(DEFAULT_RULE.name, DEFAULT_RULE.model, DEFAULT_RULE.reason)


def fallback_models(failed_model: str) -> list[str]:
    return [m for m in FALLBACK_ORDER if m != failed_model]
