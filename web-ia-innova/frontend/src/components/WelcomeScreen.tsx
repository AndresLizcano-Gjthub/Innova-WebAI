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
      <img className="welcome__logo" src="/logo.svg" alt="Logo de Web IA INNOVA" width={72} height={72} />
      <h1>Una sola interfaz, el modelo adecuado para cada tarea.</h1>
      <p>Escribe tu pregunta. Web IA INNOVA la envía al orquestador del proyecto.</p>
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
