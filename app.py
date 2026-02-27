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

app = FastAPI()

# -----------------------------
# Load Whisper model (once)
# -----------------------------
model = whisper.load_model("tiny")


# -----------------------------
# Request model for text chat
# -----------------------------
class ChatRequest(BaseModel):
    message: str
    audio: bool = False  # if true, caller would like an audio reply


# -----------------------------
# Health check route
# -----------------------------
@app.get("/")
def home():
    return {"message": "Mental Health Bot Running ✅"}


# =====================================================
# 1️⃣ TEXT CHAT ENDPOINT (Used by Streamlit)
# =====================================================
@app.post("/chat")
def chat(request: ChatRequest):

    user_text = request.message

    # Safety guardrails
    if detect_crisis(user_text):
        reply = safe_response()
    else:
        reply = generate_response(user_text)

    out = {
        "user_message": user_text,
        "response": reply
    }

    # optionally generate audio of the assistant reply
    if request.audio:
        audio_b64 = speak_text(reply)
        out["audio_base64"] = audio_b64

    return out


# =====================================================
# 2️⃣ AUDIO CONVERSATION ENDPOINT (Whisper)
# =====================================================
@app.post("/conversation")
async def conversation(file: UploadFile = File(...)):
    temp_audio = "temp_audio.wav"
    try:
        # Save uploaded audio temporarily
        with open(temp_audio, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Load audio using scipy instead of ffmpeg
        try:
            # Try reading as WAV first
            samplerate, audio_data = wavfile.read(temp_audio)
            # Convert to float and normalize
            if audio_data.dtype == np.int16:
                audio_float = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.int32:
                audio_float = audio_data.astype(np.float32) / 2147483648.0
            else:
                audio_float = audio_data.astype(np.float32)
            
            # For stereo, take mono average
            if len(audio_float.shape) > 1:
                audio_float = audio_float.mean(axis=1)
        except Exception as e:
            # If scipy fails, try with librosa
            try:
                import librosa
                audio_float, samplerate = librosa.load(temp_audio, sr=None)
            except Exception as e2:
                raise ValueError(f"Could not load audio file: {str(e2)}")

        # Whisper expects 16kHz mono, so convert if needed
        if samplerate != 16000:
            try:
                import librosa
                audio_float = librosa.resample(audio_float, orig_sr=samplerate, target_sr=16000)
            except:
                # Simple downsampling fallback
                factor = samplerate // 16000
                if factor > 0:
                    audio_float = audio_float[::factor]

        # Transcribe
        result = model.transcribe(audio=audio_float)
        user_text = result["text"].strip()

        # Safety Layer
        if detect_crisis(user_text):
            reply = safe_response()
        else:
            reply = generate_response(user_text)

        # Build audio response
        audio_b64 = speak_text(reply)

        return {
            "transcription": user_text,
            "bot_reply": reply,
            "audio_base64": audio_b64,
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
        # Clean temp file
        if os.path.exists(temp_audio):
            try:
                os.remove(temp_audio)
            except:
                pass
