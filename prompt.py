from groq import Groq
import os
import random

client = None

# Conversation history for context-aware responses
conversation_history = []

SYSTEM_PROMPT = """
You are a compassionate Mental Health First-Aid assistant called MindCare.

Rules:
- Be warm, empathetic, and genuinely supportive
- NEVER repeat the same response. Always vary your language, examples, and approach
- Ask thoughtful follow-up questions to understand the user better
- Use different coping strategies each time (breathing, grounding, journaling, etc.)
- Mirror the user's emotional tone — don't be overly cheerful if they're sad
- Never diagnose mental illness or prescribe medication
- Encourage professional help when appropriate
- If user shows crisis signals, respond calmly and provide crisis resources
- Keep responses concise (2-4 sentences) unless the user needs more detail
- Use a conversational, natural tone — not robotic or formulaic
- Reference what the user said previously to show you're truly listening
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
        model="groq/compound-mini",
        messages=messages,
        temperature=0.9,
        top_p=0.95,
    )

    reply = response.choices[0].message.content

    # Add assistant reply to history
    conversation_history.append({"role": "assistant", "content": reply})

    return reply
