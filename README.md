# 🛡️ ScamShield AI

An AI-powered assistant that analyzes suspicious SMS, WhatsApp, email, social-media and website
messages, and explains **why** they might be a scam — in plain language.

## Problem

Phishing and scam messages are one of the most common ways people are defrauded today. They rely
less on sophisticated hacking and more on **social engineering**: urgency, fake rewards, impersonation
and fear. Most people don't have the time or background to recognize these patterns before it's too
late — especially first-time smartphone users, students, and older relatives who are frequent targets.

## Solution

ScamShield AI lets a user paste any suspicious message and get an instant, structured breakdown:
a risk score, the likely scam type, the specific red flags detected, the exact phrases that triggered
concern, a beginner-friendly explanation, and a safe way to respond — without ever having to click the
suspicious link or share sensitive information to find out.

## Features

* AI scam detection powered by Google Gemini
* 0–100 AI risk score with LOW / MEDIUM / HIGH / CRITICAL bands
* Scam type classification
* Red flag detection across 15 social-engineering signal categories
* Suspicious phrase highlighting with explanations
* Heuristic URL analysis (HTTP vs HTTPS, shorteners, IP-based links, excessive subdomains — no live
  requests are ever made to the URL)
* Beginner-friendly explanations
* Safe response generator
* Session-only scan history and analytics
* Polished Streamlit dashboard UI

## Tech Stack

- Python
- Streamlit
- Google Gemini (`google-genai` SDK)
- python-dotenv

## Architecture

```text
User Message
      ↓
Input Processing
      ↓
Gemini AI Analyzer
      ↓
Structured JSON
      ↓
Risk Assessment
      ↓
Red Flag Detection
      ↓
Safety Recommendations
      ↓
Streamlit Dashboard
```

## How to Run

```bash
git clone <repository-url>
cd scamshield-ai

python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the project root (copy `.env.example`):

```text
GEMINI_API_KEY=your_key
```

Then run:

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Why This Matters

Most scams don't rely on sophisticated technical exploits — they rely on **social engineering**:
urgency, fake authority, and fear. ScamShield AI doesn't just say "this is a scam" — it explains the
*technique* being used, so the underlying skill transfers to the next message the user sees, even
without the app.

## Future Improvements

- Multilingual scam detection
- Browser extension for real-time protection
- Email inbox integration
- WhatsApp screenshot analysis (OCR)
- Real-time threat intelligence APIs
- RAG grounded in verified cybersecurity resources
- Local/offline ML classifier fallback
- Mobile application

*(None of the above are implemented in this MVP.)*

## Safety Notes

- This is a **defensive** tool only. It never generates phishing content, credential-stealing text,
  or instructions to bypass security.
- It never visits or crawls the URLs it analyzes — URL analysis is purely textual/heuristic.
- Never paste real passwords, OTPs, credit-card numbers, CVVs, API keys, or other sensitive
  credentials into this application.
- The AI risk score is an informational assessment, not a guarantee that a message is fraudulent.
