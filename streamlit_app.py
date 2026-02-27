import streamlit as st
import requests
import base64
import numpy as np
import io
import os
import soundfile as sf
from streamlit_webrtc import webrtc_streamer, WebRtcMode

# Backend API URLs
API_URL = "http://127.0.0.1:8000/chat"
CONV_URL = "http://127.0.0.1:8000/conversation"

st.set_page_config(page_title="AI Mental Health Assistant", page_icon="🕊️", layout="wide")

# ─── GLOBAL CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
.stApp {
    background: linear-gradient(135deg, #e0f7f0 0%, #e8ecf8 40%, #f5eef8 70%, #fce4ec 100%);
    font-family: 'Inter', sans-serif;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    color: #e0e0e0;
}
[data-testid="stSidebar"] * { color: #e0e0e0 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stButton button {
    color: #e0e0e0 !important;
}
[data-testid="stSidebar"] .stButton button {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white !important;
    border: none;
    border-radius: 12px;
    padding: 8px 20px;
    font-weight: 600;
    transition: all 0.3s ease;
}
[data-testid="stSidebar"] .stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

/* ── Hero section ── */
.hero-container {
    text-align: center;
    padding: 20px 0 10px;
    animation: fadeInUp 0.8s ease-out;
}
.hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
    animation: fadeInUp 1s ease-out;
}
.hero-subtitle {
    font-size: 1.15rem;
    color: #6b7280;
    max-width: 600px;
    margin: 0 auto 24px;
    line-height: 1.6;
    animation: fadeInUp 1.2s ease-out;
}

/* ── Glass cards ── */
.glass-card {
    background: rgba(255,255,255,0.75);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.5);
    border-radius: 20px;
    padding: 28px;
    box-shadow: 0 8px 32px rgba(31,38,135,0.08);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    animation: fadeInUp 0.6s ease-out;
}
.glass-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(31,38,135,0.12);
}

