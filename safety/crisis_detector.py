CRISIS_WORDS = [
    "suicide",
    "kill myself",
    "end my life",
    "don't want to live"
]

def is_crisis(text):
    text = text.lower()
    return any(word in text for word in CRISIS_WORDS)
