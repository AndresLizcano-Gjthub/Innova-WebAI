import type { DecidedBy, ResponseMeta } from "@/types/chat";

// Tabla de etiquetas (como un Map<enum, String> en Java). Record exige cubrir los tres valores.
const DECIDED_BY_LABEL: Record<DecidedBy, string> = {
  regla: "reglas",
  gestora_llm: "IA Gestora (Gemini)",
  regla_respaldo: "reglas (respaldo)",
};

interface ModelInfoProps {
  meta?: ResponseMeta;
}

// Muestra SOLO lo que el backend devolvió. Si no llegó nada, no pinta nada.
export default function ModelInfo({ meta }: ModelInfoProps) {
  if (!meta) return null;

  const items: string[] = [];
  if (meta.model) items.push(`Modelo: ${meta.model}`);
  if (meta.category) items.push(`Categoría: ${meta.category}`);
  if (meta.latencyMs !== undefined) items.push(`${(meta.latencyMs / 1000).toFixed(1)} s`);

  // "Decidido por": solo si el backend lo informó. Texto plano, legible por lectores de pantalla.
  const decidedBy = meta.decidedBy ? DECIDED_BY_LABEL[meta.decidedBy] : undefined;
  if (decidedBy) items.push(`Decidido por: ${decidedBy}`);

  if (!meta.isMock && items.length === 0 && !meta.reason) return null;

  return (
    <div className="model-info">
      {meta.isMock && <span className="badge">Datos de prueba</span>}
      {items.map((item) => (
        <span key={item} className="model-info__item">{item}</span>
      ))}
      {meta.reason && <p className="model-info__reason">{meta.reason}</p>}
    </div>
  );
}
