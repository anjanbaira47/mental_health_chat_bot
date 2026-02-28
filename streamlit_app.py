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

/* Send button styling */
[data-testid="stButton"] button[kind="secondary"]:has(+ div) ,
button[data-testid="baseButton-secondary"] {
    transition: all 0.2s ease;
}
div[data-testid="stHorizontalBlock"]:last-of-type > div:last-child button {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important;
    border: none !important;
    border-radius: 50% !important;
    width: 42px !important;
    height: 42px !important;
    font-size: 1.2rem !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 42px !important;
    box-shadow: 0 4px 12px rgba(102,126,234,0.4) !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stHorizontalBlock"]:last-of-type > div:last-child button:hover {
    transform: scale(1.1) !important;
    box-shadow: 0 6px 18px rgba(102,126,234,0.6) !important;
}

/* Hide 'Press Enter to apply' text */
.stTextInput div[data-testid="InputInstructions"] {
    display: none !important;
}

/* Login form — larger elements */
[data-testid="stTabs"] button[role="tab"] {
    font-size: 1.15rem !important;
    padding: 12px 20px !important;
}
[data-testid="stTabs"] input {
    font-size: 1.1rem !important;
    padding: 14px 16px !important;
}
[data-testid="stTabs"] label {
    font-size: 1.05rem !important;
    font-weight: 500 !important;
}
[data-testid="stTabs"] button[kind="secondary"],
[data-testid="stTabs"] button[data-testid="baseButton-secondary"] {
    font-size: 1.1rem !important;
    padding: 12px 20px !important;
}
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ───────────────────────────────────────────────────────────
# Auth URLs
AUTH_REGISTER_URL = "http://127.0.0.1:8000/register"
AUTH_LOGIN_URL = "http://127.0.0.1:8000/login"
SESSIONS_URL = "http://127.0.0.1:8000/sessions"
REPORT_URL = "http://127.0.0.1:8000/report"

# Initialize state + restore session from file
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "is_thinking" not in st.session_state:
    st.session_state.is_thinking = False

import json as _json
_SESSION_FILE = os.path.join(os.path.dirname(__file__), ".session.json")

def _save_session():
    """Save login session to file for refresh persistence."""
    try:
        with open(_SESSION_FILE, "w") as f:
            _json.dump({"uid": st.session_state.user_id, "user": st.session_state.username, "pg": st.session_state.page}, f)
    except: pass

def _clear_session():
    """Clear saved session file."""
    try:
        if os.path.exists(_SESSION_FILE):
            os.remove(_SESSION_FILE)
    except: pass

# Restore session from file (survives refresh)
if "logged_in" not in st.session_state:
    try:
        with open(_SESSION_FILE, "r") as f:
            saved = _json.load(f)
        if saved.get("uid") and saved.get("user"):
            st.session_state.logged_in = True
            st.session_state.user_id = int(saved["uid"])
            st.session_state.username = saved["user"]
            st.session_state.page = saved.get("pg", "Get Started")
        else:
            raise ValueError
    except:
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = ""
        st.session_state.page = "Login"
else:
    if "page" not in st.session_state:
        st.session_state.page = "Login"

