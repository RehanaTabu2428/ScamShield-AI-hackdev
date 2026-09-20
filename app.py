"""
ScamShield AI
An AI-powered scam and phishing message analyzer built with Streamlit + Google Gemini.

Run with:
    streamlit run app.py

NOTE ON THIS FILE: the AI detection pipeline (get_client, SYSTEM_INSTRUCTION,
build_user_prompt, call_gemini, validate_and_fill, extract_urls,
analyze_url_heuristics, add_to_history) is UNCHANGED from the original MVP.
Only the presentation layer (CSS + render_* functions + page layout) was
redesigned.
"""

import os
import re
import json
import time
import random
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

# --------------------------------------------------------------------------------------
# ENV + PAGE CONFIG
# --------------------------------------------------------------------------------------

load_dotenv()

st.set_page_config(
    page_title="ScamShield AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

GEMINI_MODEL = "gemini-3.6-flash"

# --------------------------------------------------------------------------------------
# CUSTOM CSS — futuristic AI security command-center theme
# --------------------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

:root{
    --bg-void:#05060b;
    --bg-navy:#0a0f1e;
    --panel:rgba(255,255,255,0.045);
    --panel-border:rgba(148,163,255,0.14);
    --cyan:#22d3ee;
    --blue:#3b82f6;
    --violet:#a855f7;
    --safe:#22c55e;
    --suspicious:#f59e0b;
    --high:#ef4444;
    --text-dim:#8b93ab;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3, .ss-heading { font-family: 'Space Grotesk', sans-serif; }

/* ---------- animated backdrop ---------- */
div[data-testid="stAppViewContainer"]{
    background:
        radial-gradient(ellipse 900px 500px at 12% -5%, rgba(34,211,238,0.10), transparent 60%),
        radial-gradient(ellipse 900px 600px at 90% 10%, rgba(168,85,247,0.10), transparent 60%),
        radial-gradient(ellipse 800px 500px at 50% 100%, rgba(59,130,246,0.08), transparent 60%),
        var(--bg-void);
    background-attachment: fixed;
}
div[data-testid="stAppViewContainer"]::before{
    content:"";
    position:fixed; inset:0; z-index:0; pointer-events:none;
    background-image:
        linear-gradient(rgba(148,163,255,0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(148,163,255,0.05) 1px, transparent 1px);
    background-size: 46px 46px;
    animation: gridpan 40s linear infinite;
    mask-image: radial-gradient(ellipse 80% 60% at 50% 20%, black, transparent 85%);
}
@keyframes gridpan { 0%{background-position:0 0;} 100%{background-position:120px 160px;} }

.block-container{ padding-top: 1.2rem; max-width: 1200px; }

/* ---------- floating particles ---------- */
.particle-field{ position:relative; height:0; }
.particle{
    position:fixed; width:4px; height:4px; border-radius:50%;
    background: var(--cyan); opacity:.55; z-index:0; pointer-events:none;
    box-shadow:0 0 8px 2px rgba(34,211,238,.6);
    animation: floaty 9s ease-in-out infinite;
}
@keyframes floaty{
    0%,100%{ transform: translateY(0) translateX(0); opacity:.25;}
    50%{ transform: translateY(-26px) translateX(10px); opacity:.75;}
}

/* ---------- navbar ---------- */
.ss-navbar{
    display:flex; align-items:center; justify-content:space-between;
    padding: .85rem 1.5rem; border-radius:16px;
    background: linear-gradient(120deg, rgba(15,23,42,.75), rgba(15,23,42,.55));
    backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
    border:1px solid var(--panel-border);
    box-shadow: 0 8px 32px rgba(0,0,0,.35);
    margin-bottom: 1.4rem;
}
.ss-navbar .brand{ display:flex; align-items:center; gap:.6rem; }
.ss-navbar .brand-icon{
    font-size:1.4rem;
    filter: drop-shadow(0 0 10px rgba(34,211,238,.7));
}
.ss-navbar .brand-name{
    font-family:'Space Grotesk', sans-serif; font-weight:800; letter-spacing:.04em;
    font-size:1.05rem; color:#f1f5f9;
}
.ss-navbar .links{ display:flex; gap:1.6rem; align-items:center; }
.ss-navbar .links span{
    font-size:.83rem; color:var(--text-dim); font-weight:600; letter-spacing:.02em;
}
.ss-status{
    display:flex; align-items:center; gap:.45rem;
    font-size:.75rem; font-weight:700; letter-spacing:.05em;
    padding:.3rem .75rem; border-radius:999px;
}
.ss-status.online{ color:#4ade80; background:rgba(34,197,94,.1); border:1px solid rgba(34,197,94,.35); }
.ss-status.offline{ color:#f87171; background:rgba(239,68,68,.1); border:1px solid rgba(239,68,68,.35); }
.dot{ width:7px; height:7px; border-radius:50%; background:currentColor; box-shadow:0 0 8px currentColor; animation: pulseDot 1.8s ease-in-out infinite; }
@keyframes pulseDot{ 0%,100%{opacity:1;} 50%{opacity:.35;} }

@media (max-width: 768px){
    .ss-navbar .links{ display:none; }
}

/* ---------- hero ---------- */
.ss-hero{
    display:flex; align-items:center; gap:2.5rem;
    padding: 2rem 1rem 1.6rem 1rem;
    flex-wrap: wrap;
}
.ss-hero-text{ flex:1 1 380px; min-width:280px; }
.ss-eyebrow{
    display:inline-block; font-size:.72rem; font-weight:700; letter-spacing:.14em;
    color: var(--cyan); text-transform:uppercase; margin-bottom:.7rem;
    border:1px solid rgba(34,211,238,.35); padding:.25rem .7rem; border-radius:999px;
    background:rgba(34,211,238,.06);
}
.ss-hero h1{
    font-size: 3rem; font-weight:800; line-height:1.05; margin:0 0 .6rem 0;
    background: linear-gradient(90deg,#f8fafc 10%, var(--cyan) 55%, var(--violet) 100%);
    -webkit-background-clip:text; background-clip:text; color:transparent;
    letter-spacing:-.01em;
}
.ss-hero .sub{ font-size:1.08rem; color:#cbd5e1; font-weight:600; margin-bottom:.5rem; }
.ss-hero .desc{ font-size:.93rem; color:var(--text-dim); max-width:480px; line-height:1.5; }

@media (max-width: 900px){ .ss-hero h1{ font-size:2.2rem; } }

/* ---------- 3D shield ---------- */
.shield-wrap{
    flex:0 0 240px; width:240px; height:240px; position:relative; margin:0 auto;
    perspective: 800px;
}
.shield-ring{
    position:absolute; inset:0; border-radius:50%;
    border:1.5px solid rgba(34,211,238,.30);
    animation: spin 13s linear infinite;
}
.shield-ring.r2{ inset:22px; border-color:rgba(168,85,247,.32); animation-duration:9s; animation-direction:reverse; }
.shield-ring.r3{ inset:44px; border-color:rgba(59,130,246,.30); animation-duration:17s; border-style:dashed; }
@keyframes spin{ from{ transform:rotate(0deg);} to{ transform:rotate(360deg);} }

.shield-core{
    position:absolute; inset:66px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:58px;
    background: radial-gradient(circle at 32% 28%, rgba(34,211,238,.35), rgba(168,85,247,.14) 55%, transparent 72%);
    filter: drop-shadow(0 0 28px rgba(34,211,238,.55));
    animation: corepulse 3.2s ease-in-out infinite;
}
@keyframes corepulse{ 0%,100%{ transform:scale(1);} 50%{ transform:scale(1.05);} }

.scan-sweep{
    position:absolute; left:8%; right:8%; top:50%; height:2px;
    background: linear-gradient(90deg, transparent, rgba(34,211,238,.9), transparent);
    animation: sweep 2.6s ease-in-out infinite;
    box-shadow: 0 0 12px 1px rgba(34,211,238,.7);
}
@keyframes sweep{ 0%{ top:12%; opacity:0;} 15%{opacity:1;} 50%{ top:85%; opacity:1;} 65%{opacity:0;} 100%{ top:12%; opacity:0;} }

.shield-dot{
    position:absolute; width:5px; height:5px; border-radius:50%;
    background: var(--violet); box-shadow:0 0 8px 2px rgba(168,85,247,.8);
    animation: orbit 6s linear infinite;
}

/* ---------- glass card base ---------- */
.glass{
    background: var(--panel);
    backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
    border:1px solid var(--panel-border);
    border-radius:20px;
    box-shadow: 0 10px 40px rgba(0,0,0,.35);
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.1rem;
    transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
}
.glass:hover{ border-color: rgba(34,211,238,.28); }

.scan-card-title{
    font-family:'Space Grotesk', sans-serif; font-weight:700; letter-spacing:.03em;
    font-size:1.05rem; color:#e2e8f0; margin-bottom:.9rem; display:flex; align-items:center; gap:.5rem;
}
.scan-card-title .accent{ color: var(--cyan); }

.char-counter{ font-size:.75rem; color:var(--text-dim); text-align:right; margin-top:-.4rem; }

/* ---------- disclaimer ---------- */
.ss-disclaimer{
    display:flex; gap:.6rem; align-items:flex-start;
    background:rgba(245,158,11,.07); border:1px solid rgba(245,158,11,.28);
    border-radius:14px; padding:.7rem 1rem; margin-bottom:1.1rem;
    font-size:.83rem; color:#fbbf24;
}

/* ---------- Streamlit widget restyling (via stable data-testid hooks) ---------- */
section[data-testid="stSidebar"]{
    background: linear-gradient(180deg, rgba(10,15,30,.95), rgba(5,6,11,.98));
    border-right: 1px solid var(--panel-border);
}
section[data-testid="stSidebar"] .block-container{ padding-top: 1.4rem; }

div[data-testid="stTextArea"] textarea{
    background: rgba(255,255,255,.035) !important;
    border:1px solid rgba(148,163,255,.18) !important;
    border-radius:14px !important;
    color:#0f172a !important;
    font-size:.92rem !important;
    transition: border-color .2s ease, box-shadow .2s ease;
}
div[data-testid="stTextArea"] textarea:focus{
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 3px rgba(34,211,238,.12) !important;
}

div[data-testid="stTextInput"] input{
    background: rgba(255,255,255,.035) !important;
    border:1px solid rgba(148,163,255,.18) !important;
    border-radius:12px !important;
    color:#0f172a !important;
}
div[data-testid="stTextInput"] input:focus{
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 3px rgba(34,211,238,.12) !important;
}

div[data-testid="stSelectbox"] > div{
    background: rgba(255,255,255,.035) !important;
    border-radius:12px !important;
    border:1px solid rgba(148,163,255,.18) !important;
}

/* radio-as-pills for message type */
div[data-testid="stRadio"] > div{ gap:.5rem; flex-wrap:wrap; }
div[data-testid="stRadio"] label{
    background: rgba(255,255,255,.04);
    border:1px solid rgba(148,163,255,.18);
    padding:.35rem .9rem !important;
    border-radius:999px !important;
    transition: all .18s ease;
}
div[data-testid="stRadio"] label:hover{ border-color: rgba(34,211,238,.5); background: rgba(34,211,238,.06); }

/* primary button — the SCAN button */
div[data-testid="stButton"] button{
    border-radius:14px !important;
    border: 1px solid rgba(34,211,238,.4) !important;
    font-weight:700 !important;
    letter-spacing:.03em !important;
    transition: transform .18s ease, box-shadow .18s ease, filter .18s ease !important;
}
div[data-testid="stButton"] button[kind="primary"]{
    background: linear-gradient(90deg, #0891b2, #6366f1 55%, #a855f7) !important;
    background-size: 160% 100% !important;
    box-shadow: 0 6px 24px rgba(99,102,241,.35) !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover{
    transform: translateY(-2px) scale(1.012);
    box-shadow: 0 10px 32px rgba(139,92,246,.5) !important;
    background-position: 100% 0 !important;
}
div[data-testid="stButton"] button:not([kind="primary"]):hover{
    border-color: rgba(34,211,238,.55) !important;
    transform: translateY(-1px);
}

div[data-testid="stProgress"] > div > div{
    background: linear-gradient(90deg, var(--cyan), var(--violet)) !important;
}

div[data-testid="stMetric"]{
    background: rgba(255,255,255,.035);
    border:1px solid var(--panel-border);
    border-radius:16px; padding: .8rem 1rem;
}
div[data-testid="stMetric"] label{ color: var(--text-dim) !important; }

div[data-testid="stExpander"]{
    background: rgba(255,255,255,.03);
    border:1px solid var(--panel-border) !important;
    border-radius:14px !important;
}

div[data-testid="stAlert"]{ border-radius:14px !important; }

div[data-testid="stTabs"] button[role="tab"]{
    font-weight:600; color: var(--text-dim);
}
div[data-testid="stTabs"] button[aria-selected="true"]{ color: var(--cyan) !important; }

/* ---------- threat status hero card ---------- */
.threat-card{
    border-radius:22px; padding: 1.6rem 1.8rem; margin-bottom:1rem;
    background: linear-gradient(135deg, rgba(15,23,42,.9), rgba(15,23,42,.65));
    border: 1px solid var(--card-border, rgba(34,211,238,.3));
    box-shadow: 0 0 50px -12px var(--card-glow, rgba(34,211,238,.35));
    position:relative; overflow:hidden;
}
.threat-card::after{
    content:""; position:absolute; inset:0;
    background: radial-gradient(circle at 85% 0%, var(--card-glow, rgba(34,211,238,.25)), transparent 55%);
    pointer-events:none;
}
.threat-label{ font-size:.72rem; letter-spacing:.16em; color:var(--text-dim); text-transform:uppercase; font-weight:700; }
.threat-verdict{
    font-family:'Space Grotesk', sans-serif; font-weight:800; font-size:1.9rem;
    color: var(--card-color, #fff); margin: .15rem 0 .3rem 0; letter-spacing:.02em;
}
.threat-badge{
    display:inline-flex; align-items:center; gap:.4rem;
    padding:.28rem .85rem; border-radius:999px; font-size:.78rem; font-weight:700;
    background: var(--card-glow, rgba(34,211,238,.18)); color: var(--card-color, #fff);
    border:1px solid var(--card-border, rgba(34,211,238,.4));
}
.threat-badge.pulse{ animation: badgepulse 1.6s ease-in-out infinite; }
@keyframes badgepulse{ 0%,100%{ box-shadow:0 0 0 0 var(--card-glow);} 50%{ box-shadow:0 0 0 6px transparent;} }

/* ---------- gauge ---------- */
.gauge-wrap{ display:flex; flex-direction:column; align-items:center; justify-content:center; }
.gauge-score{ font-family:'Space Grotesk', sans-serif; font-weight:800; font-size:2.1rem; }
.gauge-label{ font-size:.7rem; letter-spacing:.12em; color:var(--text-dim); text-transform:uppercase; margin-top:.15rem;}

/* ---------- threat signal chips ---------- */
.chip-row{ display:flex; flex-wrap:wrap; gap:.5rem; margin: .3rem 0 .2rem 0; }
.chip{
    display:inline-flex; align-items:center; gap:.35rem;
    padding:.32rem .8rem; border-radius:999px; font-size:.8rem; font-weight:600;
    border:1px solid; white-space:nowrap;
}
.chip-high{ background:rgba(239,68,68,.1); border-color:rgba(239,68,68,.4); color:#fca5a5; }
.chip-medium{ background:rgba(245,158,11,.1); border-color:rgba(245,158,11,.4); color:#fcd34d; }
.chip-low{ background:rgba(234,179,8,.08); border-color:rgba(234,179,8,.35); color:#fde68a; }
.chip-tag{ background:rgba(148,163,255,.08); border-color:rgba(148,163,255,.3); color:#c7d2fe; }

/* ---------- signal explanation card ---------- */
.signal-card{
    border-radius:14px; padding:.85rem 1.05rem; margin-bottom:.55rem;
    border-left:4px solid; background: rgba(255,255,255,.03);
}
.signal-card.high{ border-color:#ef4444; }
.signal-card.medium{ border-color:#f59e0b; }
.signal-card.low{ border-color:#eab308; }
.signal-card b{ font-size:.86rem; letter-spacing:.02em; }
.signal-card .exp{ font-size:.83rem; color:var(--text-dim); margin-top:.15rem; }

.phrase-card{
    background: rgba(239,68,68,.05);
    border:1px solid rgba(239,68,68,.25);
    border-radius:12px; padding:.8rem 1rem; margin-bottom:.55rem;
}
.phrase-text{ font-style:italic; color:#fca5a5; font-weight:600; font-size:.92rem; }
.phrase-reason{ font-size:.82rem; color:var(--text-dim); margin-top:.3rem; }

.safe-response-box{
    background: linear-gradient(120deg, rgba(59,130,246,.08), rgba(168,85,247,.06));
    border:1px solid rgba(59,130,246,.3); border-radius:14px; padding:1rem 1.2rem;
    font-size:.92rem; color:#dbeafe;
}

.action-row{
    display:flex; gap:.7rem; align-items:flex-start; padding:.4rem 0; font-size:.9rem; color:#e2e8f0;
}
.action-num{
    flex:0 0 22px; height:22px; border-radius:50%; background: rgba(34,211,238,.14);
    border:1px solid rgba(34,211,238,.4); color:var(--cyan); font-size:.72rem; font-weight:700;
    display:flex; align-items:center; justify-content:center;
}

/* ---------- scanning stage overlay ---------- */
.scan-overlay{
    border-radius:20px; padding:1.6rem 1.8rem;
    background: linear-gradient(135deg, rgba(15,23,42,.92), rgba(10,15,30,.85));
    border:1px solid rgba(34,211,238,.35);
    box-shadow: 0 0 50px -10px rgba(34,211,238,.35);
    text-align:center;
}
.scan-title{ font-family:'Space Grotesk',sans-serif; font-weight:700; letter-spacing:.08em; color:var(--cyan); font-size:.95rem; margin-bottom:.9rem; }
.scan-bar-track{ width:100%; height:5px; border-radius:99px; background:rgba(255,255,255,.08); overflow:hidden; margin-bottom:1rem; }
.scan-bar-fill{ height:100%; background: linear-gradient(90deg, var(--cyan), var(--violet)); border-radius:99px; }
.scan-stage-list{ text-align:left; max-width:340px; margin:0 auto; font-size:.86rem; }
.scan-stage-list div{ padding:.22rem 0; color:var(--text-dim); }
.scan-stage-list div.done{ color:#86efac; }
.scan-stage-list div.active{ color:var(--cyan); font-weight:600; }

/* ---------- dashboard stat cards ---------- */
.stat-card{
    border-radius:16px; padding:1rem 1.1rem;
    background: rgba(255,255,255,.035); border:1px solid var(--panel-border);
    text-align:center;
}
.stat-card .val{ font-family:'Space Grotesk',sans-serif; font-weight:800; font-size:1.7rem; color:#f1f5f9; }
.stat-card .lbl{ font-size:.72rem; color:var(--text-dim); letter-spacing:.06em; text-transform:uppercase; margin-top:.2rem; }
.stat-card .ic{ font-size:1.1rem; margin-bottom:.2rem; }

.section-heading{
    font-family:'Space Grotesk', sans-serif; font-weight:700; font-size:1.15rem;
    color:#e2e8f0; margin: .2rem 0 .8rem 0; display:flex; align-items:center; gap:.5rem;
}

.history-row{ font-size:.82rem; padding:.22rem 0; color:#cbd5e1; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# a few ambient floating particles, fixed positions (deterministic per session)
_particle_seed = random.Random(42)
_particles_html = "".join(
    f'<div class="particle" style="top:{_particle_seed.randint(5,95)}%; left:{_particle_seed.randint(2,98)}%; '
    f'animation-delay:{_particle_seed.uniform(0,6):.1f}s; animation-duration:{_particle_seed.uniform(7,13):.1f}s;"></div>'
    for _ in range(14)
)
st.markdown(f'<div class="particle-field">{_particles_html}</div>', unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# SESSION STATE
# --------------------------------------------------------------------------------------

if "history" not in st.session_state:
    st.session_state.history = []  # list of dicts: {score, level, scam_type, timestamp}

if "message_input" not in st.session_state:
    st.session_state.message_input = ""

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "last_message" not in st.session_state:
    st.session_state.last_message = ""

if "safe_response_generated" not in st.session_state:
    st.session_state.safe_response_generated = None

# --------------------------------------------------------------------------------------
# DEMO EXAMPLES
# --------------------------------------------------------------------------------------

DEMO_EXAMPLES = {
    "🎁 Example 1 — Fake Prize": (
        "Congratulations! You have won ₹50,000 in our lucky draw. Click this link "
        "immediately to claim your reward. Your account will be blocked within 2 hours "
        "if you do not verify your details."
    ),
    "🏦 Example 2 — Fake Bank Alert": (
        "URGENT: Your SBI account will be suspended today. Verify your PAN and banking "
        "details immediately at http://example.com or your account will be permanently "
        "blocked."
    ),
    "✅ Example 3 — Probably Safe": (
        "Hi, your appointment with the doctor is confirmed for tomorrow at 10:30 AM. "
        "Please arrive 10 minutes early."
    ),
}

MESSAGE_TYPES = ["SMS", "WhatsApp", "Email", "Social Media", "Website/URL", "Other"]

# --------------------------------------------------------------------------------------
# GEMINI CLIENT  (unchanged backend logic)
# --------------------------------------------------------------------------------------

def get_client():
    """Initialize and return a Gemini client, or None if unavailable."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        return None, "missing_key"
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        return client, None
    except Exception as e:
        return None, f"init_error: {e}"


SYSTEM_INSTRUCTION = """You are ScamShield AI, an expert cybersecurity assistant that analyzes messages \
(SMS, WhatsApp, email, social media, or website/URL text) for signs of scams, phishing, and social \
engineering.

You must carefully evaluate the message across these signal categories, not just a single keyword:
1. Urgency or fear tactics
2. Unsolicited rewards
3. Requests for OTP/password/PIN
4. Requests for financial information
5. Suspicious links
6. Impersonation of a real organization or person
7. Threats
8. Fake authority
9. Grammar/style anomalies
10. Requests for secrecy
11. Unexpected attachments
12. Pressure to act immediately
13. Account verification requests
14. Cryptocurrency/payment requests
15. Social engineering patterns

Classify the message into one of: "Legitimate message", "Suspicious but uncertain", "Likely scam", \
"Highly likely scam". Do not claim certainty when evidence is insufficient — calibrate the risk_score \
and confidence honestly, and prefer MEDIUM over HIGH/CRITICAL when signals are mixed or weak.

Risk score bands:
0-24 = LOW, 25-49 = MEDIUM, 50-74 = HIGH, 75-100 = CRITICAL.

You are a DEFENSIVE tool only. You must NEVER produce phishing content, credential-stealing text, \
malicious links, or instructions to bypass security, and you must never ask the user for real \
passwords, OTPs, card numbers, or banking credentials. The "safe_response" field must only contain a \
short, non-committal message a user could send back (e.g. asking to verify through official channels) \
— never anything that provides sensitive information.

Respond ONLY with a single valid JSON object matching this exact schema, with no markdown fences, no \
preamble, and no extra commentary:

{
  "risk_score": <integer 0-100>,
  "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "scam_type": "<short label, or 'None detected'>",
  "classification": "Legitimate message" | "Suspicious but uncertain" | "Likely scam" | "Highly likely scam",
  "summary": "<1-2 sentence explanation>",
  "suspicious_indicators": [
    {"indicator": "<name>", "severity": "HIGH" | "MEDIUM" | "LOW", "explanation": "<short reason>"}
  ],
  "suspicious_phrases": [
    {"phrase": "<verbatim short excerpt from the message>", "reason": "<why suspicious>"}
  ],
  "red_flags": ["<short flag label>", "..."],
  "recommended_actions": ["<action 1>", "<action 2>", "..."],
  "beginner_explanation": "<plain-language explanation for a non-technical user>",
  "safe_response": "<a short, safe reply the user could send instead of complying>"
}

If the message contains no meaningful red flags, return empty arrays for suspicious_indicators, \
suspicious_phrases and red_flags, a low risk_score, and explain briefly why it looks legitimate."""


def build_user_prompt(message: str, message_type: str, url_text: str) -> str:
    parts = [
        f"Message type: {message_type}",
        "Message content to analyze:",
        "---",
        message.strip(),
        "---",
    ]
    if url_text and url_text.strip():
        parts.append(f"\nAdditional suspicious URL provided separately: {url_text.strip()}")
    return "\n".join(parts)


def call_gemini(client, message: str, message_type: str, url_text: str):
    """Call Gemini and return (parsed_json_or_None, error_message_or_None)."""
    prompt = build_user_prompt(message, message_type, url_text)
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "system_instruction": SYSTEM_INSTRUCTION,
                "response_mime_type": "application/json",
                "temperature": 0.3,
            },
        )
    except Exception as e:
        err = str(e)
        if "API_KEY_INVALID" in err or "API key not valid" in err:
            return None, "Your Gemini API key appears to be invalid. Please check your .env file."
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            return None, "Gemini API rate limit reached. Please wait a moment and try again."
        if "timeout" in err.lower() or "deadline" in err.lower():
            return None, "The request to Gemini timed out. Please try again."
        return None, f"Gemini API error: {err}"

    raw_text = getattr(response, "text", None)
    if not raw_text:
        return None, "The AI returned an empty response. Please try again."

    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"```\s*$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None, "Could not parse the AI's response as JSON. Please try again."
        else:
            return None, "Could not parse the AI's response as JSON. Please try again."

    validated, validation_error = validate_and_fill(data)
    if validation_error:
        return None, validation_error
    return validated, None


def validate_and_fill(data: dict):
    """Validate required fields exist and fill sane defaults. Returns (data, error)."""
    if not isinstance(data, dict):
        return None, "Unexpected AI output format."

    try:
        score = int(data.get("risk_score", 0))
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))
    data["risk_score"] = score

    level = str(data.get("risk_level", "")).upper().strip()
    if level not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
        if score <= 24:
            level = "LOW"
        elif score <= 49:
            level = "MEDIUM"
        elif score <= 74:
            level = "HIGH"
        else:
            level = "CRITICAL"
    data["risk_level"] = level

    data.setdefault("scam_type", "None detected")
    data.setdefault("classification", "Suspicious but uncertain")
    data.setdefault("summary", "No summary provided.")
    data.setdefault("suspicious_indicators", [])
    data.setdefault("suspicious_phrases", [])
    data.setdefault("red_flags", [])
    data.setdefault("recommended_actions", [
        "Do not click unfamiliar links.",
        "Do not share OTPs, passwords, or banking details.",
        "Verify through the organization's official website or app.",
    ])
    data.setdefault("beginner_explanation", data["summary"])
    data.setdefault("safe_response", "I will verify this request directly through the official channel.")

    if not isinstance(data["suspicious_indicators"], list):
        data["suspicious_indicators"] = []
    if not isinstance(data["suspicious_phrases"], list):
        data["suspicious_phrases"] = []
    if not isinstance(data["red_flags"], list):
        data["red_flags"] = []
    if not isinstance(data["recommended_actions"], list):
        data["recommended_actions"] = [str(data["recommended_actions"])]

    return data, None


# --------------------------------------------------------------------------------------
# URL HEURISTIC ANALYSIS (no network requests made) — unchanged backend logic
# --------------------------------------------------------------------------------------

URL_REGEX = re.compile(r"(https?://[^\s]+|www\.[^\s]+)", re.IGNORECASE)

SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly",
    "shorte.st", "cutt.ly", "rb.gy", "rebrand.ly",
}


def extract_urls(text: str):
    if not text:
        return []
    return URL_REGEX.findall(text)


def analyze_url_heuristics(url: str):
    """Return a list of (label, detail) heuristic warning tuples for a single URL string."""
    findings = []
    lower = url.lower()

    if lower.startswith("http://"):
        findings.append(("Uses HTTP, not HTTPS", "The connection is not encrypted."))

    domain_match = re.search(r"https?://([^/]+)", url) or re.search(r"^(www\.[^/]+)", url)
    domain = domain_match.group(1) if domain_match else url

    if re.match(r"^\d{1,3}(\.\d{1,3}){3}", domain.replace("www.", "")):
        findings.append(("IP address instead of a domain name", "Legitimate services rarely link via raw IP."))

    for shortener in SHORTENERS:
        if shortener in lower:
            findings.append(("URL shortener detected", f"'{shortener}' hides the real destination."))
            break

    subdomain_count = domain.count(".")
    if subdomain_count >= 3:
        findings.append(("Excessive subdomains", f"'{domain}' has an unusually deep subdomain structure."))

    if re.search(r"[^\x00-\x7F]", url):
        findings.append(("Unusual/non-standard characters", "May be used to visually mimic a trusted domain."))

    if re.search(r"(paypal|bank|login|secure|account|verify)[-.]", lower) and not re.search(
        r"^(https?://)?(www\.)?(paypal|sbi|hdfcbank|icicibank)\.com", lower
    ):
        findings.append(("Misleading domain wording", "Uses trust-related words but isn't the official domain."))

    if len(domain) > 30:
        findings.append(("Very long domain name", "Long domains are sometimes used to obscure the real host."))

    return findings


def add_to_history(data: dict):
    st.session_state.history.insert(0, {
        "score": data["risk_score"],
        "level": data["risk_level"],
        "scam_type": data.get("scam_type", "None detected"),
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    })
    st.session_state.history = st.session_state.history[:20]


# --------------------------------------------------------------------------------------
# UI CONSTANTS
# --------------------------------------------------------------------------------------

# maps backend LOW/MEDIUM/HIGH/CRITICAL -> visual identity
RISK_STYLE = {
    "LOW":      {"color": "#4ade80", "glow": "rgba(34,197,94,.20)",  "border": "rgba(34,197,94,.4)",  "word": "SAFE",       "emoji": "🟢", "pulse": False},
    "MEDIUM":   {"color": "#fbbf24", "glow": "rgba(245,158,11,.20)", "border": "rgba(245,158,11,.4)", "word": "SUSPICIOUS", "emoji": "🟡", "pulse": False},
    "HIGH":     {"color": "#fb923c", "glow": "rgba(249,115,22,.22)", "border": "rgba(249,115,22,.45)","word": "HIGH RISK",  "emoji": "🟠", "pulse": True},
    "CRITICAL": {"color": "#f87171", "glow": "rgba(239,68,68,.25)",  "border": "rgba(239,68,68,.5)",  "word": "CRITICAL",   "emoji": "🔴", "pulse": True},
}

SEVERITY_CLASS = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low"}
SEVERITY_EMOJI = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟡"}

SCAN_STAGES = [
    "Input received",
    "Pattern analysis",
    "Threat intelligence analysis",
    "AI risk assessment",
    "Generating explanation",
]


# --------------------------------------------------------------------------------------
# RENDER HELPERS
# --------------------------------------------------------------------------------------

def render_navbar(client_ok: bool):
    status_class = "online" if client_ok else "offline"
    status_text = "AI PROTECTION ACTIVE" if client_ok else "AI PROTECTION OFFLINE"
    st.markdown(
        f"""
        <div class="ss-navbar">
            <div class="brand">
                <span class="brand-icon">🛡️</span>
                <span class="brand-name">SCAMSHIELD&nbsp;AI</span>
            </div>
            <div class="links">
                <span>Dashboard</span>
                <span>How It Works</span>
                <span>Threat Analysis</span>
                <span>About</span>
            </div>
            <div class="ss-status {status_class}"><span class="dot"></span>{status_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    dots = "".join(
        f'<div class="shield-dot" style="animation-delay:{i * 1.1:.1f}s; '
        f'--r:{78 + (i % 2) * 14}px;" ></div>'
        for i in range(5)
    )
    st.markdown(
        f"""
        <style>
        .shield-dot{{ top:50%; left:50%; animation-name: orbit{0}; }}
        @keyframes orbit0{{ from{{ transform: rotate(0deg) translateX(92px) rotate(0deg);}} to{{ transform: rotate(360deg) translateX(92px) rotate(-360deg);}} }}
        </style>
        <div class="ss-hero">
            <div class="ss-hero-text">
                <div class="ss-eyebrow">⚡ AI Threat Analysis Engine</div>
                <h1>SCAMSHIELD AI</h1>
                <div class="sub">Your AI-powered shield against digital scams.</div>
                <div class="desc">Analyze suspicious messages, links and content before they become threats.</div>
            </div>
            <div class="shield-wrap">
                <div class="shield-ring r1"></div>
                <div class="shield-ring r2"></div>
                <div class="shield-ring r3"></div>
                <div class="shield-core">🛡️</div>
                <div class="scan-sweep"></div>
                {dots}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_disclaimer():
    st.markdown(
        """
        <div class="ss-disclaimer">
            🔒 <div>Never paste real passwords, OTPs, credit-card numbers, CVVs, API keys or other
            sensitive credentials into this application.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def run_scan_animation(placeholder):
    """Cosmetic staged-scanning animation shown while the real Gemini call is prepared.
    Purely presentational — does not alter or fabricate any scan result."""
    total = len(SCAN_STAGES)
    for i in range(total):
        rows = []
        for j, stage in enumerate(SCAN_STAGES):
            if j < i:
                rows.append(f'<div class="done">✓ {stage}</div>')
            elif j == i:
                rows.append(f'<div class="active">→ {stage}</div>')
            else:
                rows.append(f'<div>&nbsp;&nbsp;{stage}</div>')
        pct = int(((i + 1) / total) * 100)
        placeholder.markdown(
            f"""
            <div class="scan-overlay">
                <div class="scan-title">🛰️ AI THREAT ANALYSIS IN PROGRESS</div>
                <div class="scan-bar-track"><div class="scan-bar-fill" style="width:{pct}%;"></div></div>
                <div class="scan-stage-list">{''.join(rows)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(0.28)


def render_gauge(score: int, style: dict) -> str:
    """Returns an HTML string with an animated SVG arc gauge for the risk score."""
    radius = 80
    circumference = 2 * 3.14159265 * radius
    final_offset = circumference * (1 - score / 100)
    anim_id = f"gauge{score}{random.randint(0, 999999)}"
    return f"""
    <div class="gauge-wrap">
        <svg width="200" height="200" viewBox="0 0 200 200" style="filter: drop-shadow(0 0 14px {style['glow']});">
            <circle cx="100" cy="100" r="{radius}" fill="none" stroke="rgba(255,255,255,0.07)" stroke-width="14"/>
            <circle cx="100" cy="100" r="{radius}" fill="none" stroke="{style['color']}" stroke-width="14"
                    stroke-linecap="round" stroke-dasharray="{circumference:.2f}"
                    stroke-dashoffset="{circumference:.2f}"
                    transform="rotate(-90 100 100)"
                    class="{anim_id}"/>
            <text x="100" y="94" text-anchor="middle" font-family="Space Grotesk, sans-serif"
                  font-weight="800" font-size="34" fill="{style['color']}">{score}</text>
            <text x="100" y="118" text-anchor="middle" font-family="Inter, sans-serif"
                  font-size="11" letter-spacing="2" fill="#8b93ab">/ 100</text>
        </svg>
        <style>
        @keyframes fill_{anim_id} {{
            from {{ stroke-dashoffset: {circumference:.2f}; }}
            to {{ stroke-dashoffset: {final_offset:.2f}; }}
        }}
        .{anim_id} {{ animation: fill_{anim_id} 1.3s cubic-bezier(.22,1,.36,1) forwards; }}
        </style>
        <div class="gauge-label">AI Risk Score</div>
    </div>
    """


def render_threat_card(data: dict):
    level = data["risk_level"]
    style = RISK_STYLE.get(level, RISK_STYLE["MEDIUM"])
    pulse_class = "pulse" if style["pulse"] else ""

    col_gauge, col_info = st.columns([1, 1.7])
    with col_gauge:
        st.markdown(
            f"""
            <div class="threat-card" style="--card-glow:{style['glow']}; --card-border:{style['border']}; --card-color:{style['color']};">
                {render_gauge(data['risk_score'], style)}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_info:
        st.markdown(
            f"""
            <div class="threat-card" style="--card-glow:{style['glow']}; --card-border:{style['border']}; --card-color:{style['color']}; height:100%;">
                <div class="threat-label">Threat Level</div>
                <div class="threat-verdict" style="color:{style['color']};">{style['emoji']} {style['word']}</div>
                <span class="threat-badge {pulse_class}" style="--card-glow:{style['glow']}; --card-border:{style['border']}; --card-color:{style['color']};">
                    AI VERDICT · {data.get('classification', '—')}
                </span>
                <div style="margin-top:1rem; font-size:.7rem; letter-spacing:.1em; color:var(--text-dim); text-transform:uppercase;">Scam Type</div>
                <div style="font-size:1.05rem; font-weight:700; color:#e2e8f0; margin-top:.15rem;">{data.get('scam_type', 'None detected')}</div>
                <div style="margin-top:.7rem; font-size:.76rem; color:var(--text-dim);">Informational assessment — not a guarantee that a message is fraudulent.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_signals(data: dict):
    st.markdown('<div class="section-heading">🚩 Threat Signals Detected</div>', unsafe_allow_html=True)
    indicators = data.get("suspicious_indicators", [])
    red_flags = data.get("red_flags", [])

    if not indicators and not red_flags:
        st.markdown(
            '<div class="glass" style="text-align:center; color:var(--text-dim);">✅ No significant threat signals detected.</div>',
            unsafe_allow_html=True,
        )
        return

    if red_flags:
        chips = "".join(f'<span class="chip chip-tag">🏷️ {f}</span>' for f in red_flags)
        st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)

    for ind in indicators:
        sev = str(ind.get("severity", "MEDIUM")).upper()
        css_class = SEVERITY_CLASS.get(sev, "medium")
        emoji = SEVERITY_EMOJI.get(sev, "🟠")
        st.markdown(
            f"""
            <div class="signal-card {css_class}">
                <b>{emoji} {ind.get('indicator', 'Unknown').upper()}</b>
                <div class="exp">{ind.get('explanation', '')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_suspicious_phrases(data: dict):
    phrases = data.get("suspicious_phrases", [])
    if not phrases:
        return
    st.markdown('<div class="section-heading">🔍 Suspicious Phrases</div>', unsafe_allow_html=True)
    for p in phrases:
        st.markdown(
            f"""
            <div class="phrase-card">
                <div class="phrase-text">"{p.get('phrase', '')}"</div>
                <div class="phrase-reason"><strong>Why suspicious:</strong> {p.get('reason', '')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_explanation(data: dict):
    st.markdown('<div class="section-heading">🧠 AI Security Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="glass">
            <div style="font-size:.7rem; letter-spacing:.12em; color:var(--cyan); text-transform:uppercase; font-weight:700; margin-bottom:.5rem;">Why?</div>
            <div style="font-size:.94rem; line-height:1.6; color:#e2e8f0;">{data.get('beginner_explanation', data.get('summary', ''))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_safety_actions(data: dict):
    st.markdown('<div class="section-heading">🛡️ What Should You Do?</div>', unsafe_allow_html=True)
    actions = data.get("recommended_actions", [])
    rows = "".join(
        f'<div class="action-row"><div class="action-num">{i}</div><div>{a}</div></div>'
        for i, a in enumerate(actions, start=1)
    )
    st.markdown(f'<div class="glass">{rows}</div>', unsafe_allow_html=True)


def render_safe_response(data: dict, key_suffix: str):
    st.markdown('<div class="section-heading">✉️ Suggested Safe Response</div>', unsafe_allow_html=True)
    if st.button("✨ Generate Safe Response", key=f"gen_safe_{key_suffix}"):
        st.session_state.safe_response_generated = data.get(
            "safe_response", "I will verify this request directly through the official channel."
        )
    if st.session_state.safe_response_generated:
        st.markdown(
            f'<div class="safe-response-box">{st.session_state.safe_response_generated}</div>',
            unsafe_allow_html=True,
        )


def render_url_analysis(message: str, url_field: str):
    all_text = f"{message}\n{url_field}"
    urls = extract_urls(all_text)
    st.markdown('<div class="section-heading">🔗 URL Analysis</div>', unsafe_allow_html=True)
    st.caption("URL analysis is heuristic and does not confirm that a website is malicious. No websites are visited.")
    if not urls:
        st.markdown(
            '<div class="glass" style="text-align:center; color:var(--text-dim);">No URLs detected in the message or the optional URL field.</div>',
            unsafe_allow_html=True,
        )
        return
    for url in dict.fromkeys(urls):  # de-duplicate, preserve order
        findings = analyze_url_heuristics(url)
        with st.expander(f"🔗 {url}", expanded=True):
            if findings:
                for label, detail in findings:
                    st.markdown(f"⚠️ **{label}** — {detail}")
            else:
                st.markdown("✅ No obvious structural red flags detected in this URL.")


def render_stat_cards():
    total = len(st.session_state.history)
    safe = sum(1 for h in st.session_state.history if h["level"] == "LOW")
    suspicious = sum(1 for h in st.session_state.history if h["level"] == "MEDIUM")
    high_risk = sum(1 for h in st.session_state.history if h["level"] in ("HIGH", "CRITICAL"))

    stats = [
        ("📡", total, "Scans Completed"),
        ("🟢", safe, "Safe Messages"),
        ("🟡", suspicious, "Suspicious"),
        ("🔴", high_risk, "High Risk Alerts"),
    ]
    cols = st.columns(4)
    for col, (icon, val, label) in zip(cols, stats):
        with col:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="ic">{icon}</div>
                    <div class="val">{val}</div>
                    <div class="lbl">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# --------------------------------------------------------------------------------------
# SIDEBAR
# --------------------------------------------------------------------------------------

with st.sidebar:
    st.markdown('<div class="section-heading" style="margin-top:0;">🧪 Try a Demo</div>', unsafe_allow_html=True)
    for label, text in DEMO_EXAMPLES.items():
        if st.button(label, use_container_width=True):
            st.session_state.message_input = text
            st.session_state.last_result = None
            st.session_state.safe_response_generated = None

    st.divider()

    st.markdown('<div class="section-heading">🕘 Recent Scans</div>', unsafe_allow_html=True)
    if st.session_state.history:
        for h in st.session_state.history[:8]:
            emoji = RISK_STYLE.get(h["level"], RISK_STYLE["MEDIUM"])["emoji"]
            st.markdown(
                f"<div class='history-row'>{emoji} <b>{h['score']}</b> — {h['scam_type']}</div>",
                unsafe_allow_html=True,
            )
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.history = []
            st.session_state.last_result = None
            st.rerun()
    else:
        st.caption("No scans yet this session.")

    st.divider()
    st.caption("Built for hackathon demo purposes. AI assessments are informational, not definitive.")


# --------------------------------------------------------------------------------------
# PAGE HEADER
# --------------------------------------------------------------------------------------

client, client_error = get_client()

render_navbar(client_ok=client is not None)
render_hero()

if client is None:
    st.error(
        "⚠️ **Gemini API key not configured.** Create a `.env` file (see `.env.example`) with "
        "`GEMINI_API_KEY=your_key` and restart the app to enable analysis."
    )

render_disclaimer()

# --------------------------------------------------------------------------------------
# SCAN CARD
# --------------------------------------------------------------------------------------

st.markdown('<div class="glass">', unsafe_allow_html=True)
st.markdown(
    '<div class="scan-card-title">🎯 <span class="accent">WHAT DO YOU WANT TO CHECK?</span></div>',
    unsafe_allow_html=True,
)

message_type = st.radio(
    "Message type",
    MESSAGE_TYPES,
    horizontal=True,
    label_visibility="collapsed",
)

message = st.text_area(
    "Paste a suspicious message",
    value=st.session_state.message_input,
    height=170,
    placeholder=(
        "Example:\nCongratulations! You have won ₹50,000.\nClick this link immediately to "
        "claim your reward.\nYour account will be blocked within 2 hours."
    ),
    key="message_area",
    label_visibility="collapsed",
)
st.session_state.message_input = message
st.markdown(f'<div class="char-counter">{len(message)} characters</div>', unsafe_allow_html=True)

url_field = st.text_input(
    "Suspicious URL (optional)",
    placeholder="🔗 Optional: paste a suspicious URL here",
    label_visibility="collapsed",
)

analyze_clicked = st.button("🔎 SCAN WITH AI", type="primary", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# ANALYSIS FLOW
# --------------------------------------------------------------------------------------

if analyze_clicked:
    st.session_state.safe_response_generated = None

    if not message or not message.strip():
        st.warning("⚠️ Please paste a message to analyze.")
    elif client is None:
        st.error("⚠️ Cannot analyze — the Gemini API key is missing or invalid. Check your `.env` file.")
    else:
        scan_placeholder = st.empty()
        run_scan_animation(scan_placeholder)
        try:
            result, error = call_gemini(client, message, message_type, url_field)
        except Exception as e:
            result, error = None, f"Unexpected error: {e}"
        scan_placeholder.empty()

        if error:
            st.error(f"⚠️ {error}")
        elif result:
            st.session_state.last_result = result
            st.session_state.last_message = message
            add_to_history(result)
            st.success("✅ Analysis complete.")

# --------------------------------------------------------------------------------------
# RESULTS DASHBOARD
# --------------------------------------------------------------------------------------

if st.session_state.last_result:
    data = st.session_state.last_result
    st.markdown('<div class="section-heading" style="font-size:1.3rem; margin-top:.6rem;">📋 Analysis Results</div>', unsafe_allow_html=True)

    render_threat_card(data)

    tab1, tab2, tab3, tab4 = st.tabs(["🚩 Signals & Phrases", "🧠 AI Explanation", "🛡️ Safety Actions", "🔗 URL Analysis"])

    with tab1:
        render_signals(data)
        render_suspicious_phrases(data)

    with tab2:
        render_explanation(data)
        render_safe_response(data, key_suffix="main")

    with tab3:
        render_safety_actions(data)

    with tab4:
        render_url_analysis(st.session_state.last_message, url_field)

else:
    st.markdown(
        '<div class="glass" style="text-align:center; color:var(--text-dim); padding:1.6rem;">'
        '👆 Paste a message above (or try a demo from the sidebar) and hit <b>SCAN WITH AI</b> to get started.'
        '</div>',
        unsafe_allow_html=True,
    )

# --------------------------------------------------------------------------------------
# SECURITY DASHBOARD (real session stats only — nothing fabricated)
# --------------------------------------------------------------------------------------

st.markdown('<div class="section-heading" style="margin-top:1.6rem;">📊 Security Dashboard</div>', unsafe_allow_html=True)
render_stat_cards()
