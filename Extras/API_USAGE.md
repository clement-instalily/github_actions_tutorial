# Email Insight Engine - FastAPI Backend

This document provides comprehensive information on using the FastAPI backend for the Email Insight Engine.

## Overview

The FastAPI backend provides a REST API endpoint that runs the email analysis pipeline and returns categorized insights from your emails.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
- `EMAIL_ADDRESS`: Your email address
- `EMAIL_PASSWORD`: Your email app password (not regular password)
- `GEMINI_API_KEY`: Your Google Gemini API key
- `IMAP_SERVER`: IMAP server address (default: imap.gmail.com)

Optional API configuration:
- `HOST`: API host address (default: 0.0.0.0)
- `PORT`: API port (default: 8000)

## Running the API

### Development Mode

```bash
python api.py
```

Or using uvicorn directly:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### 1. Health Check

**GET /** or **GET /health**

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "message": "API is operational",
  "timestamp": "2025-12-15T10:30:00"
}
```

### 2. Get Categories

**GET /categories**

Get available email categories and their descriptions.

**Response:**
```json
{
  "categories": {
    "IMPORTANCE": "Emails tagged as important",
    "URGENCY": "Emails tagged as urgent",
    "INFORMATIONAL": "News, newsletters, and updates",
    "SCHEDULE": "Emails with calendar events or important dates",
    "COMMITMENTS": "Commitments made by others to you",
    "OUTBOUND_COMMITMENTS": "Commitments you made to others",
    "REQUESTS": "Tasks and requests",
    "DEADLINES": "Emails with deadlines"
  }
}
```

### 3. Analyze Emails

**POST /analyze**

Run the full email analysis pipeline and return categorized insights.

**Request Body:**
```json
{
  "days_back": 7,
  "batch_size": 10,
  "folders": ["INBOX", "[Gmail]/Sent Mail"],
  "confidence_threshold": 0.6,
  "max_retries": 5
}
```

**Request Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `email_address` | string | env var | Email address to analyze |
| `email_password` | string | env var | Email password |
| `imap_server` | string | imap.gmail.com | IMAP server address |
| `gemini_api_key` | string | env var | Gemini API key |
| `gemini_model` | string | gemini-2.5-flash | Gemini model to use |
| `folders` | array | Gmail defaults | List of folders to analyze |
| `days_back` | integer | 10 | Number of days to analyze (1-90) |
| `batch_size` | integer | 10 | Batch size for AI processing (1-50) |
| `confidence_threshold` | float | 0.6 | Minimum confidence (0.0-1.0) |
| `batch_delay` | integer | 3 | Seconds between batches |
| `max_retries` | integer | 5 | Max retry attempts (1-10) |

**Response:**
```json
{
  "status": "success",
  "message": "Email analysis completed successfully",
  "timestamp": "2025-12-15T10:30:00",
  "results": {
    "IMPORTANCE": [
      {
        "sender_name": "John Doe",
        "from_address": "john@example.com",
        "date_sent": "2025-12-10",
        "summary": "Meeting agenda for Q4 planning",
        "category": "work",
        "importance": "IMPORTANT"
      }
    ],
    "URGENCY": [],
    "INFORMATIONAL": [],
    "SCHEDULE": [],
    "COMMITMENTS": [],
    "OUTBOUND_COMMITMENTS": [],
    "REQUESTS": [],
    "DEADLINES": []
  },
  "summary": {
    "IMPORTANCE": 1,
    "URGENCY": 0,
    "INFORMATIONAL": 0,
    "SCHEDULE": 0,
    "COMMITMENTS": 0,
    "OUTBOUND_COMMITMENTS": 0,
    "REQUESTS": 0,
    "DEADLINES": 0
  }
}
```

## Usage Examples

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Get categories
curl http://localhost:8000/categories

# Analyze emails (minimal request - uses env vars)
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"days_back": 7}'

# Analyze emails (full request)
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "days_back": 7,
    "batch_size": 10,
    "folders": ["INBOX", "[Gmail]/Sent Mail"],
    "confidence_threshold": 0.6
  }'
```

### Using Python requests

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Analyze emails
payload = {
    "days_back": 7,
    "batch_size": 10,
    "folders": ["INBOX", "[Gmail]/Sent Mail"]
}

response = requests.post(f"{BASE_URL}/analyze", json=payload)
result = response.json()

print(f"Status: {result['status']}")
print(f"Summary: {result['summary']}")
print(f"Important emails: {len(result['results']['IMPORTANCE'])}")
```

### Using JavaScript/Fetch

```javascript
// Health check
fetch('http://localhost:8000/health')
  .then(response => response.json())
  .then(data => console.log(data));

// Analyze emails
fetch('http://localhost:8000/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    days_back: 7,
    batch_size: 10,
    folders: ['INBOX', '[Gmail]/Sent Mail']
  })
})
  .then(response => response.json())
  .then(data => {
    console.log('Status:', data.status);
    console.log('Summary:', data.summary);
    console.log('Important emails:', data.results.IMPORTANCE);
  });
```

## Interactive API Documentation

Once the API is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive documentation where you can:
- View all available endpoints
- See request/response schemas
- Test API endpoints directly from the browser

## Error Handling

### Common Errors

1. **400 Bad Request - Configuration Error**
```json
{
  "detail": "Configuration error: EMAIL_ADDRESS not set in .env file"
}
```

**Solution:** Check your .env file and ensure all required variables are set.

2. **500 Internal Server Error - Analysis Failed**
```json
{
  "detail": "Analysis failed: Connection refused"
}
```

**Solution:** Check your email credentials and IMAP server settings.

## Rate Limiting Considerations

The Gemini API has rate limits. If you encounter 503 errors:

1. Reduce `batch_size` (e.g., from 10 to 5)
2. Increase `batch_delay` (e.g., from 3 to 5 seconds)
3. Reduce `days_back` to analyze fewer emails
4. The API automatically retries with exponential backoff

## Security Recommendations

For production deployment:

1. **Use HTTPS**: Deploy behind a reverse proxy (nginx, Caddy)
2. **Add Authentication**: Implement API key or OAuth authentication
3. **Restrict CORS**: Update `allow_origins` in api.py to specific domains
4. **Environment Variables**: Never commit .env file to version control
5. **Rate Limiting**: Add rate limiting middleware
6. **Secrets Management**: Use secrets manager (AWS Secrets Manager, etc.)

## Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t email-insight-api .
docker run -p 8000:8000 --env-file .env email-insight-api
```

## Troubleshooting

### Issue: ModuleNotFoundError
**Solution:** Install dependencies: `pip install -r requirements.txt`

### Issue: Cannot connect to IMAP server
**Solution:**
- Check IMAP is enabled in your email settings
- Use an app-specific password (not your regular password)
- Check firewall settings

### Issue: Gemini API errors
**Solution:**
- Verify GEMINI_API_KEY is correct
- Check API quota and billing
- Reduce batch_size if rate limited

## Support

For issues or questions:
1. Check the logs in the console
2. Review the error response details
3. Consult the interactive API docs at /docs

## License

[Your License Here]
