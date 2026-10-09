"use client";

import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { MAX_MESSAGE_CHARS, ORCHESTRATOR_CONFIGURED } from "@/services/orchestratorApi";

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // El cuadro crece según el texto (hasta un máximo definido en CSS).
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [text]);

  // B-09: límite compartido con el backend (constante exportada del servicio).
  // Aviso discreto al superar el 90 %; el contador se anuncia con aria-live="polite".
  const length = text.length;
  const overLimit = length > MAX_MESSAGE_CHARS;
  const nearLimit = length >= MAX_MESSAGE_CHARS * 0.9;

  const canSend = text.trim().length > 0 && !overLimit && !disabled;

  function submit() {
    if (!canSend) return;
    onSend(text);
    setText("");
  }

  // Enter envía. Shift+Enter hace salto de línea.
  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="composer">
      <div className="composer__box">
        <button
          type="button"
          className="icon-btn"
          disabled
          title="Adjuntar archivos: próximamente"
          aria-label="Adjuntar archivos (próximamente)"
        >
          +
        </button>
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder="Escribe tu pregunta…"
          aria-label="Mensaje"
          aria-invalid={overLimit || undefined}
        />
        <button
          type="button"
          className="send-btn"
          onClick={submit}
          disabled={!canSend}
          aria-label="Enviar mensaje"
        >
          Enviar
        </button>
      </div>
      {/* Región viva siempre montada (vacía hasta acercarse al límite) para que se anuncie el cambio.
          No usamos maxLength: truncaría en silencio un texto pegado; preferimos avisar y bloquear el envío. */}
      <p className={`composer__counter${overLimit ? " composer__counter--over" : ""}`} aria-live="polite">
        {nearLimit &&
          (overLimit
            ? `Mensaje demasiado largo: ${length.toLocaleString("es")} de ${MAX_MESSAGE_CHARS.toLocaleString("es")} caracteres. Acórtalo para enviarlo.`
            : `${length.toLocaleString("es")} de ${MAX_MESSAGE_CHARS.toLocaleString("es")} caracteres`)}
      </p>
      <p className="composer__hint">Enter para enviar · Shift + Enter para salto de línea</p>
      {/* Aviso de privacidad: solo con backend configurado (sin backend no hay Gemini y sería falso).
          Va junto al input, separado del aviso de "respuestas simuladas" de la bienvenida y de la
          insignia "Datos de prueba" de cada respuesta, que siguen visibles. */}
      {ORCHESTRATOR_CONFIGURED && (
        <p className="composer__privacy">
          La IA Gestora clasifica tu mensaje con Gemini (Google). No envíes datos sensibles; los mensajes marcados como
          confidenciales no se envían a la IA Gestora (Gemini).
        </p>
      )}
    </div>
  );
}
