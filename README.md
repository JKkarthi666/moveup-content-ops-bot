⚡ MoveUp ContentOps AI

AI-Powered Content Intelligence Platform for MoveUp Media

Candidate: Jai Karthikeyan
Role Applied: AI Automation & Operations Engineer
Assignment: MoveUp Media Technical Assessment

Executive Summary

MoveUp ContentOps AI is an autonomous content intelligence platform designed to help campaign managers monitor channel performance, identify winning content patterns, benchmark competitors, and generate actionable recommendations through natural language.

The platform automates the complete content analytics workflow:

Fetches the latest 10 videos from MoveUp properties and competitors
Calculates engagement metrics and performance scores
Detects content trends and momentum shifts
Generates executive-ready AI reports
Enables conversational analytics through an autonomous AI agent
Supports competitive benchmarking and scheduled reporting

The system combines deterministic analytics with LLM-powered reasoning to provide reliable and explainable content intelligence.

Business Problem

Content teams often spend hours manually:

Exporting YouTube metrics
Comparing channel performance
Identifying top-performing content
Writing weekly reports
Monitoring competitors

This project automates that workflow and transforms raw YouTube data into actionable business insights.

Key Features
Content Analytics
Fetches the latest 10 videos per channel
Calculates engagement rate
Scores content using a deterministic proxy scoring engine
Classifies performance into:
Strong
Average
Underperforming
AI Reporting

Generates:

Executive summaries
Top performer analysis
Underperforming content diagnosis
Content pattern intelligence
Actionable recommendations
Conversational Agent

Supports natural language requests such as:

Compare Netflu and ThePlayoffsTV
Identify the worst-performing video
Generate an executive report
Benchmark against competitors
Recommend next actions
Competitive Benchmarking

Tracks:

@Netflu
@ThePlayoffsTV
@ESPNBrasil
@TNTSportsBR
Automated Scheduling

Weekly automated report generation pipeline.

Intelligent Caching

Reduces:

API usage
Response times
Cost
Architecture
YouTube Data API
        │
        ▼
YouTube Extractor
        │
        ▼
Analytics Engine
        │
        ▼
Persistent Cache
        │
        ▼
Report Engine (Groq)
        │
        ▼
Agent Router
        │
        ▼
Streamlit Dashboard
Technology Stack
Backend
Python 3.13
Pydantic v2
Streamlit
Tenacity
AI Layer
Groq API
Llama 3.3 70B Versatile
Function Calling
Data Layer
YouTube Data API v3
JSON Cache Storage
Testing
Pytest
Mock-based API Testing
Performance Scoring Methodology

The platform uses a deterministic scoring engine.

Components:

View Performance (50%)
Engagement Performance (40%)
Recency Score (10%)

To prevent viral videos from dominating rankings, view counts are normalized using logarithmic scaling.

This produces a balanced proxy score between 0 and 100.

Performance tiers:

Score	Tier
65+	Strong
40–64	Average
Below 40	Underperforming
Important API Limitations

The public YouTube Data API does not expose:

Click Through Rate (CTR)
Audience Retention
Watch Time
Shares

Therefore this platform relies on:

Engagement Rate
View Velocity
Proxy Score

as public performance indicators.

Project Structure
moveup-content-ops-bot/
│
├── config/
│   └── channels.json
│
├── data/
│   ├── cache/
│   └── reports/
│
├── screenshots/
│
├── src/
│   ├── agent.py
│   ├── analytics.py
│   ├── cache.py
│   ├── logger.py
│   ├── models.py
│   ├── prompts.py
│   ├── report_engine.py
│   ├── scheduler.py
│   └── youtube.py
│
├── tests/
│   ├── test_analytics.py
│   └── test_system.py
│
├── app.py
├── requirements.txt
├── .env.example
└── README.md
Screenshots
Executive Dashboard




AI Reports




Competitive Benchmark




Installation
git clone <repository_url>
cd moveup-content-ops-bot

pip install -r requirements.txt

Create a .env file:

YOUTUBE_API_KEY=your_key_here
GROQ_API_KEY=your_key_here

Run the application:

streamlit run app.py
Running Tests
pytest
Future Improvements
Multi-platform social analytics
PostgreSQL persistence layer
Historical trend dashboards
Multi-user authentication
Slack and Discord reporting integrations
Advanced forecasting models
Assignment Deliverables

Included:

Source Code
AI Agent
Analytics Engine
Streamlit Dashboard
Automated Tests
Competitive Benchmarking
Scheduling Extension
Documentation
Author

Jai Karthikeyan

AI Automation & Operations Engineer

Built for the MoveUp Media Technical Assessment.
