import base64
import io
import asyncio
import threading
import edge_tts


def _run_in_thread(text, voice, rate):
    """Run async TTS in a separate thread with its own event loop."""
    result = {"data": None}

    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result["data"] = loop.run_until_complete(_generate(text, voice, rate))
        finally:
            loop.close()

    t = threading.Thread(target=_run)
    t.start()
    t.join(timeout=30)
    return result["data"]


async def _generate(text, voice, rate):
    """Generate speech using Microsoft Edge TTS."""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    buf.seek(0)
    return buf.read()


def speak_text(text):
    """Generate speech and return base64 encoded mp3 string."""
    if not text:
        return None

    try:
        voice = "en-IN-NeerjaNeural"
        rate = "+10%"
        audio_bytes = _run_in_thread(text, voice, rate)
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode("utf-8")
        return None
    except Exception as e:
        print(f"Error generating speech: {e}")
        return None
