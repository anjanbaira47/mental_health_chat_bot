import os
import json
import logging
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

client = None

ANALYSIS_PROMPT = """You are a mental health analysis assistant. Analyze the following user message and return a JSON object with exactly these fields:
- "stress_score": integer from 1 (no stress) to 10 (extreme stress)
- "anxiety_score": integer from 1 (no anxiety) to 10 (extreme anxiety)
- "mood_label": one of "calm", "neutral", "worried", "anxious", "stressed", "overwhelmed", "sad", "angry"

Only return the raw JSON object, no other text or markdown.

User message: "{message}"
"""


def analyze_mood(user_message: str) -> dict:
    """Analyze a user message for stress and anxiety levels using Groq LLM."""
    global client

    default = {"stress_score": 3, "anxiety_score": 3, "mood_label": "neutral"}

    if not user_message or len(user_message.strip()) < 3:
        return default

    if client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return default
        client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": ANALYSIS_PROMPT.format(message=user_message)}
            ],
            temperature=0.3,
        )
        raw = response.choices[0].message.content.strip()

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'\{[^}]+\}', raw)
        if json_match:
            result = json.loads(json_match.group())
            # Validate and clamp scores
            stress = max(1, min(10, int(result.get("stress_score", 3))))
            anxiety = max(1, min(10, int(result.get("anxiety_score", 3))))
            mood = result.get("mood_label", "neutral")
            valid_moods = ["calm", "neutral", "worried", "anxious", "stressed", "overwhelmed", "sad", "angry"]
            if mood not in valid_moods:
                mood = "neutral"
            return {"stress_score": stress, "anxiety_score": anxiety, "mood_label": mood}

        return default
    except Exception as e:
        print(f"Mood analysis error: {e}")
        return default
