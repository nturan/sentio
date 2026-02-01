# Cursor 2-Day AI Hackathon — Sentio

![Cursor 2-Day AI Hackathon](https://ai-beavers.com/_next/image?url=%2Fimages%2Fhackathon-hero-20012026.png&w=1920&q=75)

---

# Sentio

> AI-powered Change Management Assistant for tracking stakeholder sentiment and driving organizational transformation

Sentio helps change managers monitor stakeholder feedback, generate actionable recommendations, and gain insights throughout organizational change initiatives. The platform uses AI agents to analyze stakeholder sentiment, create targeted surveys, and provide data-driven guidance.

## Tech Stack

- **Frontend**: React, TypeScript, Tailwind CSS, Vite
- **Backend**: Python, FastAPI, LangGraph
- **Database**: SQLite
- **AI/ML**: OpenAI GPT-4o, Tavily (web search)
- **Hosting**: Heroku (Docker)

## How to Run

### Prerequisites
- Node.js 18+
- Python 3.11+
- OpenAI API key
- Tavily API key (optional, for web search)

### Setup

```bash
# Clone the repo
git clone https://github.com/your-team/sentio.git
cd sentio

# Set up environment variables
cp .env.example .env
# Add your API keys to .env:
# OPENAI_API_KEY=sk-...
# TAVILY_API_KEY=tvly-...
# LOCALE=en
```

### Run Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .

# Seed with demo data (optional)
python -m app.seed --scenario six_month

# Start the server
uvicorn app.main:app --reload
```

### Run Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`

## Features

- **Stakeholder Management**: Track stakeholder groups with Mendelow matrix positioning
- **Impulse Tracking**: Record and visualize stakeholder sentiment over time
- **AI Recommendations**: Generate actionable recommendations based on stakeholder feedback
- **Survey Generation**: Create targeted surveys with AI-generated questions
- **Insights Dashboard**: AI-powered insights and trend analysis
- **Multi-language Support**: Full i18n support (English/German)

## Details

### Architecture

The application uses a multi-agent architecture powered by LangGraph:

- **Chat Agent**: General change management assistant
- **Survey Agent**: Generates targeted stakeholder surveys
- **Recommendations Agent**: Creates actionable recommendations
- **Insights Agent**: Analyzes data patterns and generates insights
- **Orchestrator**: Routes requests to appropriate agents

### Demo Scenarios

Seed the database with realistic demo data:

```bash
# Fresh project
python -m app.seed --scenario new_project

# 3 months of data
python -m app.seed --scenario three_month

# 6 months of data
python -m app.seed --scenario six_month

# 10 months of data
python -m app.seed --scenario ten_month
```
