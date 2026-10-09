# Web IA INNOVA — Frontend

Interfaz de chat (Next.js App Router + React + TypeScript, CSS propio) para la plataforma multimodelo del grupo INNOVA.

## Cómo ejecutarlo (Windows, terminal de VS Code)

```powershell
npm install
npm run dev
```

Abre http://localhost:3000. Requiere Node.js 18.18+ (recomendado 20 LTS).

## Estado actual

- Chat funcional: enviar con botón o Enter (Shift+Enter = salto de línea), nueva conversación, historial en memoria, indicador de carga, errores y aviso sin conexión, diseño responsive.
- **Las respuestas son DATOS DE PRUEBA** mientras `NEXT_PUBLIC_ORCHESTRATOR_URL` esté vacía. Se marcan con la etiqueta "Datos de prueba".
- El historial se pierde al recargar (persistencia con Supabase: fase futura).
- Adjuntar archivos, configuración y cuenta: botones desactivados (próximamente).

## Estructura

```text
src/
├── app/            layout.tsx, page.tsx, globals.css
├── components/     ChatApp, Sidebar, ChatMessage, ChatInput, ModelInfo, LoadingIndicator, WelcomeScreen
├── hooks/          useChat.ts   (toda la lógica del chat)
├── services/       orchestratorApi.ts   (único archivo que habla con el backend)
└── types/          chat.ts
```

## Conectar el orquestador

1. Copia `.env.example` a `.env.local` y pon la URL base del orquestador.
2. Confirma con backend: endpoint, método, campos de entrada y de respuesta.
3. Ajusta SOLO `src/services/orchestratorApi.ts` (`ENDPOINT_PATH`, cuerpo de la petición y `parseResponse`).

Actualmente son **supuestos sin confirmar**: `POST {URL}/orchestrate` con `{ "message": "..." }`, y respuesta con `content` (o `response`) y, opcionalmente, `model`, `category`, `reason`, `latency_ms`. La interfaz muestra únicamente los metadatos que lleguen.

## Seguridad

Nunca pongas claves de OpenAI, Anthropic o NVIDIA en este proyecto. Variables con prefijo `NEXT_PUBLIC_` son visibles en el navegador: solo URLs públicas.

## Despliegue en Vercel

Sube el repositorio a GitHub, impórtalo en Vercel y define `NEXT_PUBLIC_ORCHESTRATOR_URL` en Settings → Environment Variables.
