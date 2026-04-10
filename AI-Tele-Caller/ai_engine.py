from datetime import datetime
from groq import Groq

# ============================================================
#  PASTE YOUR GROQ API KEY BELOW
#  Free key from: https://console.groq.com → API Keys
# ============================================================
GROQ_API_KEY = "PASTE_GROQ_KEY_HERE
# ============================================================

_client = Groq(api_key=GROQ_API_KEY)

CAMPAIGN = {
    "company"  : "TechSolutions India",
    "product"  : "SmartCRM Pro",
    "price"    : "999 rupees per month",
    "offer"    : "30-day free trial, no credit card required",
    "features" : ["Automated lead tracking", "WhatsApp and email integration",
                  "Sales analytics dashboard", "24/7 support"],
    "callback" : "+91-98765-43210",
}

SYSTEM_PROMPT = f"""You are Aria, a friendly AI voice assistant from {CAMPAIGN['company']}.

You do TWO things:
1. Answer ANY question on any topic — science, history, travel, jokes, sports, tech, cooking, etc.
2. Promote {CAMPAIGN['product']} naturally when relevant.

Product info:
- Price: {CAMPAIGN['price']}  |  Offer: {CAMPAIGN['offer']}
- Features: {', '.join(CAMPAIGN['features'])}
- Callback: {CAMPAIGN['callback']}

STRICT RULES:
- Always respond in 1–2 SHORT sentences only (this is a live voice call).
- Be warm, natural and conversational — like a real person on a phone call.
- Never say you cannot answer something.
- Never use bullet points or lists — only plain spoken sentences.
- After your reply write on a new line: INTENT: <word>
  Words: interested | not_interested | callback_requested | product_faq | general_question | ended | unclear
"""

_history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
_last_intent = "unclear"
_turns = 0


def get_ai_response(user_text: str) -> tuple[str, str]:
    global _last_intent, _turns

    _history.append({"role": "user", "content": user_text})

    res = _client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=_history,
        max_tokens=120,
        temperature=0.75,
    )

    raw = res.choices[0].message.content.strip()
    reply, intent = raw, "unclear"

    if "INTENT:" in raw:
        parts = raw.split("INTENT:")
        reply  = parts[0].strip()
        intent = parts[1].strip().lower().split()[0]

    _last_intent = intent
    _turns += 1
    _history.append({"role": "assistant", "content": raw})
    return reply, intent


def get_conversation_summary() -> dict:
    return {
        "timestamp"    : datetime.now().isoformat(),
        "turns"        : _turns,
        "final_intent" : _last_intent,
        "history"      : [{"role": m["role"], "text": m["content"]}
                          for m in _history if m["role"] != "system"],
        "campaign"     : CAMPAIGN["product"],
    }


def reset_conversation() -> None:
    global _history, _last_intent, _turns
    _history      = [{"role": "system", "content": SYSTEM_PROMPT}]
    _last_intent  = "unclear"
    _turns        = 0