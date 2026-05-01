# 🎬 Agentic Video Alchemist 2.0

> Drop a URL. Get viral-ready content — automatically refined until it hits.

A multi-agent AI pipeline that takes a single YouTube or Twitch URL and produces
platform-optimized content for TikTok, LinkedIn, and Twitter/X — with a
self-improving feedback loop that rewrites low-scoring hooks until they hit a
virality threshold.

---

## 🧠 What Makes This Different

Most AI content tools are a single prompt wrapper. This is a **true agentic pipeline**:

- 6 specialized agents, each with one job
- A **virality scoring loop** that rewrites hooks until they score ≥ 75/100
- Works with **any LLM provider** — Claude, GPT-4o, OpenRouter, Groq — change one line
- Self-improving output, not just generated output

---

## 🏗️ Architecture

```
URL Input
   ↓
Agent 1 — Ingestion Agent       (download + transcribe via yt-dlp + Whisper)
   ↓
Agent 2 — Hook Agent            (extract 3-5 viral moments from transcript)
   ↓
Agent 3 — Scoring Agent         (score each hook 0-100 across 4 criteria)
   ↓
Agent 4 — Rewrite Agent         (rewrite if score < 75, re-score, loop max 3x)
   ↓
Agent 5 — Formatter Agent       (format for TikTok, LinkedIn, Twitter/X)
   ↓
Agent 6 — Output Agent          (bundle into output.json + terminal summary)
   ↓
Streamlit Frontend              (live progress + platform cards + JSON export)
```

---

## 📁 Project Structure

```
video-alchemist/
├── agents/
│   ├── ingestion_agent.py      # Agent 1 — download + transcribe
│   ├── hook_agent.py           # Agent 2 — extract viral hooks
│   ├── scoring_agent.py        # Agent 3 — score hooks 0-100
│   ├── rewrite_agent.py        # Agent 4 — rewrite loop
│   ├── formatter_agent.py      # Agent 5 — platform formatting
│   └── output_agent.py         # Agent 6 — bundle output
├── frontend/
│   └── app.py                  # Streamlit UI
├── utils/
│   └── yt_downloader.py        # yt-dlp + Whisper transcription
├── prompts/
│   ├── hook_prompt.txt         # Hook extraction instructions
│   ├── scoring_prompt.txt      # Virality scoring rubric
│   ├── rewrite_prompt.txt      # Rewrite instructions
│   └── formatter_prompt.txt    # Platform-specific rules
├── config/
│   └── llm_config.py           # Provider-agnostic LLM layer
├── main.py                     # Pipeline orchestrator (CLI + importable)
├── .env.example                # API key template
├── .gitignore                  # Ignores .env and output files
├── README.md
└── requirements.txt
```

---

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/video-alchemist.git
cd video-alchemist
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your API key

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
PROVIDER=openai          # openai | claude | openrouter | groq
API_KEY=your_key_here
MODEL_NAME=gpt-4o
API_BASE=               # only needed for openrouter
```

### 4. Run

**Option A — Streamlit UI (recommended):**
```bash
streamlit run frontend/app.py
```

**Option B — Terminal CLI:**
```bash
python main.py --url "https://youtube.com/watch?v=YOUR_VIDEO_ID"
```

---

## 🔄 Switching LLM Providers

Change only your `.env` file. Zero code changes needed.

| Provider   | PROVIDER value | MODEL_NAME example                        | API_BASE                          |
|------------|----------------|-------------------------------------------|-----------------------------------|
| OpenAI     | `openai`       | `gpt-4o`                                  | _(leave blank)_                   |
| Anthropic  | `claude`       | `claude-3-5-sonnet-20241022`              | _(leave blank)_                   |
| OpenRouter | `openrouter`   | `meta-llama/llama-3.1-70b-instruct`       | `https://openrouter.ai/api/v1`    |
| Groq       | `groq`         | `llama3-70b-8192`                         | _(leave blank)_                   |

---

## 📊 Virality Scoring Rubric

Each hook is scored 0–100 across 4 criteria:

| Criteria         | Max | What it measures                              |
|------------------|-----|-----------------------------------------------|
| Emotional Trigger | 25 | Does it make the viewer feel something?       |
| Curiosity Gap     | 25 | Does it create an open loop they must close?  |
| Relatability      | 25 | Will a broad audience say "that's me"?        |
| Platform Fit      | 25 | Does it feel native to social media?          |

Hooks scoring below **75/100** are automatically rewritten and re-scored up to **3 times**.

---

## 🖥️ Frontend Preview

| Section              | Description                                      |
|----------------------|--------------------------------------------------|
| URL Input            | Paste any YouTube or Twitch link                 |
| Pipeline Progress    | Live tracker showing which agent is running      |
| Summary Metrics      | Total hooks, pass rate, avg score, total rewrites|
| Hook Cards           | Score bar, iteration history, status badge       |
| Platform Outputs     | TikTok, LinkedIn, Twitter side-by-side           |
| Thread Viewer        | Expandable Twitter thread per hook               |
| JSON Export          | Download full output.json in one click           |

---

## 🧪 Testing Individual Agents

Each agent has a built-in test at the bottom of its file:

```bash
python config/llm_config.py         # Test LLM connection
python utils/yt_downloader.py       # Test download + transcription
python agents/ingestion_agent.py    # Test ingestion
python agents/hook_agent.py         # Test hook extraction (mock data)
python agents/scoring_agent.py      # Test scoring (mock data)
python agents/rewrite_agent.py      # Test rewrite loop (mock data)
python agents/formatter_agent.py    # Test platform formatting (mock data)
python agents/output_agent.py       # Test output bundling (mock data)
```

---

## 🛠️ Tech Stack

| Layer            | Tool                        |
|------------------|-----------------------------|
| Agent Framework  | CrewAI                      |
| LLM Routing      | LiteLLM                     |
| LLM Providers    | OpenAI / Claude / OpenRouter / Groq |
| Transcription    | faster-whisper              |
| Video Download   | yt-dlp                      |
| Frontend         | Streamlit                   |
| Language         | Python 3.10+                |

---

## 🏆 Built For

**MLH Global Hack Week: GenAI**

The differentiator: a self-improving agentic loop — not just a single prompt.
Most teams wrap one LLM call. This system has 6 agents collaborating with a
feedback loop that keeps iterating until the content actually hits.

---

