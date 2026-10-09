// Tipos del chat. Son parecidos a las clases de Java: describen la "forma" de los datos.

export type Role = "user" | "assistant";

// Metadatos opcionales: SOLO se muestran si el backend los devuelve.
export interface ResponseMeta {
  model?: string;
  category?: string;
  reason?: string;
  latencyMs?: number;
  isMock?: boolean; // true cuando la respuesta es de prueba (no viene del orquestador)
  // Quién tomó la decisión de ruteo (campo `decided_by` del backend). Analogía Java: un enum.
  decidedBy?: DecidedBy;
}

export type DecidedBy = "regla" | "gestora_llm" | "regla_respaldo";

export interface Message {
  id: string;
  role: Role;
  content: string;
  createdAt: number;
  meta?: ResponseMeta;
  isError?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
}

export interface OrchestratorRequest {
  message: string;
  conversationId: string;
}

export interface OrchestratorResult {
  content: string;
  meta?: ResponseMeta;
}
