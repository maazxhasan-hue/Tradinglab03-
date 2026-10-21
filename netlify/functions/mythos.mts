export default async (request: Request) => {
  if (request.method !== "POST") return Response.json({ error: "Method not allowed" }, { status: 405, headers: { "Allow": "POST" } });
  const apiKey = Netlify.env.get("OPENAI_API_KEY");
  if (!apiKey) return Response.json({ error: "AI backend is not configured" }, { status: 503 });
  let body: { prompt?: unknown };
  try { body = await request.json(); } catch { return Response.json({ error: "Invalid JSON body" }, { status: 400 }); }
  if (typeof body.prompt !== "string" || !body.prompt.trim()) return Response.json({ error: "A prompt is required" }, { status: 400 });
  if (body.prompt.length > 18000) return Response.json({ error: "Prompt is too long (18,000 characters maximum)" }, { status: 413 });
  try {
    const upstream = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: { "Authorization": `Bearer ${apiKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({ model: "gpt-4o-mini", temperature: 0.85, max_tokens: 2200, messages: [{ role: "system", content: "You are Mythos, a master storyteller, worldbuilding architect, and narrative strategist. Follow the user's selected mode and slash commands. Use vivid sensory detail, causal worldbuilding, distinct character voices, consequential limitations, and end with a useful narrative hook. Be collaborative and avoid generic filler." }, { role: "user", content: body.prompt }] })
    });
    const data = await upstream.json().catch(() => ({}));
    if (!upstream.ok) {
      const message = upstream.status === 401 ? "AI provider rejected the configured key" : upstream.status === 429 ? "AI provider rate limit or quota reached" : "AI provider request failed";
      return Response.json({ error: message }, { status: upstream.status === 401 ? 502 : upstream.status === 429 ? 429 : 502 });
    }
    const text = data?.choices?.[0]?.message?.content;
    if (typeof text !== "string" || !text.trim()) return Response.json({ error: "AI provider returned no text" }, { status: 502 });
    return Response.json({ text }, { headers: { "Cache-Control": "no-store" } });
  } catch {
    return Response.json({ error: "AI service temporarily unavailable" }, { status: 502 });
  }
};
