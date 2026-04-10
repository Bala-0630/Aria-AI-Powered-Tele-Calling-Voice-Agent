import os
import tempfile
import sounddevice as sd
from scipy.io.wavfile import write
from deepgram import DeepgramClient, PrerecordedOptions

# ============================================================
#  API KEYS — paste your keys here
#  Deepgram (free): https://console.deepgram.com
#  ElevenLabs (optional, natural voice): https://elevenlabs.io
# ============================================================
DEEPGRAM_API_KEY  = os.getenv("DEEPGRAM_API_KEY",  "PASTE YOUR DEEPGRAM KEY HERE
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
# ============================================================

# ── TTS setup ─────────────────────────────────────────────────────────────────
USE_ELEVENLABS = bool(ELEVENLABS_API_KEY)

if USE_ELEVENLABS:
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import play as el_play
        _eleven = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        print("🔊 Voice engine : ElevenLabs (natural)")
    except Exception:
        USE_ELEVENLABS = False

if not USE_ELEVENLABS:
    import pyttsx3
    _engine = pyttsx3.init()
    _engine.setProperty("rate", 155)
    _engine.setProperty("volume", 1.0)
    # Try to use a female voice (Zira on Windows)
    for v in _engine.getProperty("voices"):
        if "zira" in v.name.lower() or "female" in v.name.lower():
            _engine.setProperty("voice", v.id)
            break
    print("🔊 Voice engine : pyttsx3 (offline)")


def speak(text: str) -> None:
    """Speak text out loud."""
    if not text.strip():
        return
    if USE_ELEVENLABS:
        try:
            audio = _eleven.text_to_speech.convert(
                voice_id="Rachel",
                text=text,
                model_id="eleven_turbo_v2",
            )
            el_play(audio)
            return
        except Exception as e:
            print(f"⚠️  ElevenLabs error: {e}")
    # pyttsx3 fallback
    _engine.say(text)
    _engine.runAndWait()


# ── STT ───────────────────────────────────────────────────────────────────────
_deepgram = DeepgramClient(DEEPGRAM_API_KEY)


def record_audio(duration: int = 6) -> str:
    """Record mic for `duration` seconds, return temp .wav path."""
    sr = 16000
    rec = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype="int16")
    sd.wait()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    write(tmp.name, sr, rec)
    return tmp.name


def speech_to_text(audio_path: str) -> str:
    """Transcribe audio to text via Deepgram."""
    try:
        with open(audio_path, "rb") as f:
            data = f.read()
        options = PrerecordedOptions(
            model="nova-2", language="en-IN",
            smart_format=True, punctuate=True,
        )
        r = _deepgram.listen.rest.v("1").transcribe_file({"buffer": data}, options)
        return r.results.channels[0].alternatives[0].transcript.strip()
    except Exception as e:
        print(f"⚠️  STT error: {e}")
        return ""