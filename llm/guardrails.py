# llm/guardrails.py

CRISIS_KEYWORDS = [
    "suicide",
    "kill myself",
    "end my life",
    "want to die",
    "no reason to live",
    "self harm",
    "hurt myself"
]

def detect_crisis(text: str) -> bool:
    """
    Detects high-risk mental health messages.
    """
    text = text.lower()

    for word in CRISIS_KEYWORDS:
        if word in text:
            return True

    return False


def safe_response():
    """
    Response used when crisis is detected.
    """
    return (
        "I'm really sorry that you're feeling this way. "
        "You are not alone, and support is available. "
        "Please consider reaching out to a trusted person or a mental health "
        "professional. If you are in immediate danger, contact your local "
        "emergency or suicide prevention helpline right now."
    )
