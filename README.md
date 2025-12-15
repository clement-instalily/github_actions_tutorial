# Email-Based Productivity System

An intelligent email productivity system that leverages AI to manage inbox workflow and track daily tasks. The project consists of an email reader/summarizer (current implementation) with plans to evolve into a comprehensive todo monitoring app.

## Overview

This project started as a GitHub Actions learning exercise but has evolved into a practical productivity tool that:
- Reads and analyzes incoming emails using Google Gemini AI
- Classifies emails by urgency to help prioritize responses
- Plans to integrate with a todo monitoring system for daily productivity tracking

## Current Implementation: Email Insight Engine

### Features

- **Multi-folder Email Support**: Fetches emails from INBOX, Sent Mail, Spam, and other folders
- **AI-Powered Analysis**: Uses Google Gemini to analyze and categorize emails
- **8 Category Classification**: Importance, Urgency, Informational, Schedule, Commitments, Outbound Commitments, Requests, Deadlines
- **RESTful API**: FastAPI backend for programmatic access

### Architecture

```
┌─────────────────────┐
│  FastAPI Backend    │
│     (api.py)        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Email Insight Engine│
│(email_insight_      │
│   engine.py)        │
└──────────┬──────────┘
           │
           ├──▶ ┌──────────────────┐
           │    │  Email Fetcher   │
           │    │   (fetcher.py)   │
           │    └────────┬─────────┘
           │             │
           │             ▼
           │    ┌──────────────────┐
           │    │   IMAP Server    │
           │    │  (Multi-folder)  │
           │    └──────────────────┘
           │
           └──▶ ┌──────────────────┐
                │   Gemini API     │
                │ (Batch Analysis) │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │ 8 Categories     │
                │ Classification   │
                └──────────────────┘
```

### Tech Stack

- **Python 3.13**: Core language
- **FastAPI**: Modern web framework for building APIs
- **IMAP Library**: Email fetching via `imaplib`
- **Google Gemini API**: AI-powered analysis and classification
- **python-dotenv**: Environment variable management

### How It Works

1. **API Request**: Client sends POST request to `/analyze` endpoint
2. **Email Fetching**: Fetcher connects to IMAP server and retrieves emails from multiple folders
3. **Batch Processing**: Emails are processed in batches to optimize API usage
4. **AI Analysis**: Each email is analyzed using Gemini API with structured prompts
5. **Categorization**: AI classifies emails into 8 categories with detailed metadata
6. **Response**: Returns categorized results with summaries and insights

## Usage

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Start the API server
python app/api.py

# Or using uvicorn directly
uvicorn app.api:app --reload
```

The API will be available at `http://localhost:8000`

### API Features

- **RESTful API**: Clean HTTP endpoints for email analysis
- **Categorized Results**: Returns emails organized by 8 categories (IMPORTANCE, URGENCY, INFORMATIONAL, SCHEDULE, COMMITMENTS, OUTBOUND_COMMITMENTS, REQUESTS, DEADLINES)
- **Flexible Configuration**: Override settings via API request or use environment variables
- **Interactive Documentation**: Built-in Swagger UI and ReDoc
- **Background Processing**: Handles long-running analysis tasks

### API Endpoints

1. **GET /health** - Health check endpoint
2. **GET /categories** - List available email categories
3. **POST /analyze** - Run full email analysis pipeline

### Example Usage

```bash
# Health check
curl http://localhost:8000/health

# Analyze last 7 days of emails
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"days_back": 7, "batch_size": 10}'
```

```python
# Python example
import requests

response = requests.post(
    "http://localhost:8000/analyze",
    json={"days_back": 7, "folders": ["INBOX"]}
)

results = response.json()
print(f"Important emails: {len(results['results']['IMPORTANCE'])}")
print(f"Urgent emails: {len(results['results']['URGENCY'])}")
```

### Interactive Documentation

Visit these URLs when the API is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Testing the API

Run the included test script:
```bash
python test_api.py
```

For complete API documentation, see [API_USAGE.md](Extras/API_USAGE.md).

## Future Architecture: Todo Monitoring App

The long-term vision is to build an email-based productivity system with automated check-ins throughout the day. See [long_term_goal.md](Extras/long_term_goal.md) for complete architectural details.

### Planned Features

**Three Daily Check-ins**:
- **10 AM - Morning Review**: Shows yesterday's completed tasks + 5-day highlights, asks for today's plan
- **3 PM - Midday Check-in**: Shows morning progress, asks for updates
- **8 PM - Evening Wrap-up**: Full day activity review, requests reflection

**Core Capabilities**:
- Email-first interface (works from inbox, no app switching required)
- AI-powered task parsing from freeform replies
- Automatic progress summaries ("top 5 things from last 5 days")
- Timezone-aware scheduling for multiple users
- Simple reply-to-email interaction model

### Planned Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Scheduler     │────▶│   Email Service  │────▶│  User's Inbox   │
│ (cron/cloud)    │     │ (SendGrid/SES)   │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                          │
                                                          ▼ (reply)
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Database      │◀────│   Reply Parser   │◀────│ Inbound Email   │
│ (Postgres/etc)  │     │   + AI Summary   │     │    Webhook      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │
         └──▶ Stores: User prefs, TodoItems, DailySummaries
```

### Development Roadmap

**Phase 1 - MVP** (Single user, simple parsing):
- [ ] Email sending with scheduled check-ins
- [ ] Basic reply parsing with structured format
- [ ] SQLite storage for todos and summaries
- [ ] Manual classification of tasks

**Phase 2 - AI Enhancement**:
- [ ] Freeform reply parsing using Gemini/Claude
- [ ] Auto-generated 5-day summaries
- [ ] Web dashboard for history viewing
- [ ] Improved urgency detection

**Phase 3 - Multi-user Platform**:
- [ ] User registration and management
- [ ] Per-user timezone handling
- [ ] Customizable check-in times
- [ ] Integration with external tools (calendar, Notion, etc.)

## Project Structure

```
github_actions_tutorial/
├── app/                            # Main application folder
│   ├── email_insight_engine.py     # Main email analysis orchestrator
│   ├── fetcher.py                  # Email fetching via IMAP
│   ├── PROMPTs.py                  # AI prompt templates
│   └── api.py                      # FastAPI backend server
├── test_api.py                     # API testing script
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── utils/                          # Utility functions
├── Extras/                         # Additional documentation
│   ├── API_USAGE.md                # Complete API documentation
│   ├── IMPLEMENTATION_STATUS.md    # Implementation status
│   └── long_term_goal.md          # Future architecture documentation
└── README.md                      # This file
```

## Environment Variables

Required in `.env` file:

```bash
EMAIL_ADDRESS=your-email@gmail.com          # Your email address
EMAIL_PASSWORD=your-app-password            # Gmail app password
IMAP_SERVER=imap.gmail.com                 # IMAP server (default: Gmail)
GEMINI_API_KEY=your-gemini-api-key         # Google Gemini API key
```

## Security Considerations

- Never commit `.env` file to version control
- Use app-specific passwords, not your main email password
- Store API keys securely
- Consider rate limiting for API calls in production

## Contributing

This is currently a personal productivity project and learning exercise. Feedback and suggestions welcome.

## License

MIT License - feel free to use and modify for your own productivity needs.
