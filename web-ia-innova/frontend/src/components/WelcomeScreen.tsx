interface WelcomeScreenProps {
  onPick: (text: string) => void;
}

const SUGGESTIONS = [
  "Explícame qué es un orquestador de modelos de IA",
  "Ayúdame a redactar el resumen de un informe",
  "Revisa esta función y dime si tiene errores",
];

export default function WelcomeScreen({ onPick }: WelcomeScreenProps) {
  return (
    <div className="welcome">
      {/* Decorativo: la marca ya aparece como texto en la barra lateral */}
      <img className="welcome__logo" src="/logo.svg" alt="" aria-hidden="true" width={72} height={72} />
      {/* F-03: copy honesto. Es un prototipo; no prometemos ruteo real ni "el modelo adecuado". */}
      <h1>Prototipo de una interfaz multimodelo.</h1>
      <p>Escribe tu pregunta para probar la interfaz. Las respuestas que verás son simuladas.</p>
      <p className="welcome__notice" role="note">
        Prototipo en desarrollo: todavía no hay un orquestador real ni modelos de IA conectados.
      </p>
      <div className="welcome__suggestions">
        {SUGGESTIONS.map((s) => (
          <button key={s} type="button" className="suggestion" onClick={() => onPick(s)}>
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
