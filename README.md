# ⚡ MoveUp ContentOps AI

**Role:** AI Automation & Operations Engineer  
**Project:** MoveUp Content Ops Bot  

## 🎯 Executive Summary
MoveUp Media requires an automated system to fetch the last 10 videos from each channel, generate performance insights, and provide a conversational interface for campaign managers.

The **MoveUp ContentOps AI** satisfies all required objectives. It is an autonomous, agentic platform that replaces manual extraction with a persistent JSON cache layer, replaces subjective guessing with a deterministic logarithmic scoring engine, and utilizes Groq Llama-3.3 function calling to instantly generate **content pattern intelligence and actionable recommendations**.

---

## 📸 Platform Previews

### 📊 Executive Dashboard & Channel Metrics (Full 10-Video Scope)
![Channel Metrics](screenshots/metrics.png)

### 📑 Synthesized AI Production Reports
![AI Reports](screenshots/ai_reports.png)

### ⚔️ Competitive Sector Benchmarking (Bonus Extension)
![Competitive Benchmark](screenshots/benchmark.png)

---

## 🏗️ Enterprise Architecture & Data Flow

1. **Configuration (`config/channels.json`):** Tracks MoveUp properties and competitors dynamically.
2. **Persistent Cache Layer (`src/cache.py`):** Saves API calls by caching responses locally.
3. **Data Extraction (`src/youtube.py`):** Utilizes the official YouTube `contentDetails.relatedPlaylists.uploads` method to reliably resolve handles.
4. **Analytics Engine (`src/analytics.py`):** Normalizes viral view spikes using a logarithmic mathematical formula.
5. **AI Intelligence Layer (`src/report_engine.py`):** Pre-computed analytics fed to Groq to generate strictly validated `ReportResult` Pydantic models.
6. **Agentic Router (`src/agent.py`):** An autonomous function-calling agent capable of **multi-tool execution**.

---

## 📂 Repository Structure

```text
moveup-content-ops-bot/
├── config/             # SaaS configuration (channel lists)
├── data/               # Persistent cache & report storage
├── screenshots/        # Architecture & UI preview images
├── src/                # Core Python logic
│   ├── agent.py        # Autonomous tool-calling agent
│   ├── analytics.py    # Logarithmic scoring engine
│   ├── cache.py        # State management
│   ├── models.py       # Pydantic data contracts
│   ├── report_engine.py# AI report synthesis
│   └── youtube.py      # API extraction engine
├── tests/              # Automated test suite
├── app.py              # Streamlit management platform
├── requirements.txt    # Project dependencies
└── README.md           # Documentation