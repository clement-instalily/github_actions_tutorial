#!/usr/bin/env python3
"""
Email Insight Engine - Main Orchestrator
Coordinates all components to analyze emails and generate insights
"""

import os
import sys
import time
import json
from google.genai.errors import ServerError
from tqdm import tqdm
from dotenv import load_dotenv
from app.fetcher import EmailFetcher
from google import genai
from app.PROMPTs import EMAIL_ANALYSIS_PROMPT 

class EmailInsightEngine:
    def __init__(
        self,
        email_address=None,
        email_password=None,
        imap_server=None,
        gemini_api_key=None,
        gemini_model=None,
        folders=None,
        days_back=10,
        batch_size=10,
        confidence_threshold=0.6,
        data_dir="data",
        batch_delay=3,
        max_retries=5
    ):
        """Initialize the Email Insight Engine

        Args:
            email_address: Email address to connect to (defaults to EMAIL_ADDRESS env var)
            email_password: Email password (defaults to EMAIL_PASSWORD env var)
            imap_server: IMAP server address (defaults to imap.gmail.com)
            gemini_api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            gemini_model: Gemini model to use (defaults to gemini-2.0-flash-exp)
            folders: List of folders to analyze (defaults to INBOX, Sent, Spam, Promotions)
            days_back: Number of days to analyze (default: 10)
            batch_size: Batch size for AI processing (default: 10)
            confidence_threshold: Minimum confidence for entity extraction (default: 0.6)
            data_dir: Directory for storing data (default: "data")
            batch_delay: Seconds to wait between batches (default: 3)
            max_retries: Maximum retry attempts for API errors (default: 5)
        """
        print("\n" + "="*60)
        print("EMAIL INSIGHT ENGINE")
        print("="*60 + "\n")

        # Load environment variables
        load_dotenv()

        # Email configuration
        self.email_address = email_address or os.getenv("EMAIL_ADDRESS")
        self.email_password = email_password or os.getenv("EMAIL_PASSWORD")
        self.imap_server = imap_server or os.getenv("IMAP_SERVER", "imap.gmail.com")

        # Gemini AI configuration
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.gemini_model = gemini_model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        # Analysis configuration
        self.folders = folders if folders is not None else [
            'INBOX',
            '[Gmail]/Sent Mail',
            '[Gmail]/Spam',
            '[Gmail]/Promotions'
        ]
        self.days_back = days_back
        self.batch_size = batch_size
        self.confidence_threshold = confidence_threshold
        self.data_dir = data_dir
        self.batch_delay = batch_delay
        self.max_retries = max_retries

        # Validate required configuration
        self._validate_config()

        # Initialize components
        self.fetcher = EmailFetcher(
            self.email_address,
            self.email_password,
            self.imap_server
        )

    def _validate_config(self):
        """Validate required configuration values"""
        errors = []

        if not self.email_address:
            errors.append("email_address not provided or EMAIL_ADDRESS not set in .env file")

        if not self.email_password:
            errors.append("email_password not provided or EMAIL_PASSWORD not set in .env file")

        if not self.gemini_api_key:
            errors.append("gemini_api_key not provided or GEMINI_API_KEY not set in .env file")

        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Configuration errors:\n{error_msg}")

    def run_full_analysis(self):
        """Execute complete email analysis pipeline"""


        ALL_EMAILS = {
            "IMPORTANCE": [],
            "URGENCY": [],
            "INFORMATIONAL": [],
            "SCHEDULE": [],
            "COMMITMENTS": [],
            "OUTBOUND_COMMITMENTS": [],
            "REQUESTS": [],
            "DEADLINES": []
        }


        try:
            # Phase 1: Email Collection
            print("PHASE 1: Email Collection")
            print("-" * 60)
            emails = self._fetch_emails()

            if not emails:
                print("\nNo new emails found. Exiting.")
                return

            print(f"Fetched {len(emails)} emails")
            # Phase 2: AI Analysis
            print("\nPHASE 2: AI Analysis")
            print("-" * 60)

            total_batches = (len(emails) + self.batch_size - 1) // self.batch_size

            for i in range(0, len(emails), self.batch_size):
                batch_num = (i // self.batch_size) + 1
                email_batch = emails[i:i+self.batch_size]
                batch_response = self._analyze_emails(email_batch)
                parsed_mp = self._extract_important_info(batch_response)

                # updated ALL_EMAILS with the parsed_mp
                for key, value in parsed_mp.items():
                    ALL_EMAILS[key].extend(value)

                return ALL_EMAILS
                print(f"ALL_EMAILS: \n {ALL_EMAILS}")



            # Phase 4: Calculate Metrics
            print("\n📊 PHASE 4: Calculating Metrics")
            print("-" * 60)
            self._calculate_metrics()

            # Phase 5: Generate Report
            print("\n📝 PHASE 5: Generating Report")
            print("-" * 60)
            self._generate_report()

        except KeyboardInterrupt:
            print("\n\n⚠️  Analysis interrupted by user")
            self.data_manager.save_all()
        except Exception as e:
            print(f"\n❌ Error during analysis: {e}")

            if "503" in str(e) or "overloaded" in str(e).lower():
                print("\n💡 Suggestions:")
                print("   1. Wait a few minutes and try again")
                print("   2. Reduce batch_size (currently: {})".format(self.batch_size))
                print("   3. Reduce days_back to analyze fewer emails")
                print("   4. Try running during off-peak hours")
                print("\n   Example: engine = EmailInsightEngine(batch_size=5, days_back=3)")

            import traceback
            traceback.print_exc()
        finally:
            self.fetcher.close()


    def _process_email(self, email_data, category):
        """
        Process an email and return only relevant info based on the category.

        Args:
            email_data: Full email analysis data
            category: Category type (IMPORTANCE, URGENCY, INFORMATIONAL, SCHEDULE,
                     COMMITMENTS, OUTBOUND_COMMITMENTS, REQUESTS, DEADLINES)

        Returns:
            dict: Filtered email data with only relevant fields for the category
        """
        # Common base fields for all categories
        base_info = {
            "sender_name": email_data.get("sender_name"),
            "from_address": email_data.get("from_address"),
            "date_sent": email_data.get("date_sent"),
            "date_received": email_data.get("date_received"),
            "summary": email_data.get("summary", "")
        }

        metadata = email_data.get('metadata', {})
        entities = email_data.get('entities', {})
        sent_analysis = email_data.get('sent_analysis', {})

        # Category-specific fields
        if category == "IMPORTANCE":
            return {
                **base_info,
                "category": email_data.get("category"),
                "classification": email_data.get("classification"),
                "importance": metadata.get("importance"),
                "important_dates": email_data.get("important_dates", [])
            }

        elif category == "URGENCY":
            return {
                **base_info,
                "urgency": metadata.get("urgency"),
                "deadline": metadata.get("deadline"),
                "time_sensitivity": metadata.get("time_sensitivity"),
                "important_dates": email_data.get("important_dates", [])
            }

        elif category == "INFORMATIONAL":
            return {
                **base_info,
                "content_type": metadata.get("content_type"),
                "category": email_data.get("category")
            }

        elif category == "SCHEDULE":
            return {
                **base_info,
                "calendar": entities.get("calendar", []),
                "important_dates": email_data.get("important_dates", [])
            }

        elif category == "COMMITMENTS":
            return {
                **base_info,
                "commitments": entities.get("commitments", [])
            }

        elif category == "OUTBOUND_COMMITMENTS":
            return {
                **base_info,
                "is_sent_email": sent_analysis.get("is_sent_email"),
                "outbound_commitments": sent_analysis.get("outbound_commitments", []),
                "deliverables_promised": sent_analysis.get("deliverables_promised", []),
                "confirmations_sent": sent_analysis.get("confirmations_sent", [])
            }

        elif category == "REQUESTS":
            return {
                **base_info,
                "requests": entities.get("requests", []),
                "urgency": metadata.get("urgency")
            }

        elif category == "DEADLINES":
            return {
                **base_info,
                "deadlines": entities.get("deadlines", []),
                "important_dates": email_data.get("important_dates", [])
            }

        # Default: return base info
        return base_info


    def _extract_important_info(self, batch_response):
        """
        Parse AI response and categorize emails by type.
        A single email can fit multiple categories.

        Returns:
            dict: Dictionary with categorized emails:
                - IMPORTANCE: Emails tagged as IMPORTANT
                - URGENCY: Emails tagged as URGENT
                - INFORMATIONAL: News/newsletters/updates
                - SCHEDULE: Emails with calendar events/dates
                - COMMITMENTS: Emails with commitments from others
                - OUTBOUND_COMMITMENTS: Emails with your commitments
                - REQUESTS: Emails with tasks/requests
                - DEADLINES: Emails with deadlines
        """

        COLLECTION_MP = {
            "IMPORTANCE": [],
            "URGENCY": [],
            "INFORMATIONAL": [],
            "SCHEDULE": [],
            "COMMITMENTS": [],
            "OUTBOUND_COMMITMENTS": [],
            "REQUESTS": [],
            "DEADLINES": []
        }

        if not batch_response:
            return COLLECTION_MP

        try:
            # Clean the response - remove markdown code blocks if present
            cleaned_response = batch_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # Parse JSON response
            email_analyses = json.loads(cleaned_response)

            # If it's a single object, wrap it in a list
            if isinstance(email_analyses, dict):
                email_analyses = [email_analyses]

            for email_data in email_analyses:

                metadata = email_data.get('metadata', {})
                entities = email_data.get('entities', {})
                sent_analysis = email_data.get('sent_analysis', {})

                # Check 1: Email tagged as IMPORTANT
                if metadata.get('importance') == 'IMPORTANT':
                    info_data = self._process_email(email_data, "IMPORTANCE")
                    COLLECTION_MP["IMPORTANCE"].append(info_data)

                # Check 2: Email tagged as URGENT
                if metadata.get('urgency') == 'URGENT':
                    urgent_data = self._process_email(email_data, "URGENCY")
                    COLLECTION_MP["URGENCY"].append(urgent_data)

                # Check 3: Informational content (news, newsletters, updates)
                if metadata.get('content_type') == 'INFORMATIONAL':
                    info_data = self._process_email(email_data, "INFORMATIONAL")
                    COLLECTION_MP["INFORMATIONAL"].append(info_data)

                # Check 4: Has schedules/calendar events
                if entities.get('calendar') or email_data.get('important_dates'):
                    schedule_data = self._process_email(email_data, "SCHEDULE")
                    COLLECTION_MP["SCHEDULE"].append(schedule_data)

                # Check 5: Has commitments (inbound - what others promised)
                if entities.get('commitments'):
                    commitment_data = self._process_email(email_data, "COMMITMENTS")
                    COLLECTION_MP["COMMITMENTS"].append(commitment_data)

                # Check 6: Has outbound commitments (sent emails with "I will" statements)
                if (sent_analysis.get('outbound_commitments') or
                    sent_analysis.get('deliverables_promised')):
                    outbound_data = self._process_email(email_data, "OUTBOUND_COMMITMENTS")
                    COLLECTION_MP["OUTBOUND_COMMITMENTS"].append(outbound_data)

                # Check 7: Has requests/tasks
                if entities.get('requests'):
                    request_data = self._process_email(email_data, "REQUESTS")
                    COLLECTION_MP["REQUESTS"].append(request_data)

                # Check 8: Has deadlines
                if entities.get('deadlines'):
                    deadline_data = self._process_email(email_data, "DEADLINES")
                    COLLECTION_MP["DEADLINES"].append(deadline_data)

            # Print summary statistics
            print(f"   ✓ Categorized emails:")
            for category, emails in COLLECTION_MP.items():
                if emails:
                    print(f"      - {category}: {len(emails)} emails")

        except json.JSONDecodeError as e:
            print(f"   ⚠️  Warning: Failed to parse JSON response: {e}")
            print(f"   Response preview: {batch_response[:200]}...")
        except Exception as e:
            print(f"   ⚠️  Warning: Error extracting important info: {e}")

        return COLLECTION_MP 




    def _fetch_emails(self):
        """Fetch emails from all folders"""
        print(f"Connecting to {self.imap_server}...")
        self.fetcher.connect()

        print(f"Fetching emails from last {self.days_back} days...")
        print(f"Folders: {', '.join(self.folders)}\n")

        emails = self.fetcher.fetch_all_folders(
            folders=self.folders,
            days_back=self.days_back
        )

        print(f"\n✓ Fetched {len(emails)} total emails")
        return emails

    def _analyze_emails(self, email_batch):
        """Analyze emails with AI with retry logic"""

        # Format emails for the prompt
        emails_text = ""
        for i, email in enumerate(email_batch, 1):
            emails_text += f"""
                    EMAIL {i}:
                    Sender Name: {email.get('sender_name', 'N/A')}
                    From: {email.get('from_address', 'N/A')}
                    To: {email.get('to_address', 'N/A')}
                    Subject: {email.get('subject', 'N/A')}
                    Date Sent: {email.get('date_sent', 'N/A')}
                    Date Received: {email.get('date_received', 'N/A')}
                    Folder: {email.get('folder', 'N/A')}
                    Body:
                    {email.get('body', 'N/A')}
                    ---
                    """

        client = genai.Client()

        # List of models to try (in order of preference)
        models_to_try = [
            "gemini-2.5-flash", 
            "gemini-2.5-flash-lite"
        ]

        # Retry configuration
        max_retries = self.max_retries
        base_delay = 2  # seconds


        for model in models_to_try:
            print(f"\nTrying model: {model}")

            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=f"""Analyze the following batch of {len(email_batch)} emails and return a JSON array with analysis for each email.

                        EMAILS TO ANALYZE:
                        {emails_text}

                        ANALYSIS INSTRUCTIONS:
                        {EMAIL_ANALYSIS_PROMPT}

                        RULES:
                        - Return a JSON array with one object per email (total: {len(email_batch)} objects)
                        - Do not skip any emails
                        - Follow the exact JSON format specified above
                        - Return ONLY valid JSON, no markdown formatting
                        """
                    )

                    print(f"✓ Successfully analyzed with {model}")
                    return response.text

                except ServerError as e:
                    if e.status_code == 503:  # Service Unavailable
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)  # Exponential backoff
                            print(f"⚠️  Model {model} overloaded (attempt {attempt + 1}/{max_retries})")
                            print(f"   Retrying in {delay} seconds...")
                            time.sleep(delay)
                        else:
                            print(f"Model {model} failed after {max_retries} attempts")
                            break  # Try next model
                    else:
                        # For other server errors, raise immediately
                        raise
                except Exception as e:
                    print(f"Error with model {model}: {e}")
                    break  # Try next model

        return None


    def _calculate_metrics(self):
        """Calculate performance metrics"""
        emails_df = self.data_manager.get_emails_last_n_days(self.days_back)

        if emails_df.empty:
            return

        # Count emails by folder
        inbox_count = len(emails_df[emails_df['folder'] == 'INBOX'])
        sent_count = len(emails_df[emails_df['folder'] == '[Gmail]/Sent Mail'])

        # Count tasks
        tasks_df = self.data_manager.tasks_df
        pending_tasks = len(tasks_df[tasks_df['status'] == 'pending'])

        print(f"✓ Emails received (inbox): {inbox_count}")
        print(f"✓ Emails sent: {sent_count}")
        print(f"✓ Pending tasks: {pending_tasks}")

    def _generate_report(self):
        """Generate weekly insight report"""
        stats = self.data_manager.get_stats()

        print("\n" + "="*60)
        print("EMAIL INSIGHT ENGINE - WEEKLY REPORT")
        print("="*60)
        print(f"\n Summary Statistics:")
        print(f"  Total Emails: {stats['total_emails']}")
        print(f"  Total Tasks: {stats['total_tasks']}")
        print(f"  Pending Tasks: {stats['pending_tasks']}")
        print(f"  Entities Extracted: {stats['total_entities']}")
        print(f"  Contacts Tracked: {stats['total_contacts']}")

        # Show top pending tasks
        pending_tasks = self.data_manager.get_pending_tasks()
        if not pending_tasks.empty:
            print(f"\n📋 Top Pending Tasks:")
            for idx, task in pending_tasks.head(5).iterrows():
                print(f"  • [{task['task_type']}] {task['description']}")

        # Show financial entities
        financial_entities = self.data_manager.get_entities_by_type('invoice')
        if not financial_entities.empty:
            print(f"\n💰 Financial Alerts:")
            for idx, entity in financial_entities.head(5).iterrows():
                print(f"  • {entity['entity_subtype']}: ${entity['value']}")

        print("\n" + "="*60)


def main():
    """Main entry point"""

    # initialize the engine by creating reader and gemini analyzer 
    engine = EmailInsightEngine()

    # Logic to run the full analysis 
    engine.run_full_analysis()


if __name__ == "__main__":
    main()
