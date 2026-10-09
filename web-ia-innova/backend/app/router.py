"""Reglas de ruteo del orquestador.

Basado en la matriz de delegación del informe. Las reglas son explícitas y
tienen PRIORIDAD: se evalúan de menor a mayor número y gana la primera que coincide.
Así, si dos reglas se contradicen, el resultado es siempre el mismo (determinista).

PENDIENTE: los nombres de modelo son los del informe y deben validarse
contra los proveedores reales antes de usarlos en producción.
"""
from dataclasses import dataclass
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


def _has(text: str, words: list[str]) -> bool:
    t = text.lower()
    return any(w in t for w in words)


RULES: list[Rule] = [
    # Privacidad primero: lo sensible no debe salir a proveedores externos.
    Rule(10, "procesamiento_privado", NEMOTRON,
         "Contenido sensible o privado: ruta controlada",
         lambda m: _has(m, ["confidencial", "datos sensibles", "información privada", "no debe salir"])),
    Rule(20, "trabajo_masivo", NEMOTRON,
         "Gran volumen de datos: ruta económica",
         lambda m: _has(m, ["miles de registros", "lote", "procesar todos los documentos"])),
    Rule(30, "razonamiento_complejo", SOL,
         "Tarea de alta dificultad o riesgo",
         lambda m: _has(m, ["arquitectura", "depurar", "error intermitente", "concurrencia", "auditar", "revisión crítica"])),
    Rule(40, "contexto_extenso", CLAUDE,
         "Código o contexto extenso",
         lambda m: len(m) > LONG_CONTEXT_CHARS or _has(m, ["repositorio", "refactoriza", "revisa este código", "revisa esta función"])),
    Rule(50, "automatizacion_cotidiana", TERRA,
         "Tarea normal y variada",
         lambda m: _has(m, ["script", "automatiza", "informe", "correo", "redacta", "api"])),
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
