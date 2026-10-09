import type { Conversation } from "@/types/chat";

interface SidebarProps {
  conversations: Conversation[];
  activeId: string;
  isOpen: boolean;
  onClose: () => void;
  onNew: () => void;
  onSelect: (id: string) => void;
}

export default function Sidebar({
  conversations,
  activeId,
  isOpen,
  onClose,
  onNew,
  onSelect,
}: SidebarProps) {
  return (
    <>
      {isOpen && <div className="backdrop" onClick={onClose} aria-hidden="true" />}
      <aside className={`sidebar${isOpen ? " sidebar--open" : ""}`} aria-label="Barra lateral">
        <div className="sidebar__top">
          <span className="brand">
            <img src="/logo.svg" alt="" width={32} height={32} />
            Web IA INNOVA
          </span>
          <button type="button" className="icon-btn sidebar__close" onClick={onClose} aria-label="Cerrar barra lateral">
            ×
          </button>
        </div>

        <button type="button" className="new-chat" onClick={() => { onNew(); onClose(); }}>
          + Nueva conversación
        </button>

        <nav className="history" aria-label="Historial de conversaciones">
          {conversations.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`history__item${c.id === activeId ? " history__item--active" : ""}`}
              aria-current={c.id === activeId ? "page" : undefined}
              onClick={() => { onSelect(c.id); onClose(); }}
            >
              {c.title}
            </button>
          ))}
        </nav>

        <div className="sidebar__bottom">
          <button type="button" className="sidebar__link" disabled title="Próximamente">
            Configuración
          </button>
          <button type="button" className="sidebar__link" disabled title="Próximamente">
            Cuenta
          </button>
        </div>
      </aside>
    </>
  );
}
