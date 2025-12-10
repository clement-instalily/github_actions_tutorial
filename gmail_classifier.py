"""
Gmail Email Classifier
This script connects to Gmail, reads the first x emails, and classifies them as urgent or not urgent.
"""

import os
import pickle
import re
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailClassifier:
    """A class to handle Gmail authentication and email classification."""
    
    def __init__(self, credentials_path: str = 'credentials.json'):
        """
        Initialize the Gmail Classifier.
        
        Args:
            credentials_path: Path to the OAuth2 credentials JSON file
        """
        self.credentials_path = credentials_path
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        creds = None
        
        # The file token.pickle stores the user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found at {self.credentials_path}. "
                        "Please download it from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
    
    def read_emails(self, max_results: int = 10) -> List[Dict]:
        """
        Read the first x emails from Gmail inbox.
        
        Args:
            max_results: Number of emails to retrieve (default: 10)
        
        Returns:
            List of email dictionaries containing id, subject, sender, snippet, and body
        """
        try:
            # Get list of messages
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                labelIds=['INBOX']
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print('No messages found.')
                return []
            
            emails = []
            for message in messages:
                # Get full message details
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                
                email_data = self._parse_email(msg)
                emails.append(email_data)
            
            return emails
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def _parse_email(self, msg: Dict) -> Dict:
        """
        Parse email message to extract relevant information.
        
        Args:
            msg: Raw email message from Gmail API
        
        Returns:
            Dictionary with parsed email data
        """
        headers = msg['payload']['headers']
        
        # Extract subject, from, and date
        subject = ''
        sender = ''
        date = ''
        
        for header in headers:
            if header['name'] == 'Subject':
                subject = header['value']
            elif header['name'] == 'From':
                sender = header['value']
            elif header['name'] == 'Date':
                date = header['value']
        
        # Get email snippet
        snippet = msg.get('snippet', '')
        
        return {
            'id': msg['id'],
            'subject': subject,
            'sender': sender,
            'date': date,
            'snippet': snippet
        }
    
    def classify_email(self, email: Dict) -> str:
        """
        Classify an email as 'urgent' or 'not urgent' based on keywords and patterns.
        
        Args:
            email: Email dictionary with subject, sender, and snippet
        
        Returns:
            Classification result: 'urgent' or 'not urgent'
        """
        # Keywords that typically indicate urgent emails
        urgent_keywords = [
            'urgent', 'asap', 'immediately', 'emergency', 'critical',
            'important', 'deadline', 'time-sensitive', 'action required',
            'alert', 'warning', 'attention needed', 'priority', 'final notice',
            'payment due', 'expires today', 'last chance', 'respond now'
        ]
        
        # Combine subject and snippet for analysis
        content = f"{email.get('subject', '')} {email.get('snippet', '')}".lower()
        
        # Check for urgent keywords using word boundary matching to avoid false positives
        for keyword in urgent_keywords:
            # Use regex with word boundaries for more accurate matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, content):
                return 'urgent'
        
        # Check for urgent patterns
        # Emails from specific senders could be marked as urgent (e.g., boss, clients)
        # This is a basic implementation - can be extended with ML models
        
        return 'not urgent'
    
    def classify_emails(self, max_results: int = 10) -> List[Dict]:
        """
        Read and classify emails.
        
        Args:
            max_results: Number of emails to process
        
        Returns:
            List of emails with classification
        """
        emails = self.read_emails(max_results)
        
        for email in emails:
            email['classification'] = self.classify_email(email)
        
        return emails


def main():
    """Main function to demonstrate email classification."""
    try:
        # Initialize classifier
        classifier = GmailClassifier()
        
        # Ask user how many emails to classify
        num_emails = input("How many emails would you like to classify? (default: 10): ")
        num_emails = int(num_emails) if num_emails else 10
        
        print(f"\nReading and classifying {num_emails} emails...\n")
        
        # Get and classify emails
        classified_emails = classifier.classify_emails(max_results=num_emails)
        
        # Display results
        urgent_count = 0
        not_urgent_count = 0
        
        for i, email in enumerate(classified_emails, 1):
            classification = email['classification']
            if classification == 'urgent':
                urgent_count += 1
            else:
                not_urgent_count += 1
            
            print(f"Email {i}:")
            print(f"  From: {email['sender']}")
            print(f"  Subject: {email['subject']}")
            print(f"  Classification: {classification.upper()}")
            print(f"  Snippet: {email['snippet'][:100]}...")
            print("-" * 80)
        
        print(f"\nSummary:")
        print(f"  Total emails: {len(classified_emails)}")
        print(f"  Urgent: {urgent_count}")
        print(f"  Not Urgent: {not_urgent_count}")
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nPlease follow the setup instructions in README.md to configure Gmail API credentials.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    main()
