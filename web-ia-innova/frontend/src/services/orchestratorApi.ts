import type { OrchestratorRequest, OrchestratorResult, ResponseMeta } from "@/types/chat";

/*
 * Capa de servicios: es el ÚNICO archivo que habla con el orquestador.
 * Si el contrato de la API cambia, solo se modifica este archivo.
 *
 * PENDIENTE (confirmar con el equipo de backend):
 *  - URL real, método y campos de entrada/salida.
 *  - El informe sugiere un endpoint como /orchestrate, pero NO está confirmado.
 *  Por eso parseResponse() es tolerante y solo lee campos que existan.
 */

const API_URL = process.env.NEXT_PUBLIC_ORCHESTRATOR_URL;
const TIMEOUT_MS = 30_000;
const ENDPOINT_PATH = "/orchestrate"; // SUPUESTO: confirmar con backend

// B-09: longitud máxima del mensaje. DEBE coincidir con MAX_MESSAGE_CHARS del backend
// (backend/app/schemas.py). Analogía Java: una constante compartida del contrato, como
// un `public static final int` que cliente y servidor deben mantener sincronizada a mano.
export const MAX_MESSAGE_CHARS = 32_000;

export class OrchestratorError extends Error {}

export async function sendMessage(req: OrchestratorRequest): Promise<OrchestratorResult> {
  // Sin URL configurada -> datos de prueba, claramente marcados.
  if (!API_URL) return mockResponse(req);

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch(`${API_URL}${ENDPOINT_PATH}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: req.message }), // SUPUESTO: confirmar campos
      signal: controller.signal,
    });

    // F-05: mensaje distinto según el estado HTTP.
    if (res.status === 429) {
      throw new OrchestratorError("Demasiadas solicitudes, espera un momento e inténtalo de nuevo.");
    }
    if (res.status >= 500) {
      throw new OrchestratorError("El servidor tuvo un problema. Inténtalo de nuevo en unos instantes.");
    }
    if (!res.ok) {
      throw new OrchestratorError(`El servidor respondió con error ${res.status}. Intenta de nuevo.`);
    }

    // F-05: un JSON inválido NO es un fallo de red; se separa para no decir "revisa tu conexión".
    // Analogía Java: capturar JsonParseException aparte de IOException.
    let data: unknown;
    try {
      data = await res.json();
    } catch {
      throw new OrchestratorError("La respuesta del servidor tiene un formato inesperado.");
    }
    return parseResponse(data);
  } catch (error) {
    if (error instanceof OrchestratorError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new OrchestratorError("La solicitud tardó demasiado. Intenta de nuevo.");
    }
    throw new OrchestratorError("No se pudo conectar con el servidor. Revisa tu conexión.");
  } finally {
    clearTimeout(timer);
  }
}

function parseResponse(data: unknown): OrchestratorResult {
  if (typeof data !== "object" || data === null) {
    throw new OrchestratorError("La respuesta del servidor no tiene el formato esperado.");
  }
  const d = data as Record<string, unknown>;

  const content =
    typeof d.content === "string" ? d.content : typeof d.response === "string" ? d.response : null;
  if (content === null) {
    throw new OrchestratorError("La respuesta del servidor no incluye contenido.");
  }

  // Solo copiamos lo que realmente llegó. Nada se inventa.
  const meta: ResponseMeta = {};
  if (typeof d.model === "string") meta.model = d.model;
  if (typeof d.category === "string") meta.category = d.category;
  if (typeof d.reason === "string") meta.reason = d.reason;
  if (typeof d.latency_ms === "number") meta.latencyMs = d.latency_ms;
  if (d.is_mock === true) meta.isMock = true; // el backend avisa que la respuesta es simulada

  return { content, meta: Object.keys(meta).length > 0 ? meta : undefined };
}

function mockResponse(req: OrchestratorRequest): Promise<OrchestratorResult> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        content:
          `Esta es una respuesta de prueba. Recibí tu mensaje: «${req.message}». ` +
          "Cuando el orquestador esté conectado, aquí aparecerá la respuesta real.",
        meta: { isMock: true },
      });
    }, 1200);
  });
}
