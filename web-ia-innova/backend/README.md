# IA Gestora / Orquestadora — Backend básico (avance)

API en FastAPI que recibe un mensaje, elige un modelo con **reglas explícitas por prioridad** (matriz de delegación del informe) y devuelve una respuesta normalizada.

## Estado

- Funciona: `POST /orchestrate`, `GET /health`, reglas de ruteo, fallback, CORS, registro de la decisión, Dockerfile para Hugging Face.
- **Respuestas simuladas** (`PROVIDER_MODE=mock`). Las llamadas reales a OpenAI / Anthropic / NVIDIA **no están implementadas** (`RealProvider`).
- Sin autenticación ni límites de uso todavía.
- Los nombres de modelo vienen del informe y deben validarse.

## Contrato (el que usa el frontend)

`POST /orchestrate`

```json
{ "message": "texto del usuario" }
```

Respuesta 200:

```json
{
  "request_id": "uuid",
  "content": "...",
  "model": "gpt-5.6-terra",
  "category": "automatizacion_cotidiana",
  "reason": "Tarea normal y variada",
  "latency_ms": 12,
  "fallback_used": false,
  "is_mock": true
}
```

Error 502 si ningún proveedor responde: `{ "detail": "..." }`.

## Ejecutar en local

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Documentación interactiva: http://localhost:8000/docs

## Probar las reglas (no necesita instalar nada)

```powershell
python -m unittest -v
```

## Desplegar en Hugging Face

1. Crea un Space nuevo con SDK **Docker**.
2. Sube estos archivos (Dockerfile, requirements.txt, carpeta app/).
3. En Settings → Variables and secrets: `ALLOWED_ORIGINS` (dominio de Vercel) y, cuando se implementen los proveedores, las claves como **Secrets**.
4. La URL del Space es la que va en `NEXT_PUBLIC_ORCHESTRATOR_URL` del frontend.

## Pendientes

- Implementar `RealProvider` por proveedor (adaptadores independientes).
- Autenticación (por ejemplo, validar el token de Supabase) y límites de uso.
- Guardar métricas en Supabase.
- Mover las reglas a configuración editable por el panel admin.
