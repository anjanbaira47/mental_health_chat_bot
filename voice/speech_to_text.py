import whisper

model = whisper.load_model("base")

async def transcribe_audio(audio):
    """Save incoming upload to a temp file and return the transcription text."""
    file_location = "temp.wav"

    with open(file_location, "wb") as f:
        f.write(await audio.read())

    result = model.transcribe(file_location)
    return result["text"]


def transcribe_file(path: str):
    """Helper allowing callers to transcribe an existing file path."""
    result = model.transcribe(path)
    return result["text"]