with st.sidebar:
    st.markdown("### 🕊️ MindCare AI")
    st.markdown("<small style='color:#9ca3af'>Your safe space to talk</small>", unsafe_allow_html=True)
    st.markdown("---")

    if st.session_state.logged_in:
        st.markdown(f"<div style='color:#43e97b;font-weight:600;margin-bottom:8px;'>👤 {st.session_state.username}</div>", unsafe_allow_html=True)
        st.markdown("---")

        # Navigation tabs as buttons
        nav_items = [
            ("", "Get Started", "Home"),
            ("", "Chat", "Chat"),
            ("", "Tracker", "Tracker"),
            ("", "Resources", "Resources"),
        ]
        for icon, page_name, label in nav_items:
            is_active = st.session_state.page == page_name
            if is_active:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:10px 16px;
                    border-radius:10px;margin-bottom:6px;font-weight:600;font-size:0.95rem;">
                    {icon} {label}
                </div>""", unsafe_allow_html=True)
            else:
                if st.button(f"{icon}  {label}", key=f"nav_{page_name}", use_container_width=True):
                    st.session_state.page = page_name
                    _save_session()
                    st.rerun()

        st.markdown("---")
        if st.button("Clear Chat", use_container_width=True, key="clear_chat"):
            st.session_state.messages = []
            st.session_state.last_response = None
            st.session_state.is_thinking = False
            st.rerun()
        if st.button("Logout", use_container_width=True, key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = ""
            st.session_state.messages = []
            st.session_state.last_response = None
            st.session_state.page = "Login"
            _clear_session()
            st.rerun()
    else:
        st.markdown("<div style='color:#9ca3af;'>Please log in to continue</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<small style='color:#6b7280'>A calm, supportive assistant.<br>Not a substitute for professional help.</small>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
#  WELCOME PAGE
# ═══════════════════════════════════════════════════════════════════════
def render_get_started():
    st.markdown(f"""
    <div style="text-align:center; padding:60px 20px 30px;">
        <div style="font-size:3.5rem; margin-bottom:12px;">🕊️</div>
        <div class="hero-title" style="font-size:2.2rem; margin-bottom:10px;">
            Welcome, {st.session_state.username}
        </div>
        <div class="hero-subtitle" style="max-width:500px; margin:0 auto 40px; font-size:1.05rem; color:#6b7280;">
            A safe, non-judgmental space to share how you're feeling.
            Talk to our AI companion — anytime, anywhere.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Single prominent button
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🗣️  Start Conversation", use_container_width=True, key="start_conv"):
            st.session_state.page = "Chat"
            st.session_state.input_mode = "💬 Text"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Minimal feature summary — 3 clean icon cards
    st.markdown("""
    <div style="display:flex; justify-content:center; gap:30px; flex-wrap:wrap; padding:20px 0;">
        <div style="text-align:center; width:160px;">
            <div style="font-size:2rem; margin-bottom:8px;">💬</div>
            <div style="font-weight:600; color:#1a1a2e; font-size:0.95rem;">Text Chat</div>
            <div style="color:#9ca3af; font-size:0.8rem; margin-top:4px;">Type how you feel</div>
        </div>
        <div style="text-align:center; width:160px;">
            <div style="font-size:2rem; margin-bottom:8px;">🎙️</div>
            <div style="font-weight:600; color:#1a1a2e; font-size:0.95rem;">Voice Input</div>
            <div style="color:#9ca3af; font-size:0.8rem; margin-top:4px;">Speak your thoughts</div>
        </div>
        <div style="text-align:center; width:160px;">
            <div style="font-size:2rem; margin-bottom:8px;">📊</div>
            <div style="font-weight:600; color:#1a1a2e; font-size:0.95rem;">Wellness Tracker</div>
            <div style="color:#9ca3af; font-size:0.8rem; margin-top:4px;">Track your progress</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


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
    if st.button("← Back", key="back_chat"):
        st.session_state.page = "Get Started"
        st.rerun()
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
        with st.form("chat_form", clear_on_submit=True):
            input_col, btn_col = st.columns([9, 1])
            with input_col:
                user_input = st.text_input("How are you feeling today?", placeholder="Type your message here…", label_visibility="collapsed", key="chat_input")
            with btn_col:
                submitted = st.form_submit_button("⬆", use_container_width=True)
        
        if submitted and user_input and user_input.strip():
            st.session_state.messages.append({"role": "user", "content": user_input.strip()})
            st.session_state.is_thinking = True
            try:
                r = requests.post(API_URL, json={
                    "message": user_input.strip(),
                    "audio": True,
                    "user_id": st.session_state.get("user_id")
                }, timeout=30)
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
    if st.button("← Back", key="back_resources"):
        st.session_state.page = "Get Started"
        st.rerun()
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


# ═══════════════════════════════════════════════════════════════════════
#  LOGIN / SIGNUP PAGE
# ═══════════════════════════════════════════════════════════════════════
def render_login():
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">🕊️ MindCare AI</div>
        <div class="hero-subtitle">Sign in or create an account to begin your wellness journey.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

        with tab1:

            login_user = st.text_input("Username", key="login_user", placeholder="Enter your username")
            login_pass = st.text_input("Password", type="password", key="login_pass", placeholder="Enter your password")
            if st.button("🔑  Log In", use_container_width=True, key="login_btn"):
                if login_user and login_pass:
                    try:
                        r = requests.post(AUTH_LOGIN_URL, json={"username": login_user, "password": login_pass}, timeout=10)
                        data = r.json()
                        if data.get("success"):
                            st.session_state.logged_in = True
                            st.session_state.user_id = data["user_id"]
                            st.session_state.username = login_user
                            st.session_state.page = "Get Started"
                            _save_session()
                            st.rerun()
                        else:
                            st.error(data.get("message", "Login failed."))
                    except Exception:
                        st.error("Connection error. Is the backend running?")
                else:
                    st.warning("Please enter both username and password.")

        with tab2:
            reg_user = st.text_input("Choose a username", key="reg_user", placeholder="Pick a username")
            reg_pass = st.text_input("Choose a password", type="password", key="reg_pass", placeholder="Min 4 characters")
            reg_pass2 = st.text_input("Confirm password", type="password", key="reg_pass2", placeholder="Re-enter password")
            if st.button("📝  Create Account", use_container_width=True, key="reg_btn"):
                if not reg_user or not reg_pass:
                    st.warning("Please fill in all fields.")
                elif len(reg_pass) < 4:
                    st.warning("Password must be at least 4 characters.")
                elif reg_pass != reg_pass2:
                    st.error("Passwords do not match.")
                else:
                    try:
                        r = requests.post(AUTH_REGISTER_URL, json={"username": reg_user, "password": reg_pass}, timeout=10)
                        data = r.json()
                        if data.get("success"):
                            # Auto-login after signup
                            r2 = requests.post(AUTH_LOGIN_URL, json={"username": reg_user, "password": reg_pass}, timeout=10)
                            login_data = r2.json()
                            if login_data.get("success"):
                                st.session_state.logged_in = True
                                st.session_state.user_id = login_data["user_id"]
                                st.session_state.username = reg_user
                                st.session_state.page = "Get Started"
                                _save_session()
                                st.rerun()
                            else:
                                st.success("✅ Account created! Please log in.")
                        else:
                            st.error(data.get("message", "Registration failed."))
                    except Exception:
                        st.error("Connection error. Is the backend running?")



# ═══════════════════════════════════════════════════════════════════════
#  TRACKER PAGE
# ═══════════════════════════════════════════════════════════════════════
def render_tracker():
    if st.button("← Back", key="back_tracker"):
        st.session_state.page = "Get Started"
        _save_session()
        st.rerun()
    st.markdown('<div class="section-title">📊 Your Wellness Tracker</div>', unsafe_allow_html=True)

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("Please log in to view your tracker.")
        return

    # Fetch sessions from backend
    try:
        r = requests.post(SESSIONS_URL, json={"user_id": user_id}, timeout=10)
        sessions = r.json().get("sessions", [])
    except Exception:
        st.error("Could not load tracker data. Is the backend running?")
        return

    if not sessions:
        st.markdown("""
        <div class="glass-card" style="text-align:center; padding:40px;">
            <div style="font-size:3rem; margin-bottom:12px;">📊</div>
            <div style="color:#6b7280; font-size:1.1rem;">
                No sessions recorded yet.<br>Start chatting to build your wellness profile!
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Summary stats ──
    stress_scores = [s["stress_score"] for s in sessions]
    anxiety_scores = [s["anxiety_score"] for s in sessions]
    mood_labels = [s["mood_label"] for s in sessions]

    avg_stress = sum(stress_scores) / len(stress_scores)
    avg_anxiety = sum(anxiety_scores) / len(anxiety_scores)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:2rem; font-weight:700; color:#667eea;">{len(sessions)}</div>
            <div style="font-size:0.85rem; color:#6b7280;">Total Sessions</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        color = "#22c55e" if avg_stress <= 4 else "#eab308" if avg_stress <= 6 else "#ef4444"
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:2rem; font-weight:700; color:{color};">{avg_stress:.1f}</div>
            <div style="font-size:0.85rem; color:#6b7280;">Avg Stress (1-10)</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        color = "#22c55e" if avg_anxiety <= 4 else "#eab308" if avg_anxiety <= 6 else "#ef4444"
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:2rem; font-weight:700; color:{color};">{avg_anxiety:.1f}</div>
            <div style="font-size:0.85rem; color:#6b7280;">Avg Anxiety (1-10)</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        # Most common mood
        from collections import Counter
        mood_counter = Counter(mood_labels)
        top_mood = mood_counter.most_common(1)[0][0].capitalize()
        st.markdown(f"""
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:2rem; font-weight:700; color:#667eea;">{top_mood}</div>
            <div style="font-size:0.85rem; color:#6b7280;">Most Common Mood</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ──
    import pandas as pd
    df = pd.DataFrame(sessions)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("**📈 Stress Level Over Time**")
        st.line_chart(df[["stress_score"]], color="#ef4444")
    with chart_col2:
        st.markdown("**📈 Anxiety Level Over Time**")
        st.line_chart(df[["anxiety_score"]], color="#667eea")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Mood distribution ──
    st.markdown("**🎭 Mood Distribution**")
    mood_df = pd.DataFrame(list(mood_counter.items()), columns=["Mood", "Count"])
    mood_df = mood_df.sort_values("Count", ascending=False)
    st.bar_chart(mood_df.set_index("Mood"))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Recent sessions table ──
    st.markdown("**📋 Recent Sessions**")
    recent = sessions[-10:]
    table_data = []
    for s in reversed(recent):
        table_data.append({
            "Time": s["timestamp"][:16],
            "Message": s["user_message"][:60] + ("..." if len(s["user_message"]) > 60 else ""),
            "Stress": s["stress_score"],
            "Anxiety": s["anxiety_score"],
            "Mood": s["mood_label"].capitalize(),
        })
    import pandas as _pd
    df_table = _pd.DataFrame(table_data)
    df_table.index = range(len(df_table), 0, -1)  # n at top, 1 at bottom
    df_table.index.name = "#"
    st.table(df_table)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Download PDF report ──
    st.markdown("**📥 Download Wellness Report**")
    if st.button("📄  Generate PDF Report", use_container_width=True, key="pdf_btn"):
        with st.spinner("Generating your wellness report…"):
            try:
                r = requests.post(REPORT_URL, json={"user_id": user_id}, timeout=15)
                data = r.json()
                pdf_b64 = data.get("pdf_base64")
                if pdf_b64:
                    pdf_bytes = base64.b64decode(pdf_b64)
                    st.download_button(
                        label="⬇️  Download PDF",
                        data=pdf_bytes,
                        file_name=f"mindcare_report_{st.session_state.username}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.error("Could not generate report.")
            except Exception as e:
                st.error(f"Error: {str(e)}")


# ─── PAGE ROUTING ──────────────────────────────────────────────────────
if not st.session_state.logged_in:
    render_login()
else:
    page = st.session_state.get("page", "Get Started")
    if page == "Get Started":
        render_get_started()
    elif page == "Chat":
        render_chat()
    elif page == "Tracker":
        render_tracker()
    elif page == "Resources":
        render_resources()
    else:
        render_get_started()

# ─── FOOTER ────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align: center; color: #9ca3af; font-size: 0.85rem; padding: 20px 0; margin-top: 40px; border-top: 1px solid rgba(0,0,0,0.05);">
    VARAHA 2026 all rights reserved
</div>
""", unsafe_allow_html=True)
