"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { OrchestratorError, sendMessage } from "@/services/orchestratorApi";
import type { Conversation, Message } from "@/types/chat";

function newId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function createConversation(): Conversation {
  return { id: newId(), title: "Nueva conversación", messages: [], createdAt: Date.now() };
}

function makeTitle(text: string): string {
  return text.length > 40 ? `${text.slice(0, 40)}…` : text;
}

/*
 * Hook = función reutilizable que guarda estado y lógica de React.
 * Aquí vive TODA la lógica del chat; los componentes solo dibujan.
 */
export function useChat() {
  const [conversations, setConversations] = useState<Conversation[]>(() => [createConversation()]);
  const [activeId, setActiveId] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const loadingRef = useRef(false); // guarda inmediata contra envíos duplicados

  // Detecta pérdida de conexión.
  useEffect(() => {
    setIsOnline(navigator.onLine);
    const on = () => setIsOnline(true);
    const off = () => setIsOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);

  // Si no hay una seleccionada, usamos la primera.
  const activeConversation = conversations.find((c) => c.id === activeId) ?? conversations[0];

  const addMessage = useCallback((conversationId: string, message: Message) => {
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== conversationId) return c;
        const isFirstUserMessage = message.role === "user" && c.messages.length === 0;
        return {
          ...c,
          title: isFirstUserMessage ? makeTitle(message.content) : c.title,
          messages: [...c.messages, message],
        };
      }),
    );
  }, []);

  const newConversation = useCallback(() => {
    // Si la actual está vacía, no creamos otra igual.
    if (activeConversation.messages.length === 0) return;
    const conv = createConversation();
    setConversations((prev) => [conv, ...prev]);
    setActiveId(conv.id);
  }, [activeConversation]);

  const send = useCallback(
    async (text: string) => {
      const content = text.trim();
      if (!content || loadingRef.current) return; // vacío o ya enviando

      const conversationId = activeConversation.id;
      loadingRef.current = true;
      setIsLoading(true);

      addMessage(conversationId, { id: newId(), role: "user", content, createdAt: Date.now() });

      try {
        const result = await sendMessage({ message: content, conversationId });
        addMessage(conversationId, {
          id: newId(),
          role: "assistant",
          content: result.content,
          createdAt: Date.now(),
          meta: result.meta,
        });
      } catch (error) {
        const errorText =
          error instanceof OrchestratorError ? error.message : "Ocurrió un error inesperado.";
        addMessage(conversationId, {
          id: newId(),
          role: "assistant",
          content: errorText,
          createdAt: Date.now(),
          isError: true,
        });
      } finally {
        loadingRef.current = false;
        setIsLoading(false);
      }
    },
    [activeConversation, addMessage],
  );

  return {
    conversations,
    activeConversation,
    isLoading,
    isOnline,
    send,
    newConversation,
    selectConversation: setActiveId,
  };
}
