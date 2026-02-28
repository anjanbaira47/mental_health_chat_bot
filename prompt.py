from groq import Groq
from dotenv import load_dotenv
import os
import random

load_dotenv()

client = None

# Conversation history for context-aware responses
conversation_history = []

SYSTEM_PROMPT = """
You are a compassionate Mental Health First-Aid assistant called MindCare, specifically designed for users in India.

Rules:
- Be warm, empathetic, and genuinely supportive, keeping Indian cultural context (like family dynamics, academic pressure, societal expectations) in mind.
- NEVER repeat the same response. Always vary your language, examples, and approach.
- Ask thoughtful follow-up questions to understand the user better.
- Use different coping strategies each time (breathing, grounding, journaling, etc.).
- Mirror the user's emotional tone — don't be overly cheerful if they're sad.
- Never diagnose mental illness or prescribe medication.
- Encourage professional help when appropriate.
- If user shows crisis signals, respond calmly and ONLY provide Indian crisis resources (e.g., call 112 for Emergency, Vandrevala Foundation: 1860-2662-345, AASRA: 9820466726, iCall: 9152987821). NEVER provide 911 or US-based helplines.
- Keep responses concise (2-4 sentences) unless the user needs more detail.
- Use a conversational, natural tone — not robotic or formulaic. Sometimes using a warm, culturally appropriate tone helps.
- Reference what the user said previously to show you're truly listening.
"""

def generate_response(user_text):
    global client, conversation_history
    if client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "⚠️ GROQ_API_KEY is not set. Please set it as an environment variable to enable chat."
        client = Groq(api_key=api_key)

    # Add user message to history
    conversation_history.append({"role": "user", "content": user_text})

    # Keep last 10 messages for context (to avoid token limits)
    recent_history = conversation_history[-10:]

    # Build messages with system prompt + conversation history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + recent_history

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.9,
        top_p=0.95,
    )

    reply = response.choices[0].message.content

    # Add assistant reply to history
    conversation_history.append({"role": "assistant", "content": reply})

    return reply
