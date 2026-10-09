"use client";

import { useEffect, useRef, useState } from "react";
import { useChat } from "@/hooks/useChat";
import ChatInput from "./ChatInput";
import ChatMessage from "./ChatMessage";
import LoadingIndicator from "./LoadingIndicator";
import Sidebar from "./Sidebar";
import WelcomeScreen from "./WelcomeScreen";

export default function ChatApp() {
  const { conversations, activeConversation, isLoading, isOnline, send, newConversation, selectConversation } =
    useChat();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Baja automáticamente al último mensaje.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeConversation.messages.length, isLoading]);

  const isEmpty = activeConversation.messages.length === 0;

  return (
    <div className="app">
      <Sidebar
        conversations={conversations}
        activeId={activeConversation.id}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNew={newConversation}
        onSelect={selectConversation}
      />

      <main className="main">
        <header className="topbar">
          <button
            type="button"
            className="icon-btn menu-btn"
            onClick={() => setSidebarOpen(true)}
            aria-label="Abrir barra lateral"
          >
            ☰
          </button>
          <span className="topbar__title">{activeConversation.title}</span>
        </header>

        {!isOnline && (
          <div className="banner" role="alert">
            Sin conexión a internet. Podrás enviar mensajes cuando vuelva.
          </div>
        )}

        <div className="messages">
          {isEmpty ? (
            <WelcomeScreen onPick={send} />
          ) : (
            <div className="messages__inner">
              {activeConversation.messages.map((m) => (
                <ChatMessage key={m.id} message={m} />
              ))}
              {isLoading && <LoadingIndicator />}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <ChatInput onSend={send} disabled={isLoading || !isOnline} />
      </main>
    </div>
  );
}
