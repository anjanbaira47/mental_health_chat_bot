import base64
import io
import asyncio
import edge_tts


async def _generate_speech(text):
    """Generate speech using Microsoft Edge TTS (natural voice)."""
    # Use an Indian English female voice - natural sounding
    voice = "en-IN-NeerjaNeural"
    communicate = edge_tts.Communicate(text, voice, rate="+10%")
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    buf.seek(0)
    return buf.read()


def speak_text(text):
    """Generate speech for the given text and return a base64 encoded mp3 string."""
    if not text:
        return None

    try:
        audio_bytes = asyncio.run(_generate_speech(text))
        if audio_bytes:
            encoded = base64.b64encode(audio_bytes).decode("utf-8")
            return encoded
        return None
    except Exception as e:
        print(f"Error generating speech: {e}")
        return None
