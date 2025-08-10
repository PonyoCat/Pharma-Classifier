const API = import.meta.env.VITE_API_BASE; // Henter addresse 

export async function submitNote(text) { // Sender teksten til backend så vi kan evaluere den og gemme i database
  const r = await fetch(`${API}/analyze`, { 
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text })
  });
  if (!r.ok) {
    const msg = await r.text().catch(() => "Analyze failed");
    throw new Error(msg || "Analyze failed");
  }
  return r.json();
}