/* ── Feature cards on welcome page ── */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-top: 28px;
}
.feature-card {
    background: rgba(255,255,255,0.8);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.6);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    animation: fadeInUp 0.8s ease-out;
}
.feature-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 12px 36px rgba(102,126,234,0.15);
}
.feature-icon { font-size: 2.4rem; margin-bottom: 12px; }
.feature-title { font-weight: 600; font-size: 1.05rem; color: #1a1a2e; margin-bottom: 6px; }
.feature-desc  { font-size: 0.88rem; color: #6b7280; line-height: 1.5; }

/* ── Chat messages ── */
.chat-container {
    max-height: 440px;
    overflow-y: auto;
    padding: 16px;
    border-radius: 16px;
    background: rgba(255,255,255,0.45);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.4);
}
.msg-row { display: flex; margin-bottom: 14px; animation: msgSlideIn 0.4s ease-out; }
.msg-row.user   { justify-content: flex-end; }
.msg-row.bot    { justify-content: flex-start; }
.msg-avatar {
    width: 38px; height: 38px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem;
    flex-shrink: 0;
}
.msg-avatar.user-av { background: linear-gradient(135deg,#667eea,#764ba2); margin-left: 10px; order: 2; }
.msg-avatar.bot-av  { background: linear-gradient(135deg,#43e97b,#38f9d7); margin-right: 10px; }
.msg-bubble {
    max-width: 70%;
    padding: 14px 18px;
    border-radius: 18px;
    font-size: 0.95rem;
    line-height: 1.55;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.msg-bubble.user-bub {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border-bottom-right-radius: 4px;
}
.msg-bubble.bot-bub {
    background: rgba(255,255,255,0.9);
    color: #1a1a2e;
    border: 1px solid rgba(200,200,230,0.3);
    border-bottom-left-radius: 4px;
}

/* ── Thinking / loading animation ── */
.thinking-container {
    display: flex; align-items: center; gap: 10px;
    padding: 14px 18px;
    background: rgba(255,255,255,0.85);
    border-radius: 18px;
    border-bottom-left-radius: 4px;
    max-width: 140px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    animation: fadeIn 0.3s ease-out;
}
.dot-pulse { display: flex; gap: 5px; }
.dot-pulse span {
    width: 8px; height: 8px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 50%;
    animation: dotBounce 1.4s ease-in-out infinite;
}
.dot-pulse span:nth-child(2) { animation-delay: 0.2s; }
.dot-pulse span:nth-child(3) { animation-delay: 0.4s; }

/* ── Audio waveform animation ── */
.audio-wave-container {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 20px;
    background: linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1));
    border-radius: 14px;
    margin-top: 8px;
    border: 1px solid rgba(102,126,234,0.15);
    animation: fadeIn 0.5s ease-out;
}
.wave-icon {
    font-size: 1.4rem;
    animation: pulse 1.5s ease-in-out infinite;
}
.wave-bars { display: flex; align-items: center; gap: 3px; height: 28px; }
.wave-bars .bar {
    width: 3px;
    background: linear-gradient(180deg, #667eea, #764ba2);
    border-radius: 3px;
    animation: waveBar 1.2s ease-in-out infinite;
}
.wave-bars .bar:nth-child(1) { height: 40%; animation-delay: 0.0s; }
.wave-bars .bar:nth-child(2) { height: 70%; animation-delay: 0.1s; }
.wave-bars .bar:nth-child(3) { height: 100%; animation-delay: 0.2s; }
.wave-bars .bar:nth-child(4) { height: 60%; animation-delay: 0.3s; }
.wave-bars .bar:nth-child(5) { height: 85%; animation-delay: 0.4s; }
.wave-bars .bar:nth-child(6) { height: 45%; animation-delay: 0.5s; }
.wave-bars .bar:nth-child(7) { height: 75%; animation-delay: 0.6s; }
.wave-bars .bar:nth-child(8) { height: 55%; animation-delay: 0.7s; }
.wave-label { font-size: 0.85rem; color: #667eea; font-weight: 500; }

/* ── Voice / mic button ── */
.voice-btn {
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border: none;
    border-radius: 50px;
    padding: 12px 28px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 16px rgba(102,126,234,0.3);
}
.voice-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(102,126,234,0.4);
}
.mic-icon { font-size: 1.3rem; }

/* ── Resource cards ── */
.resource-card {
    background: rgba(255,255,255,0.8);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 24px;
    border-left: 4px solid;
    margin-bottom: 16px;
    transition: transform 0.3s ease;
    animation: fadeInUp 0.6s ease-out;
}
.resource-card:hover { transform: translateX(6px); }
.resource-card.emergency  { border-color: #ef4444; }
.resource-card.helpline   { border-color: #667eea; }
.resource-card.selfcare    { border-color: #43e97b; }

/* ── Animations ── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}
@keyframes msgSlideIn {
    from { opacity: 0; transform: translateX(-10px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes dotBounce {
    0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
    40%           { transform: scale(1); opacity: 1; }
}
@keyframes waveBar {
    0%, 100% { transform: scaleY(0.5); }
    50%      { transform: scaleY(1); }
}
@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50%      { transform: scale(1.15); }
}
@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50%      { transform: translateY(-8px); }
}

/* ── Misc polish ── */
.stTextInput input {
    border-radius: 14px !important;
    border: 2px solid rgba(102,126,234,0.2) !important;
    padding: 12px 16px !important;
    font-size: 0.95rem !important;
    transition: border-color 0.3s ease !important;
}
.stTextInput input:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102,126,234,0.1) !important;
}
.section-title {
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ───────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Get Started"

with st.sidebar:
    st.markdown("### 🕊️ MindCare AI")
    st.markdown("<small style='color:#9ca3af'>Your safe space to talk</small>", unsafe_allow_html=True)
    st.markdown("---")
    pages = ["Get Started", "Chat", "Resources"]
    current_index = pages.index(st.session_state.page) if st.session_state.page in pages else 0
    choice = st.selectbox("Navigate", pages, index=current_index, label_visibility="collapsed")
    st.session_state.page = choice
    st.markdown("---")
    if st.button("🗑️  Clear Conversation"):
        st.session_state.messages = []
        st.session_state.last_response = None
    st.markdown("---")
    st.markdown("<small style='color:#6b7280'>A calm, supportive assistant.<br>Not a substitute for professional help.</small>", unsafe_allow_html=True)

# Initialize state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "is_thinking" not in st.session_state:
    st.session_state.is_thinking = False


# ═══════════════════════════════════════════════════════════════════════
#  WELCOME PAGE
# ═══════════════════════════════════════════════════════════════════════
def render_get_started():
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">Welcome — You're Seen Here</div>
        <div class="hero-subtitle">
            A safe, non-judgmental space to share how you're feeling.
            Our AI companion listens, supports, and guides you — anytime you need it.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Mental health information section
    st.markdown("""
    <div class="glass-card" style="margin-bottom:20px;">
        <div style="font-size:1.3rem; font-weight:700; color:#1a1a2e; margin-bottom:12px;">🧠 Why Mental Health Matters</div>
        <div style="color:#374151; line-height:1.8; font-size:0.95rem;">
            Mental health is just as important as physical health. <strong>1 in 5 people</strong> experience a mental health condition each year,
            yet many suffer in silence. Talking about your feelings is not a sign of weakness — it's a sign of strength.
            Early support can make a real difference in managing stress, anxiety, and emotional challenges.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        <div class="glass-card" style="height:100%;">
            <div style="font-size:1.1rem; font-weight:700; color:#1a1a2e; margin-bottom:10px;">⚠️ Common Signs to Watch For</div>
            <div style="color:#374151; line-height:1.8; font-size:0.9rem;">
                😔 Persistent sadness or low mood<br>
                😰 Excessive worry or fear<br>
                😴 Changes in sleep or appetite<br>
                🚫 Withdrawal from friends & activities<br>
                💭 Difficulty concentrating<br>
                😤 Unusual irritability or anger
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown("""
        <div class="glass-card" style="height:100%;">
            <div style="font-size:1.1rem; font-weight:700; color:#1a1a2e; margin-bottom:10px;">🌱 Daily Wellness Tips</div>
            <div style="color:#374151; line-height:1.8; font-size:0.9rem;">
                🧘 Practice 5 minutes of mindfulness daily<br>
                🏃 Move your body — even a short walk helps<br>
                📓 Journal your thoughts before bed<br>
                🤝 Stay connected with people you trust<br>
                💤 Prioritize 7–8 hours of sleep<br>
                🎵 Listen to music that lifts your mood
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Feature cards
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon" style="animation: float 3s ease-in-out infinite;">💬</div>
            <div class="feature-title">Text Chat</div>
            <div class="feature-desc">Type how you're feeling and receive empathetic, thoughtful responses.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon" style="animation: float 3s ease-in-out infinite 0.3s;">🎙️</div>
            <div class="feature-title">Voice Input</div>
            <div class="feature-desc">Record your thoughts — we'll listen and respond with voice too.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon" style="animation: float 3s ease-in-out infinite 0.6s;">🛡️</div>
            <div class="feature-title">Safe & Private</div>
            <div class="feature-desc">Crisis detection built-in. We'll always point you to real help when needed.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Big start button
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🗣️  Start Conversation", use_container_width=True, key="start_conv"):
            st.session_state.page = "Chat"
            st.session_state.input_mode = "💬 Text"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick-start prompts
    col1, col2 = st.columns(2)
    with col1:
        if st.button("😟  I'm feeling anxious", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "I'm feeling anxious about work and can't sleep."})
            st.session_state.page = "Chat"
            st.rerun()
    with col2:
        if st.button("🤗  I need someone to talk to", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "I need someone to talk to. I'm feeling overwhelmed."})
            st.session_state.page = "Chat"
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════
#  CHAT PAGE
# ═══════════════════════════════════════════════════════════════════════
def render_chat_messages():
    """Render chat history with styled bubbles."""
    msgs_html = ""
    messages = st.session_state.messages
    has_audio = bool(st.session_state.get("last_response"))

    for i, msg in enumerate(messages):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        is_last_bot = (role == "assistant" and i == len(messages) - 1)

        if role == "user":
            msgs_html += f"""
            <div class="msg-row user">
                <div class="msg-bubble user-bub">{content}</div>
                <div class="msg-avatar user-av">👤</div>
            </div>"""
        else:
            # Last bot message gets typewriter effect
            typewriter_class = ' typewriter-text' if is_last_bot else ''
            msgs_html += f"""
            <div class="msg-row bot">
                <div class="msg-avatar bot-av">🕊️</div>
                <div class="msg-bubble bot-bub{typewriter_class}">{content}</div>
            </div>"""

    # Show thinking animation if waiting
    if st.session_state.get("is_thinking"):
        msgs_html += """
        <div class="msg-row bot">
            <div class="msg-avatar bot-av">🕊️</div>
            <div class="thinking-container">
                <div class="dot-pulse">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>"""

    return msgs_html


def render_chat():
    st.markdown('<div class="section-title">💬 Chat — I\'m here to listen</div>', unsafe_allow_html=True)

    left, right = st.columns([2.5, 1])

    with left:
        # Chat messages
        msgs_html = render_chat_messages()
        if msgs_html:
            st.markdown(f'<div class="chat-container">{msgs_html}</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="chat-container" style="text-align:center; padding:60px 20px;">
                <div style="font-size:3rem; margin-bottom:12px; animation: float 3s ease-in-out infinite;">🕊️</div>
                <div style="color:#6b7280; font-size:1rem;">
                    Start a conversation below.<br>I'm here whenever you're ready.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Audio waveform + player if audio response
        if st.session_state.get("last_response"):
            st.markdown("""
            <div class="audio-wave-container" id="wave-container">
                <div class="wave-icon" id="wave-icon">🔊</div>
                <div class="wave-bars" id="wave-bars">
                    <div class="bar"></div><div class="bar"></div><div class="bar"></div>
                    <div class="bar"></div><div class="bar"></div><div class="bar"></div>
                    <div class="bar"></div><div class="bar"></div>
                </div>
                <div class="wave-label" id="wave-label">Press play to listen</div>
            </div>
            <style>
                .wave-bars.paused .bar { animation: none !important; height: 4px !important; }
                .wave-icon.paused { animation: none !important; }
            </style>
            <script>
                // Typewriter effect for last bot message
                const twEl = document.querySelector('.typewriter-text');
                if (twEl) {
                    const fullText = twEl.textContent;
                    const words = fullText.split(' ');
                    twEl.textContent = '';
                    twEl.style.visibility = 'visible';
                    let wordIndex = 0;
                    let twInterval = null;

                    function startTypewriter(durationMs) {
                        const delay = Math.max(durationMs / words.length, 60);
                        twInterval = setInterval(() => {
                            if (wordIndex < words.length) {
                                twEl.textContent += (wordIndex > 0 ? ' ' : '') + words[wordIndex];
                                wordIndex++;
                            } else {
                                clearInterval(twInterval);
                            }
                        }, delay);
                    }

                    // Start typewriter immediately with estimated timing
                    startTypewriter(words.length * 150);
                }

                // Audio play/pause/end control for waveform
                const checkAudio = setInterval(() => {
                    const audio = document.querySelector('audio');
                    if (audio) {
                        clearInterval(checkAudio);
                        const bars = document.getElementById('wave-bars');
                        const icon = document.getElementById('wave-icon');
                        const label = document.getElementById('wave-label');
                        // Auto-play
                        audio.play().then(() => {
                            if (bars) bars.classList.remove('paused');
                            if (icon) icon.classList.remove('paused');
                            if (label) label.textContent = '🗣️ Assistant is speaking…';
                        }).catch(() => {
                            if (bars) bars.classList.add('paused');
                            if (icon) icon.classList.add('paused');
                            if (label) label.textContent = 'Press play to listen';
                        });
                        audio.addEventListener('play', () => {
                            if (bars) bars.classList.remove('paused');
                            if (icon) icon.classList.remove('paused');
                            if (label) label.textContent = '🗣️ Assistant is speaking…';
                        });
                        audio.addEventListener('pause', () => {
                            if (bars) bars.classList.add('paused');
                            if (icon) icon.classList.add('paused');
                            if (label) label.textContent = 'Paused';
                        });
                        audio.addEventListener('ended', () => {
                            if (bars) bars.classList.add('paused');
                            if (icon) icon.classList.add('paused');
                            if (label) label.textContent = '✅ Finished speaking';
                        });
                    }
                }, 200);
            </script>
            """, unsafe_allow_html=True)
            try:
                audio_bytes = base64.b64decode(st.session_state.last_response)
                st.audio(audio_bytes, format="audio/mp3")
            except Exception:
                pass

    with right:
        st.markdown("""
        <div class="glass-card" style="animation-delay:0.2s;">
            <div style="font-weight:600; font-size:1.05rem; margin-bottom:12px;">
                🌿 Tips for a calming conversation
            </div>
            <div style="font-size:0.88rem; color:#6b7280; line-height:1.8;">
                🫁 Take a slow, deep breath before writing<br>
                💛 Be honest about what you're feeling<br>
                🆘 If you need immediate help, use the Resources tab<br>
                🎧 Switch to Audio mode to speak & listen
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Input area ──
    col_mode, col_spacer = st.columns([1, 3])
    with col_mode:
        input_mode = st.radio("Input mode", ["💬 Text", "🎙️ Voice"], horizontal=True, label_visibility="collapsed")

    if input_mode == "💬 Text":
        user_input = st.text_input("How are you feeling today?", placeholder="Type your message here…", label_visibility="collapsed")
        if user_input and user_input != st.session_state.get("last_input", ""):
            st.session_state.last_input = user_input
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.is_thinking = True
            # Rerun to show thinking animation, then fetch
            # We can't truly show the animation mid-request in Streamlit,
            # so we fetch inline and rerun after.
            try:
                r = requests.post(API_URL, json={"message": user_input, "audio": True}, timeout=30)
                if r.status_code == 200:
                    data = r.json()
                    bot_reply = data.get("response", "Sorry, I couldn't process that.")
                    audio_response_b64 = data.get("audio_base64")
                else:
                    bot_reply = "Server error. Please try again."
                    audio_response_b64 = None
            except Exception:
                bot_reply = "Connection error. Is the backend running?"
                audio_response_b64 = None

            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            st.session_state.last_response = audio_response_b64
            st.session_state.is_thinking = False
            st.rerun()

    else:
        # Voice mode
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
            <span class="mic-icon" style="font-size:1.6rem; animation: pulse 1.5s ease-in-out infinite;">🎙️</span>
            <span style="color:#6b7280; font-size:0.95rem;">Record or upload a voice message</span>
        </div>
        """, unsafe_allow_html=True)

        rec_method = st.radio("Recording method", ["🔴 Browser Record", "📁 File Upload"], horizontal=True, key="rec_method_choice", label_visibility="collapsed")

        if rec_method == "🔴 Browser Record":
            ctx = webrtc_streamer(
                key="recorder",
                mode=WebRtcMode.SENDONLY,
                audio_receiver_size=256,
                media_stream_constraints={"audio": True, "video": False},
            )

            # Show listening animation when WebRTC is active
            if ctx and ctx.state.playing:
                st.markdown("""
                <div class="audio-wave-container" style="border-color:rgba(239,68,68,0.3); background:linear-gradient(135deg,rgba(239,68,68,0.08),rgba(234,88,12,0.08));">
                    <div style="font-size:1.4rem; animation: pulse 1s ease-in-out infinite;">🔴</div>
                    <div class="wave-bars">
                        <div class="bar" style="background:linear-gradient(180deg,#ef4444,#ea580c);"></div>
                        <div class="bar" style="background:linear-gradient(180deg,#ef4444,#ea580c);"></div>
                        <div class="bar" style="background:linear-gradient(180deg,#ef4444,#ea580c);"></div>
                        <div class="bar" style="background:linear-gradient(180deg,#ef4444,#ea580c);"></div>
                        <div class="bar" style="background:linear-gradient(180deg,#ef4444,#ea580c);"></div>
                        <div class="bar" style="background:linear-gradient(180deg,#ef4444,#ea580c);"></div>
                    </div>
                    <div style="font-size:0.85rem; color:#ef4444; font-weight:500;">Listening… Speak now</div>
                </div>
                """, unsafe_allow_html=True)

            if st.button("📤  Send Recording", use_container_width=True):
                if ctx and ctx.audio_receiver:
                    try:
                        frames = ctx.audio_receiver.get_frames(timeout=1)
                        if frames and len(frames) > 0:
                            arr = np.concatenate([f.to_ndarray().T for f in frames])
                            samplerate = frames[0].sample_rate
                            buf = io.BytesIO()
                            sf.write(buf, arr, samplerate=samplerate, format="WAV")
                            audio_bytes = buf.getvalue()

                            with st.spinner("🎧 Converting your speech to text…"):
                                files = {"file": ("recording.wav", audio_bytes)}
                                r = requests.post(CONV_URL, files=files, timeout=30)
                            if r.status_code == 200:
                                data = r.json()
                                transcription = data.get("transcription")
                                bot_reply = data.get("bot_reply")
                                audio_response_b64 = data.get("audio_base64")
                                if transcription:
                                    st.session_state.messages.append({"role": "user", "content": transcription})
                                    st.info(f"📝 You said: *{transcription}*")
                                if bot_reply:
                                    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                                st.session_state.last_response = audio_response_b64
                                st.rerun()
                            else:
                                st.error(f"Server error: {r.status_code}")
                        else:
                            st.warning("No audio recorded. Press START, speak, then click Send.")
                    except Exception as e:
                        st.error(f"Error processing audio: {str(e)}")
                else:
                    st.warning("Recorder not initialized. Press START first, then Send.")

        else:
            audio_file = st.file_uploader("Upload a WAV, MP3, or M4A file", type=["wav", "mp3", "m4a"], key="audio_upload")
            if audio_file is not None:
                files = {"file": (audio_file.name, audio_file.getvalue())}
                with st.spinner("🎧 Converting your speech to text…"):
                    try:
                        r = requests.post(CONV_URL, files=files, timeout=30)
                        if r.status_code == 200:
                            data = r.json()
                            transcription = data.get("transcription")
                            bot_reply = data.get("bot_reply")
                            audio_response_b64 = data.get("audio_base64")
                            if transcription:
                                st.session_state.messages.append({"role": "user", "content": transcription})
                                st.info(f"📝 You said: *{transcription}*")
                            if bot_reply:
                                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                            st.session_state.last_response = audio_response_b64
                            st.rerun()
                        else:
                            st.error(f"Server error: {r.status_code}")
                    except Exception as e:
                        st.error(f"Connection error: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════
#  RESOURCES PAGE
# ═══════════════════════════════════════════════════════════════════════
def render_resources():
    st.markdown('<div class="section-title">🛡️ Resources & Support</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="resource-card emergency">
        <div style="font-weight:700; font-size:1.1rem; color:#ef4444; margin-bottom:6px;">🚨 Emergency</div>
        <div style="color:#374151; line-height:1.6;">
            If you're in immediate danger, <strong>call 112</strong> (India Emergency).<br>
            <strong>Vandrevala Foundation:</strong> 1860-2662-345 (24/7)<br>
            <strong>iCall:</strong> 9152987821 &nbsp;|&nbsp;
            <strong>AASRA:</strong> 9820466726
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="resource-card helpline">
        <div style="font-weight:700; font-size:1.1rem; color:#667eea; margin-bottom:6px;">📞 India Helplines</div>
        <div style="color:#374151; line-height:1.6;">
            <strong>NIMHANS:</strong> 080-46110007 &nbsp;|&nbsp;
            <strong>Snehi:</strong> 044-24640050<br>
            <strong>Connecting Trust:</strong> 9922001122 &nbsp;|&nbsp;
            <strong>Parivarthan:</strong> 7676602602<br><br>
            More helplines:
            <a href="https://www.thelivelovelaughfoundation.org/helpline" target="_blank" style="color:#667eea; text-decoration:underline;">
                thelivelovelaughfoundation.org
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="resource-card selfcare">
        <div style="font-weight:700; font-size:1.1rem; color:#059669; margin-bottom:6px;">🌿 Self-Care Techniques</div>
        <div style="color:#374151; line-height:1.6;">
            🫁 <strong>Box breathing</strong> — Inhale 4s → Hold 4s → Exhale 4s → Hold 4s<br>
            🌍 <strong>5-4-3-2-1 grounding</strong> — Name 5 things you see, 4 you hear, 3 you touch, 2 you smell, 1 you taste<br>
            🧘 <strong>Progressive muscle relaxation</strong> — Tense and release each muscle group<br>
            📓 <strong>Journaling</strong> — Write down three things you're grateful for today
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── PAGE ROUTING ──────────────────────────────────────────────────────
page = st.session_state.get("page", "Get Started")
if page == "Get Started":
    render_get_started()
elif page == "Chat":
    render_chat()
else:
    render_resources()
