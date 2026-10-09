"use client";

import { useEffect, useRef, useState, type KeyboardEvent } from "react";

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

  const canSend = text.trim().length > 0 && !disabled;

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
      <p className="composer__hint">Enter para enviar · Shift + Enter para salto de línea</p>
    </div>
  );
}
