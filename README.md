# 🤖 Aria — AI-Powered Tele-Calling Voice Agent

> A real-time conversational AI agent that makes and handles voice calls, understands natural speech, and responds with human-like voice and live text — built for scalable, automated customer outreach.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey?logo=flask)
![Groq](https://img.shields.io/badge/Groq-Llama%203.3-orange)
![Deepgram](https://img.shields.io/badge/Deepgram-Nova--2-green)
![License](https://img.shields.io/badge/License-MIT-purple)

---

## 1. Problem Statement

Businesses that rely on tele-calling face a critical scalability problem: human agents are expensive, inconsistent, and cannot operate 24/7. Existing robocall systems play pre-recorded messages and have zero ability to understand or respond to what the caller actually says — making them ineffective and frustrating. There is no affordable, open-source solution that combines real-time speech understanding, intelligent dynamic responses, and natural voice output in a single deployable system. This project addresses that gap by building a fully conversational AI calling agent that listens, understands, reasons, and speaks — handling FAQs, objections, and general queries without any human involvement. The result is a system that small and mid-sized businesses in India can deploy immediately at near-zero cost using free-tier APIs.

---

## 2. Features

| Feature | Description |
|---------|-------------|
| 🎙️ Real-time speech recognition | Converts caller's voice to text using Deepgram Nova-2 with Indian English support |
| 🧠 Conversational AI responses | Generates context-aware replies using Groq-hosted Llama 3.3 70B with full conversation memory |
| 🔊 Text-to-speech output | Every reply is spoken aloud via browser Web Speech API (or ElevenLabs for natural voice) |
| 💬 Live chat UI | Chat bubble interface shows the full conversation transcript in real time |
| 🏷️ Intent detection | Automatically classifies every user response into intents: interested, callback_requested, ended, etc. |
| 🎤 Mic button | One-click voice input using browser's Web Speech Recognition — no extra software needed |
| ⌨️ Text input fallback | Users can type messages if mic is unavailable |
| 🔄 Multi-call support | Reset button starts a fresh conversation without restarting the server |
| 💾 Conversation logging | Every call is saved as a timestamped JSON file with full transcript and final intent |
| 🔇 Voice toggle | User can mute/unmute AI voice output at any time |

---

## 3. Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| Python 3.11 | Core application language |
| Flask | Lightweight web server and REST API |
| Groq API (Llama 3.3-70B) | Large language model for generating AI responses |
| Deepgram SDK (Nova-2) | Cloud speech-to-text transcription |
| sounddevice | Microphone audio capture |
| scipy | WAV file encoding for audio buffer |
| pyttsx3 | Offline text-to-speech fallback |

### Frontend
| Technology | Purpose |
|-----------|---------|
| HTML / CSS / Vanilla JS | Interactive chat interface |
| Web Speech API (Browser built-in) | Browser-native voice input (mic) and voice output (TTS) |
| ElevenLabs SDK (optional) | High-quality natural voice TTS as an upgrade |

---

## 4. Project Structure

```
voice-ai-caller/
│
├── app.py              # Flask web server, all routes, and the full chat UI (HTML embedded)
├── ai_engine.py        # Groq/Llama AI brain — builds prompts, manages conversation history, detects intent
├── voice.py            # Deepgram STT client, microphone recorder, pyttsx3/ElevenLabs TTS
├── requirements.txt    # All Python dependencies
├── call_logs/          # Auto-created at runtime — stores JSON logs of every conversation
└── README.md           # This file
```

**Key design decision:** The entire frontend UI is embedded as a string inside `app.py` — this keeps the project as a single-folder deployment with zero build steps, no npm, and no template directories.

---

## 5. Installation & Setup

### Prerequisites
- Python 3.11 installed
- A microphone connected to your computer
- A modern browser (Chrome recommended for Web Speech API)

### Step 1 — Clone the repository
```bash
git clone https://github.com/your-username/voice-ai-caller.git
cd voice-ai-caller
```

### Step 2 — Install dependencies
```bash
pip install flask groq deepgram-sdk sounddevice scipy pyttsx3
```

### Step 3 — Get free API keys

**Groq (AI brain) — Free:**
1. Go to https://console.groq.com
2. Sign up → API Keys → Create API Key
3. Copy the key (starts with `gsk_`)

**Deepgram (Speech-to-text) — Free $200 credits:**
1. Go to https://console.deepgram.com
2. Sign up → API Keys → Create a New API Key
3. Copy the key

### Step 4 — Add your API keys

Open `ai_engine.py` and paste your Groq key on line 7:
```python
GROQ_API_KEY = "gsk_your_key_here"
```

Open `voice.py` and paste your Deepgram key on line 11:
```python
DEEPGRAM_API_KEY = "your_deepgram_key_here"
```

### Step 5 — Run the application
```bash
python app.py
```

### Step 6 — Open in browser
```
http://localhost:5000
```

Aria will greet you automatically. Click the 🎤 mic button to speak, or type in the text box.

---

## 6. How It Works

### Voice Input Flow
1. User clicks the 🎤 mic button in the browser
2. Browser Web Speech API captures microphone audio and transcribes it locally
3. Transcribed text is sent to `/chat` endpoint via POST request
4. `ai_engine.py` appends the message to the full conversation history
5. Groq API sends the history + system prompt to Llama 3.3-70B
6. The model returns a reply and an `INTENT:` tag on a new line
7. `app.py` splits the reply from the intent and returns both as JSON
8. Browser renders the reply as a chat bubble and speaks it aloud via Web Speech API

### Speech-to-Text Flow (Python mic recording — alternative mode)
1. `voice.py` records audio from system microphone using `sounddevice` at 16kHz
2. Audio is written to a temporary `.wav` file using `scipy`
3. File buffer is sent to Deepgram Nova-2 REST API with `language=en-IN`
4. Deepgram returns the transcript which is returned to the caller

### Intent Detection Flow
1. The system prompt instructs Llama to append `INTENT: <word>` after every reply
2. `ai_engine.py` splits the raw output on `"INTENT:"` to extract reply and intent separately
3. Intent is returned to the frontend and displayed as a colour-coded badge under each message
4. `app.py` logs specific intents (`interested`, `callback_requested`) to the console for CRM follow-up

### Conversation Memory Flow
1. Every user message and AI reply is stored in `_history` list as role/content pairs
2. The full history is passed to Groq on every API call — the model sees the entire conversation
3. On `/reset`, history is cleared and reinitialized with just the system prompt
4. On `/log`, the full history is returned as JSON and downloaded as a call log file

---

## 7. Scalability

**Concurrent users:** The current Flask dev server is single-threaded. For production, replace with `gunicorn --workers 4 app:app` — each worker handles independent sessions. Because conversation history is stored in Python module-level globals, a production deployment would move `_history` to Redis or a session store keyed by user ID to support true multi-user concurrency.

**Data volume:** Call logs are written as flat JSON files. For high call volumes (1000+ calls/day), logs should be ingested into a database (PostgreSQL or MongoDB). The JSON schema is already structured for direct insertion — each log contains timestamp, turns, final intent, and full message history.

**API rate limits:** Groq free tier allows 30 requests/minute and 14,400/day on Llama 3.3-70B. For production scale, Groq paid tier or a self-hosted Ollama instance on a GPU server eliminates this bottleneck entirely. Deepgram free tier handles 45 minutes of audio — paid tier removes limits.

**Deployment:** The app is stateless at the HTTP layer (state lives in-process). Containerising with Docker takes one `Dockerfile` — the app has no native binary dependencies beyond Python packages. Deployment to Railway, Render, or a ₹500/month VPS is straightforward.

**Identified bottleneck:** The biggest bottleneck is Groq API latency (~400–800ms per call). This can be reduced by streaming the response token-by-token and beginning TTS playback before the full reply is generated — a streaming upgrade path that the architecture already supports.

---

## 8. Feasibility

**Immediately deployable:** All dependencies are pip-installable Python packages. There are no compiled binaries, no GPU requirements, and no Docker required for local use. The entire system runs on a standard laptop.

**Free to run:** Groq and Deepgram both offer generous free tiers sufficient for a hackathon demo and early-stage testing. ElevenLabs (optional) adds a natural voice for $0 on the free tier (10,000 characters/month).

**Production path:** Taking this to production requires three changes: (1) move conversation state to Redis for multi-user support, (2) swap Flask dev server for gunicorn, (3) add Twilio or VAPI integration for real outbound phone calls instead of browser-based mic input. All three are well-documented and achievable within days.

**Infrastructure requirements:** A single 1-core VPS with 512MB RAM is sufficient to serve the Flask app and handle Groq/Deepgram API proxying. No GPU, no Kubernetes, no complex infrastructure needed at this stage.

**Dependency risk:** Groq and Deepgram are third-party APIs. If either goes down, the system fails gracefully — Deepgram has a pyttsx3 offline fallback, and Groq can be swapped for Ollama (local) or OpenAI with a one-line model name change.

---

## 9. Novelty

Existing solutions fall into two categories: (1) enterprise platforms like VAPI and Twilio AI that cost hundreds of dollars per month and require no-code configuration, and (2) simple Python chatbots that work in text only with no voice pipeline. **Aria fills the gap between these two extremes.**

Specifically, what is novel here:

- **Open-source, zero-cost voice AI calling stack** — combines Groq (free LLM), Deepgram (free STT), and Web Speech API (browser-native TTS) into a coherent pipeline that costs nothing to run at demo scale.
- **Dual-output interaction model** — every response is simultaneously printed as text and spoken aloud. Most voice assistants do one or the other; this system does both so the user can read and listen at the same time — important for accessibility and noisy environments.
- **Intent tagging built into the LLM prompt** — rather than training a separate intent classifier, the system prompt instructs the LLM to self-report its detected intent after every reply. This eliminates an entire ML pipeline while producing reliable intent labels for CRM logging.
- **India-first design** — the STT is configured for `en-IN` (Indian English accent), the campaign is priced in rupees, and the callback number format follows Indian standards. Most open-source calling tools are built for US/UK English and break on Indian accents.

---

## 10. Feature Depth

### Conversation Memory
The full conversation history is passed to the LLM on every API call. This means Aria remembers context across the entire call — if a user says "I mentioned I run a small business" five turns ago, Aria's next reply accounts for it. Most simple chatbots reset context on every message.

### Intent Detection Edge Cases
- If the LLM omits the `INTENT:` tag (rare but possible), the code defaults to `"unclear"` without crashing — the `split("INTENT:")` check is guarded.
- Intent words are lowercased and only the first word is taken — so `"interested, wants callback"` correctly extracts `"interested"`.
- The `ended` intent triggers call termination in the loop — preventing the agent from continuing to talk after the user says goodbye.

### Silent Turn Handling
If Deepgram returns an empty transcript (silence, background noise, or mic off), the system counts silent turns. After 2 consecutive silent turns, Aria says a polite goodbye and ends the session — preventing infinite silent loops.

### Configurable Campaign
The entire product pitch, pricing, features, and callback number live in a single `CAMPAIGN` dictionary in `ai_engine.py`. Changing the campaign requires editing one dictionary — no prompt engineering needed.

### Conversation Logs
Each saved log contains: ISO timestamp, turn count, final detected intent, and the full message history with roles. This structure is directly queryable for conversion rate analysis — e.g. count logs where `final_intent == "interested"` divided by total logs gives conversion rate.

---

## 11. Ethical Use & Disclaimer

This project is built for **legitimate business use cases** such as customer support, product demos, and outreach with prior consent. 

- **Do not use this system to make unsolicited calls** to people who have not consented to being contacted — this may violate TRAI regulations in India and equivalent laws in other countries.
- **Disclose that the caller is an AI** when required by law or when directly asked. The system prompt instructs Aria not to proactively claim to be human.
- **Conversation logs contain personal data** (voice transcripts). Store and handle them in compliance with applicable data protection laws (IT Act 2000 in India, GDPR in Europe).
- This project does not make real phone calls by default — it runs in-browser. Twilio/VAPI integration for real outbound calls must be added separately and used responsibly.

---

## 12. License

This project is licensed under the **MIT License**.

```
MIT License — Copyright (c) 2025 Balam

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software to use, copy, modify, merge, publish, and distribute it,
subject to the conditions of the MIT License.
```

See the [LICENSE](LICENSE) file for full details.

---

## 13. Author

**Balam**
- 📧 Email: your-email@example.com
- 🐙 GitHub: [@your-username](https://github.com/your-username)
- 🏫 Institution: Your College Name

---

> ⭐ If this project helped you, please star the repository on GitHub!
