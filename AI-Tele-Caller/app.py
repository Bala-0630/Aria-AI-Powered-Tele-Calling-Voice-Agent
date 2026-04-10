import json
import os
import threading
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, Response
from ai_engine import get_ai_response, get_conversation_summary, reset_conversation
from voice import record_audio, speech_to_text

app = Flask(__name__)
LOG_DIR = Path("call_logs")
LOG_DIR.mkdir(exist_ok=True)

# ── HTML UI ───────────────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aria — AI Voice Assistant</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Segoe UI', sans-serif;
    background: #0f0f1a;
    color: #e0e0e0;
    height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  /* ── Header ── */
  .header {
    width: 100%;
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    padding: 16px 32px;
    display: flex;
    align-items: center;
    gap: 14px;
    border-bottom: 1px solid #2a2a4a;
  }
  .avatar {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, #6c63ff, #3ecfcf);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
  }
  .header-info h1 { font-size: 18px; font-weight: 600; color: #fff; }
  .header-info p  { font-size: 12px; color: #888; }
  .status-dot {
    width: 10px; height: 10px;
    background: #2ecc71;
    border-radius: 50%;
    margin-left: auto;
    box-shadow: 0 0 6px #2ecc71;
    animation: pulse 1.5s infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

  /* ── Chat window ── */
  .chat-wrapper {
    width: 100%; max-width: 780px;
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 20px 16px 0;
    overflow: hidden;
  }
  #chat {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
    padding-bottom: 12px;
    scroll-behavior: smooth;
  }
  #chat::-webkit-scrollbar { width: 4px; }
  #chat::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }

  /* ── Messages ── */
  .msg { display: flex; gap: 10px; align-items: flex-start; max-width: 85%; }
  .msg.aria  { align-self: flex-start; }
  .msg.user  { align-self: flex-end; flex-direction: row-reverse; }

  .msg-icon {
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; flex-shrink: 0;
  }
  .msg.aria  .msg-icon { background: linear-gradient(135deg,#6c63ff,#3ecfcf); }
  .msg.user  .msg-icon { background: #2a2a4a; }

  .bubble {
    padding: 10px 14px;
    border-radius: 16px;
    font-size: 14.5px;
    line-height: 1.55;
  }
  .msg.aria .bubble {
    background: #1e1e35;
    border: 1px solid #2a2a5a;
    border-top-left-radius: 4px;
    color: #dce0ff;
  }
  .msg.user .bubble {
    background: #6c63ff;
    border-top-right-radius: 4px;
    color: #fff;
  }

  .msg-meta {
    font-size: 10px;
    color: #555;
    margin-top: 3px;
    padding: 0 4px;
  }
  .msg.user .msg-meta { text-align: right; }

  /* Intent badge */
  .intent-badge {
    font-size: 10px;
    padding: 2px 7px;
    border-radius: 99px;
    margin-top: 4px;
    display: inline-block;
  }
  .intent-general   { background:#1e3a2f; color:#2ecc71; }
  .intent-interested{ background:#1e2a4a; color:#3ecfcf; }
  .intent-product   { background:#2a1e4a; color:#a78bfa; }
  .intent-ended     { background:#3a1e1e; color:#e74c3c; }
  .intent-other     { background:#2a2a2a; color:#888; }

  /* Typing indicator */
  .typing .bubble { display:flex; gap:5px; align-items:center; padding:14px; }
  .dot { width:7px;height:7px;background:#6c63ff;border-radius:50%;
         animation:bounce 1s infinite; }
  .dot:nth-child(2){animation-delay:.15s}
  .dot:nth-child(3){animation-delay:.3s}
  @keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}

  /* ── Controls ── */
  .controls {
    width: 100%; max-width: 780px;
    padding: 16px;
    background: #0f0f1a;
    border-top: 1px solid #1e1e35;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .input-row {
    display: flex;
    gap: 10px;
    align-items: center;
  }

  #text-input {
    flex: 1;
    background: #1a1a2e;
    border: 1px solid #2a2a5a;
    border-radius: 24px;
    padding: 11px 18px;
    color: #e0e0e0;
    font-size: 14px;
    outline: none;
    transition: border 0.2s;
  }
  #text-input:focus { border-color: #6c63ff; }
  #text-input::placeholder { color: #444; }

  .btn {
    border: none; cursor: pointer;
    border-radius: 50%;
    width: 44px; height: 44px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    transition: transform 0.15s, opacity 0.15s;
  }
  .btn:hover  { transform: scale(1.08); }
  .btn:active { transform: scale(0.95); }

  #send-btn { background: #6c63ff; }
  #mic-btn  { background: #1e1e35; border: 1px solid #2a2a5a; }
  #mic-btn.recording { background: #e74c3c; border-color: #e74c3c;
                        animation: mic-pulse 0.8s infinite; }
  @keyframes mic-pulse { 0%,100%{box-shadow:0 0 0 0 rgba(231,76,60,0.5)}
                         50%{box-shadow:0 0 0 8px rgba(231,76,60,0)} }

  .btn-row {
    display: flex;
    gap: 8px;
    justify-content: center;
  }
  .action-btn {
    background: #1a1a2e;
    border: 1px solid #2a2a5a;
    color: #aaa;
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
  }
  .action-btn:hover { border-color: #6c63ff; color: #6c63ff; }

  #status-bar {
    text-align: center;
    font-size: 11px;
    color: #555;
    height: 14px;
  }
</style>
</head>
<body>

<div class="header">
  <div class="avatar">🤖</div>
  <div class="header-info">
    <h1>Aria — AI Voice Assistant</h1>
    <p>TechSolutions India · SmartCRM Pro</p>
  </div>
  <div class="status-dot"></div>
</div>

<div class="chat-wrapper">
  <div id="chat"></div>
</div>

<div class="controls">
  <div id="status-bar">Ready</div>
  <div class="input-row">
    <input id="text-input" type="text" placeholder="Type your message or use the mic…" autocomplete="off"/>
    <button class="btn" id="mic-btn"  title="Hold to speak">🎤</button>
    <button class="btn" id="send-btn" title="Send">➤</button>
  </div>
  <div class="btn-row">
    <button class="action-btn" onclick="resetCall()">🔄 New Call</button>
    <button class="action-btn" onclick="saveLog()">💾 Save Log</button>
    <button class="action-btn" id="tts-toggle" onclick="toggleTTS()">🔊 Voice ON</button>
  </div>
</div>

<script>
const chat       = document.getElementById('chat');
const input      = document.getElementById('text-input');
const micBtn     = document.getElementById('mic-btn');
const statusBar  = document.getElementById('status-bar');
let voiceEnabled = true;
let isRecording  = false;

// ── TTS via browser Web Speech API ──────────────────────────────────────────
function speakText(text) {
  if (!voiceEnabled) return;
  window.speechSynthesis.cancel();
  const utt  = new SpeechSynthesisUtterance(text);
  utt.rate   = 0.95;
  utt.pitch  = 1.05;
  utt.volume = 1;
  // Pick a female voice if available
  const voices = window.speechSynthesis.getVoices();
  const female = voices.find(v =>
    v.name.includes('Female') || v.name.includes('Zira') ||
    v.name.includes('Samantha') || v.name.includes('Google UK English Female')
  );
  if (female) utt.voice = female;
  window.speechSynthesis.speak(utt);
}

// Load voices (Chrome needs this trigger)
window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();

// ── Add message bubble ───────────────────────────────────────────────────────
function addMessage(role, text, intent='') {
  const wrapper = document.createElement('div');
  wrapper.className = `msg ${role}`;

  const icon   = document.createElement('div');
  icon.className = 'msg-icon';
  icon.textContent = role === 'aria' ? '🤖' : '👤';

  const right  = document.createElement('div');

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;

  const meta = document.createElement('div');
  meta.className = 'msg-meta';
  meta.textContent = new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});

  right.appendChild(bubble);

  if (intent && role === 'aria') {
    const badge = document.createElement('span');
    badge.className = 'intent-badge ' + intentClass(intent);
    badge.textContent = intent;
    right.appendChild(badge);
  }

  right.appendChild(meta);
  wrapper.appendChild(icon);
  wrapper.appendChild(right);
  chat.appendChild(wrapper);
  chat.scrollTop = chat.scrollHeight;
  return wrapper;
}

function intentClass(i) {
  if (i === 'general_question')    return 'intent-general';
  if (i === 'interested')          return 'intent-interested';
  if (i.includes('product') || i.includes('faq')) return 'intent-product';
  if (i === 'ended')               return 'intent-ended';
  return 'intent-other';
}

function showTyping() {
  const el = document.createElement('div');
  el.className = 'msg aria typing';
  el.id = 'typing';
  el.innerHTML = `
    <div class="msg-icon">🤖</div>
    <div class="bubble"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
  chat.appendChild(el);
  chat.scrollTop = chat.scrollHeight;
}

function hideTyping() {
  const el = document.getElementById('typing');
  if (el) el.remove();
}

function setStatus(msg) { statusBar.textContent = msg; }

// ── Send text message ────────────────────────────────────────────────────────
async function sendMessage(text) {
  if (!text.trim()) return;
  input.value = '';
  addMessage('user', text);
  showTyping();
  setStatus('Aria is thinking…');

  try {
    const res  = await fetch('/chat', {
      method : 'POST',
      headers: {'Content-Type':'application/json'},
      body   : JSON.stringify({text})
    });
    const data = await res.json();
    hideTyping();

    if (data.reply) {
      addMessage('aria', data.reply, data.intent);
      speakText(data.reply);          // 🔊 speaks out loud
      setStatus('Ready');
    }
  } catch(e) {
    hideTyping();
    setStatus('Error — check server');
  }
}

// ── Mic button (browser Web Speech Recognition) ──────────────────────────────
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

if (SpeechRecognition) {
  recognition = new SpeechRecognition();
  recognition.lang        = 'en-IN';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = (e) => {
    const spoken = e.results[0][0].transcript;
    input.value  = spoken;
    sendMessage(spoken);
  };
  recognition.onend = () => {
    micBtn.classList.remove('recording');
    isRecording = false;
    setStatus('Ready');
  };
  recognition.onerror = (e) => {
    micBtn.classList.remove('recording');
    isRecording = false;
    setStatus('Mic error: ' + e.error);
  };
} else {
  micBtn.title = 'Speech recognition not supported — use text input';
}

micBtn.addEventListener('click', () => {
  if (!recognition) { setStatus('Use text input — mic not supported in this browser'); return; }
  if (isRecording) {
    recognition.stop();
  } else {
    window.speechSynthesis.cancel();   // stop Aria speaking before we listen
    recognition.start();
    micBtn.classList.add('recording');
    isRecording = true;
    setStatus('🎤 Listening… speak now');
  }
});

// ── Send on Enter / button ───────────────────────────────────────────────────
document.getElementById('send-btn').addEventListener('click', () => sendMessage(input.value));
input.addEventListener('keydown', e => { if (e.key === 'Enter') sendMessage(input.value); });

// ── Toggle TTS ───────────────────────────────────────────────────────────────
function toggleTTS() {
  voiceEnabled = !voiceEnabled;
  document.getElementById('tts-toggle').textContent = voiceEnabled ? '🔊 Voice ON' : '🔇 Voice OFF';
  if (!voiceEnabled) window.speechSynthesis.cancel();
}

// ── New call ─────────────────────────────────────────────────────────────────
async function resetCall() {
  await fetch('/reset', {method:'POST'});
  chat.innerHTML = '';
  setStatus('New call started');
  startGreeting();
}

// ── Save log ─────────────────────────────────────────────────────────────────
async function saveLog() {
  const res  = await fetch('/log');
  const data = await res.json();
  const blob = new Blob([JSON.stringify(data, null, 2)], {type:'application/json'});
  const a    = document.createElement('a');
  a.href     = URL.createObjectURL(blob);
  a.download = `call_${Date.now()}.json`;
  a.click();
  setStatus('Log downloaded');
}

// ── Greeting on load ─────────────────────────────────────────────────────────
async function startGreeting() {
  showTyping();
  setStatus('Aria is connecting…');
  const res  = await fetch('/greet');
  const data = await res.json();
  hideTyping();
  addMessage('aria', data.reply);
  speakText(data.reply);
  setStatus('Ready');
}

window.addEventListener('load', startGreeting);
</script>
</body>
</html>
"""

# ── Flask routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/greet")
def greet():
    reset_conversation()
    greeting = (
        "Hello! This is charu How can I Assist you today?"
    )
    return jsonify({"reply": greeting})


@app.route("/chat", methods=["POST"])
def chat():
    data      = request.get_json()
    user_text = data.get("text", "").strip()
    if not user_text:
        return jsonify({"reply": "I did not catch that. Could you repeat?", "intent": "unclear"})
    reply, intent = get_ai_response(user_text)
    return jsonify({"reply": reply, "intent": intent})


@app.route("/reset", methods=["POST"])
def reset():
    reset_conversation()
    return jsonify({"status": "ok"})


@app.route("/log")
def log():
    return jsonify(get_conversation_summary())


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  🚀 Aria AI Voice Assistant")
    print("  Open in browser: http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(debug=False, port=5000)