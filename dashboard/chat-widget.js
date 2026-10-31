(() => {
  "use strict";
  if (window.__nexoraChatLoaded) return;
  window.__nexoraChatLoaded = true;
  const script = document.currentScript;
  const apiBase = (script && script.dataset.apiBase || "https://tradinglab03-intake.maazxhasan.workers.dev").replace(/\/$/, "");
  const css = `
  #nexora-chat-launcher{position:fixed;right:22px;bottom:22px;z-index:99998;border:0;border-radius:999px;background:#6d5dfc;color:#fff;padding:14px 19px;font:600 15px system-ui;box-shadow:0 10px 32px #0003;cursor:pointer}
  #nexora-chat-panel{position:fixed;right:18px;bottom:84px;width:min(370px,calc(100vw - 28px));height:min(570px,calc(100dvh - 120px));z-index:99999;background:#fff;color:#151525;border:1px solid #e6e5f2;border-radius:20px;box-shadow:0 22px 70px #10102435;display:none;overflow:hidden;font:14px/1.45 system-ui}
  #nexora-chat-panel *{box-sizing:border-box}#nexora-chat-panel.nx-open{display:flex;flex-direction:column}
  .nx-head{padding:17px;background:linear-gradient(135deg,#17172e,#41318b);color:#fff;display:flex;align-items:center;gap:11px}.nx-voice,.nx-mic{border:1px solid #aaa1ff;border-radius:10px;background:#ffffff16;color:#fff;padding:8px 10px;cursor:pointer}.nx-voice[aria-pressed=true]{background:#b8f5e8;color:#11252c}.nx-mic{background:#f3f1ff;color:#3b327c;border-color:#dedafc}.nx-mark{width:38px;height:38px;border-radius:12px;background:#ffffff22;display:grid;place-items:center;font-weight:800}.nx-head strong{display:block;font-size:15px}.nx-head small{opacity:.8}.nx-close{margin-left:auto;background:transparent;color:white;border:0;font-size:24px;cursor:pointer}
  .nx-messages{flex:1;overflow:auto;padding:15px;display:flex;flex-direction:column;gap:10px;background:#fafaff}.nx-msg{max-width:88%;white-space:pre-wrap;overflow-wrap:anywhere;padding:10px 12px;border-radius:14px;background:#eeeefa;align-self:flex-start}.nx-msg.nx-user{background:#6555e8;color:#fff;align-self:flex-end}.nx-msg.nx-wait{opacity:.65;font-style:italic}.nx-suggestions{display:flex;gap:6px;flex-wrap:wrap;padding:0 12px 10px;background:#fafaff}.nx-suggestions button{border:1px solid #dedafc;border-radius:999px;background:white;padding:7px 10px;color:#3b327c;cursor:pointer;font-size:12px}.nx-form{display:flex;gap:8px;padding:12px;border-top:1px solid #eee}.nx-form input{min-width:0;flex:1;border:1px solid #dddbea;border-radius:12px;padding:12px;font:inherit}.nx-form button{border:0;border-radius:12px;background:#6555e8;color:#fff;padding:0 15px;font-weight:700;cursor:pointer}.nx-form button:disabled{opacity:.55}.nx-note{font-size:10px;color:#777;padding:0 13px 10px;background:white}.nx-error{color:#9c2e38}
  @media(prefers-reduced-motion:no-preference){#nexora-chat-launcher{transition:transform .15s}#nexora-chat-launcher:hover{transform:translateY(-2px)}}
  `;
  const style = document.createElement("style"); style.textContent = css; document.head.appendChild(style);
  const panel = document.createElement("section"); panel.id = "nexora-chat-panel"; panel.setAttribute("aria-label","Nexora AI chat");
  panel.innerHTML = '<div class="nx-head"><div class="nx-mark">N</div><div><strong>Nexora AI</strong><small>Website assistant · Voice optional</small></div><button class="nx-voice" type="button" aria-label="Toggle spoken replies" aria-pressed="false" title="Toggle spoken replies">🔊</button><button class="nx-close" aria-label="Close chat">×</button></div><div class="nx-messages" aria-live="polite"></div><div class="nx-suggestions"><button type="button">What does Nexora do?</button><button type="button">How do I get started?</button><button type="button">Discuss a project</button></div><form class="nx-form"><input aria-label="Your message" maxlength="1200" placeholder="Ask Nexora a question…" required><button class="nx-mic" type="button" aria-label="Speak your message" title="Speak your message">🎙</button><button type="submit">Send</button></form><div class="nx-note">Voice input and spoken replies use your browser. Please don\'t share passwords, payment details, or sensitive personal data.</div>';
  const launcher = document.createElement("button"); launcher.id = "nexora-chat-launcher"; launcher.type = "button"; launcher.textContent = "✦ Chat with Nexora";
  document.body.append(panel, launcher);
  const messages = panel.querySelector(".nx-messages"), form = panel.querySelector("form"), input = form.querySelector("input"), send = form.querySelector('button[type="submit"]'), mic = panel.querySelector(".nx-mic"), voiceToggle = panel.querySelector(".nx-voice");
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null, spokenReplies = false;
  const history = [];
  function add(text, role, extra) { const el = document.createElement("div"); el.className = "nx-msg" + (role === "user" ? " nx-user" : "") + (extra || ""); el.textContent = text; messages.appendChild(el); messages.scrollTop = messages.scrollHeight; return el; }
  function open() { panel.classList.add("nx-open"); launcher.setAttribute("aria-expanded","true"); if (!messages.childElementCount) add("Hi! I'm Nexora's website assistant. I can explain our AI capabilities and help you prepare a project enquiry. What would you like to know?","assistant"); input.focus(); }
  launcher.addEventListener("click", () => panel.classList.contains("nx-open") ? (panel.classList.remove("nx-open"), launcher.setAttribute("aria-expanded","false")) : open());
  panel.querySelector(".nx-close").addEventListener("click", () => { panel.classList.remove("nx-open"); launcher.setAttribute("aria-expanded","false"); if ("speechSynthesis" in window) window.speechSynthesis.cancel(); });
  voiceToggle.addEventListener("click", () => {
    spokenReplies = !spokenReplies;
    voiceToggle.setAttribute("aria-pressed", String(spokenReplies));
    voiceToggle.title = spokenReplies ? "Turn spoken replies off" : "Turn spoken replies on";
    if (!spokenReplies && "speechSynthesis" in window) window.speechSynthesis.cancel();
    add(spokenReplies ? "Spoken replies enabled. Your browser will read assistant answers aloud." : "Spoken replies disabled.", "assistant");
  });
  mic.addEventListener("click", () => {
    if (!SpeechRecognition) { add("Voice input is not supported in this browser. You can type your message instead.", "assistant", " nx-error"); return; }
    if (recognition) { recognition.stop(); recognition = null; mic.textContent = "🎙"; mic.setAttribute("aria-label", "Speak your message"); return; }
    recognition = new SpeechRecognition(); recognition.lang = "en-IN"; recognition.interimResults = false; recognition.maxAlternatives = 1;
    mic.textContent = "●"; mic.setAttribute("aria-label", "Stop voice input");
    recognition.onresult = event => { input.value = String(event.results?.[0]?.[0]?.transcript || "").trim(); if (input.value) form.requestSubmit(); };
    recognition.onerror = event => add("Voice input failed (" + String(event.error || "unknown error") + "). Please type your message instead.", "assistant", " nx-error");
    recognition.onend = () => { recognition = null; mic.textContent = "🎙"; mic.setAttribute("aria-label", "Speak your message"); };
    try { recognition.start(); } catch (error) { recognition = null; mic.textContent = "🎙"; mic.setAttribute("aria-label", "Speak your message"); add("Could not start voice input. Check microphone permission and try again.", "assistant", " nx-error"); }
  });
  panel.querySelectorAll(".nx-suggestions button").forEach(b => b.addEventListener("click", () => { input.value = b.textContent; form.requestSubmit(); }));
  form.addEventListener("submit", async e => {
    e.preventDefault(); const message = input.value.trim(); if (!message || send.disabled) return;
    input.value = ""; add(message,"user"); history.push({role:"user",content:message}); if (history.length > 12) history.splice(0,2);
    send.disabled = true; const wait = add("Thinking…","assistant"," nx-wait");
    try {
      const response = await fetch(apiBase + "/api/chat", {method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({message,history:history.slice(-8)})});
      const data = await response.json().catch(() => ({}));
      wait.remove();
      if (!response.ok || typeof data.reply !== "string") throw new Error(data.error || "The chat service is not configured yet.");
      const reply = data.reply.slice(0,3000); add(reply,"assistant"); history.push({role:"assistant",content:reply}); if(history.length>12)history.splice(0,2);
      if (spokenReplies && "speechSynthesis" in window) { window.speechSynthesis.cancel(); const utterance = new SpeechSynthesisUtterance(reply); utterance.lang = "en-IN"; window.speechSynthesis.speak(utterance); }
    } catch (err) {
      wait.remove(); add("Sorry, the AI chat service isn't connected yet. You can still use the project enquiry form on this website, and we won't pretend your message was sent.","assistant"," nx-error");
    } finally { send.disabled = false; input.focus(); }
  });
})();