import { useState } from "react";
import { submitNote } from "./lib/api";
import "./index.css";

export default function App() { 
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastItem, setLastItem] = useState(null);

  async function onSubmit(e) {
    e.preventDefault(); // Prevendefault gør side ikke reloader
    if (!text.trim()) return; // Tjekker for tekst
    setLoading(true); // 
    setError("");
    try {
      const item = await submitNote(text.trim());
      setLastItem(item);
      setText("");
    } catch (err) {
      setError(err.message || "Noget gik galt");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <h1>Indsend note</h1>
      <form onSubmit={onSubmit} className="card"> // Knap der sender kode
        <label htmlFor="note">Note</label>
        <textarea // Stedet hvor man skriver tekst
          id="note"
          rows="6"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Skriv en kort note der skal analyseres"
          required
        />
        <button type="submit" disabled={loading || !text.trim()}> 
          {loading ? "Sender..." : "Send til analyse"}
        </button>
        {error && <div className="error">{error}</div>}
      </form>

      {lastItem && ( // Viser sidste resultat
        <div className="card">
          <h2>Sidste resultat</h2>
          <div className="meta">
            {new Date((lastItem.createdAt || 0) * 1000).toLocaleString()}
          </div>
          <div className="text">{lastItem.text}</div>
          {Array.isArray(lastItem.labels) && lastItem.labels.length > 0 && (
            <div className="labels">
              {lastItem.labels.map((l) => (
                <span key={l} className="chip">{l}</span>
              ))}
            </div>
          )}
          <div className="score">Score: {Math.round((lastItem.score || 0) * 100)}%</div>
        </div>
      )}
    </div>
  );
}
