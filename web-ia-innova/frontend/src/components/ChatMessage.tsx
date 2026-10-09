import type { Message } from "@/types/chat";
import ModelInfo from "./ModelInfo";

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="message message--user">
        <div className="message__body">{message.content}</div>
      </div>
    );
  }

  return (
    // F-02: los errores llevan role="alert" para que se anuncien de inmediato (como un Exception visible).
    <div
      className={`message message--assistant${message.isError ? " message--error" : ""}`}
      role={message.isError ? "alert" : undefined}
    >
      <img className="avatar" src="/logo.svg" alt="" aria-hidden="true" />
      <div className="message__body">
        {message.isError && <strong className="error-label">Error. </strong>}
        {message.content}
        <ModelInfo meta={message.meta} />
      </div>
    </div>
  );
}
