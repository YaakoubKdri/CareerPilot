# CareerPilot

AI-powered job application assistant with multi-agent orchestration, PDF export, and email delivery.

## Features

- **Multi-Agent Pipeline**: CrewAI-powered agents for job analysis, resume tailoring, cover letter writing, interview prep, and review
- **MCP Integration**: Model Context Protocol server for job analysis and resume scoring
- **PDF Export**: Generate professional PDFs of all application materials
- **Email Delivery**: Send generated materials directly to your inbox
- **Modern UI**: Clean, responsive interface with tabs and copy functionality

## Tech Stack

- **Backend**: FastAPI, CrewAI, Python
- **Frontend**: HTML, CSS, Vanilla JS
- **Config**: YAML-based agent and task definitions
- **PDF**: ReportLab
- **Email**: SMTP

## Quick Start

### 1. Install Dependencies

```bash
pip install fastapi crewai python-dotenv reportlab pyyaml uvicorn
```

### 2. Configure Environment

Copy `.env.example` to `.env` and set your credentials:

```env
# OpenAI API Key (REQUIRED for CrewAI agents)
OPENAI_API_KEY=sk-proj-your-api-key-here

# Email Configuration (optional - for email delivery)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

**Important:** The `OPENAI_API_KEY` is required for the CrewAI agents to generate content. Get your API key from [OpenAI](https://platform.openai.com/api-keys).

### 3. Start Everything

```bash
python run.py
```

This starts both backend (port 8000) and frontend (port 3000).

Or run separately:
```bash
cd backend && uvicorn main:app --reload --port 8000
cd frontend && python -m http.server 3000
```

## Project Structure

```
careerpilot/
├── config/
│   ├── agents.yaml       # Agent definitions
│   ├── tasks.yaml        # Task pipeline
│   └── mcp_config.yaml   # MCP server tools
├── backend/
│   ├── agents/
│   │   └── loader.py     # Load agents from YAML
│   ├── tasks/
│   │   └── executor.py   # Execute task pipeline
│   ├── mcp_tools/
│   │   └── server.py     # MCP server with tools
│   └── main.py           # FastAPI app
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── .env.example
└── README.md
```

## Usage

1. Fill in job title, company, job description, and your resume
2. Click "Generate Application Materials"
3. View results in tabs (Resume, Cover Letter, Interview Prep, Review)
4. Copy content, download as PDF, or send via email

## Configuration

### OpenAI API Key

The `OPENAI_API_KEY` environment variable is **required**. Without it, the CrewAI agents cannot generate content.

Get your API key from: https://platform.openai.com/api-keys

### Agents (`config/agents.yaml`)

Define agent roles, goals, and backstories. Each agent handles a specific aspect of job application preparation.

### Tasks (`config/tasks.yaml`)

Define the sequential pipeline with dependencies. Tasks are mapped to agents and execute in order.

### MCP Tools (`config/mcp_config.yaml`)

Configure MCP server tools for job analysis and resume matching capabilities.

## API Endpoints

- `GET /` - Health check
- `POST /generate` - Generate application materials using CrewAI
- `POST /generate-pdf` - Generate PDF document
- `POST /send-email` - Send materials via email
