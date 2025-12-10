# Gmail Email Classifier

A Python application that connects to Gmail, reads emails, and classifies them as urgent or not urgent based on content analysis.

## Features

- OAuth2 authentication with Gmail API
- Read the first x emails from your inbox
- Classify emails as urgent or not urgent based on:
  - Subject line keywords
  - Email content/snippet analysis
  - Configurable urgency criteria
- Display classification results with email details

## Prerequisites

- Python 3.7 or higher
- A Google Cloud Project with Gmail API enabled
- OAuth2 credentials from Google Cloud Console

## Setup Instructions

### 1. Enable Gmail API and Get Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth2 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Download the credentials JSON file
   - Save it as `credentials.json` in the project directory

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python gmail_classifier.py
```

On first run, you'll be prompted to:
1. Authorize the application in your browser
2. Grant read-only access to your Gmail
3. The authorization token will be saved for future use

## Usage

When you run the script, you'll be asked:
```
How many emails would you like to classify? (default: 10):
```

Enter the number of emails you want to process, or press Enter for the default (10).

The script will display:
- Email sender
- Email subject
- Classification (URGENT or NOT URGENT)
- Email snippet
- Summary statistics

## Example Output

```
Email 1:
  From: boss@company.com
  Subject: URGENT: Deadline approaching for project
  Classification: URGENT
  Snippet: This is to remind you that the project deadline is tomorrow...
--------------------------------------------------------------------------------
Email 2:
  From: newsletter@example.com
  Subject: Weekly newsletter
  Classification: NOT URGENT
  Snippet: Here are this week's top stories...
--------------------------------------------------------------------------------

Summary:
  Total emails: 10
  Urgent: 3
  Not Urgent: 7
```

## Classification Logic

The classifier uses keyword-based analysis to determine urgency. An email is marked as "urgent" if it contains any of these keywords:

- urgent, asap, immediately
- emergency, critical, important
- deadline, time-sensitive
- action required, alert, warning
- attention needed, priority
- final notice, payment due
- expires today, last chance
- respond now

## Customization

You can customize the classification logic by modifying the `classify_email` method in `gmail_classifier.py`. Consider adding:

- Machine learning models for better classification
- Sender-based rules (e.g., emails from specific people are always urgent)
- Time-based rules (e.g., emails within certain hours)
- Label-based classification

## Security Notes

- The `credentials.json` file contains sensitive information - never commit it to version control
- The `token.pickle` file stores your access token - keep it secure
- The application only requests read-only access to Gmail
- Both files are already included in `.gitignore`

## Troubleshooting

**Error: "Credentials file not found"**
- Make sure `credentials.json` is in the project directory
- Verify you downloaded the correct file from Google Cloud Console

**Error: "Access denied"**
- Check that Gmail API is enabled in your Google Cloud Project
- Verify the OAuth consent screen is properly configured

**Error: "Invalid authentication"**
- Delete `token.pickle` and re-authenticate
- Ensure your credentials haven't expired

## License

This is a tutorial project for learning GitHub Actions and CI/CD.
