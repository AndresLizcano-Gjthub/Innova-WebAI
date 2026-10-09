// Tres puntos animados mientras se espera la respuesta.
// role="status" + aria-live avisa a lectores de pantalla sin interrumpir.
export default function LoadingIndicator() {
  return (
    <div className="message message--assistant" role="status" aria-live="polite">
      <img className="avatar" src="/logo.svg" alt="" aria-hidden="true" />
      <div className="message__body">
        <div className="dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <span className="sr-only">La IA está procesando tu solicitud</span>
      </div>
    </div>
  );
}
