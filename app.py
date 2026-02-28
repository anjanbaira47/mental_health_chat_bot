from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import whisper
import shutil
import os
import base64
import numpy as np
import scipy.io.wavfile as wavfile

from llm.guardrails import detect_crisis, safe_response
from prompt import generate_response
from voice.text_to_speech import speak_text
from database import create_user, verify_user, save_session, get_user_sessions
from mood_analyzer import analyze_mood
from report_generator import generate_report

app = FastAPI()

# -----------------------------
# Load Whisper model (once)
# -----------------------------
model = whisper.load_model("tiny")


# -----------------------------
# Request/Response models
# -----------------------------
class ChatRequest(BaseModel):
    message: str
    audio: bool = False
    user_id: int = None  # optional, for session tracking

class AuthRequest(BaseModel):
    username: str
    password: str

class SessionsRequest(BaseModel):
    user_id: int


# -----------------------------
# Health check route
# -----------------------------
@app.get("/")
def home():
    return {"message": "Mental Health Bot Running ✅"}


# =====================================================
# AUTH ENDPOINTS
# =====================================================
@app.post("/register")
def register(req: AuthRequest):
    return create_user(req.username, req.password)


@app.post("/login")
def login(req: AuthRequest):
    return verify_user(req.username, req.password)


# =====================================================
# TEXT CHAT ENDPOINT
# =====================================================
@app.post("/chat")
def chat(request: ChatRequest):
    user_text = request.message

    # Safety guardrails
    if detect_crisis(user_text):
        reply = safe_response()
    else:
        reply = generate_response(user_text)

    # Analyze mood
    mood = analyze_mood(user_text)

    out = {
        "user_message": user_text,
        "response": reply,
        "stress_score": mood["stress_score"],
        "anxiety_score": mood["anxiety_score"],
        "mood_label": mood["mood_label"],
    }

    # Save session if user is logged in
    if request.user_id:
        save_session(
            user_id=request.user_id,
            user_message=user_text,
            bot_reply=reply,
            stress_score=mood["stress_score"],
            anxiety_score=mood["anxiety_score"],
            mood_label=mood["mood_label"],
        )

    # Optionally generate audio
    if request.audio:
        audio_b64 = speak_text(reply)
        out["audio_base64"] = audio_b64

    return out


# =====================================================
# AUDIO CONVERSATION ENDPOINT
# =====================================================
@app.post("/conversation")
async def conversation(file: UploadFile = File(...), user_id: int = None):
    temp_audio = "temp_audio.wav"
    try:
        with open(temp_audio, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            samplerate, audio_data = wavfile.read(temp_audio)
            if audio_data.dtype == np.int16:
                audio_float = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.int32:
                audio_float = audio_data.astype(np.float32) / 2147483648.0
            else:
                audio_float = audio_data.astype(np.float32)
            if len(audio_float.shape) > 1:
                audio_float = audio_float.mean(axis=1)
        except Exception:
            try:
                import librosa
                audio_float, samplerate = librosa.load(temp_audio, sr=None)
            except Exception as e2:
                raise ValueError(f"Could not load audio file: {str(e2)}")

        if samplerate != 16000:
            try:
                import librosa
                audio_float = librosa.resample(audio_float, orig_sr=samplerate, target_sr=16000)
            except:
                factor = samplerate // 16000
                if factor > 0:
                    audio_float = audio_float[::factor]

        result = model.transcribe(audio=audio_float)
        user_text = result["text"].strip()

        if detect_crisis(user_text):
            reply = safe_response()
        else:
            reply = generate_response(user_text)

        # Analyze mood
        mood = analyze_mood(user_text)

        # Save session if user is logged in
        if user_id:
            save_session(
                user_id=user_id,
                user_message=user_text,
                bot_reply=reply,
                stress_score=mood["stress_score"],
                anxiety_score=mood["anxiety_score"],
                mood_label=mood["mood_label"],
            )

        audio_b64 = speak_text(reply)

        return {
            "transcription": user_text,
            "bot_reply": reply,
            "audio_base64": audio_b64,
            "stress_score": mood["stress_score"],
            "anxiety_score": mood["anxiety_score"],
            "mood_label": mood["mood_label"],
        }
    except Exception as e:
        print(f"Error in /conversation: {e}")
        import traceback
        traceback.print_exc()
        return {
            "transcription": "",
            "bot_reply": f"Sorry, there was an error processing your audio: {str(e)}",
            "audio_base64": None,
        }
    finally:
        if os.path.exists(temp_audio):
            try:
                os.remove(temp_audio)
            except:
                pass


# =====================================================
# TRACKER ENDPOINTS
# =====================================================
@app.post("/sessions")
def sessions(req: SessionsRequest):
    data = get_user_sessions(req.user_id)
    return {"sessions": data}


@app.post("/report")
def report(req: SessionsRequest):
    from database import get_connection
    conn = get_connection()
    row = conn.execute("SELECT username FROM users WHERE id = ?", (req.user_id,)).fetchone()
    conn.close()
    username = row["username"] if row else "User"

    session_data = get_user_sessions(req.user_id)
    pdf_bytes = generate_report(username, session_data)
    encoded = base64.b64encode(pdf_bytes).decode("utf-8")
    return {"pdf_base64": encoded}
