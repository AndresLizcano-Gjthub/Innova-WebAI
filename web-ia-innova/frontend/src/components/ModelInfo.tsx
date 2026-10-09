import type { ResponseMeta } from "@/types/chat";

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
