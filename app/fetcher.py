#!/usr/bin/env python3
"""
Email Fetcher - Multi-folder IMAP Email Retrieval
Fetches emails from Inbox, Sent Mail, Spam, and Promotions folders
"""

import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import re


class EmailFetcher:
    def __init__(self, email_address, password, imap_server="imap.gmail.com"):
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.mail = None

    def connect(self):
        """Establish IMAP connection"""
        self.mail = imaplib.IMAP4_SSL(self.imap_server)
        self.mail.login(self.email_address, self.password)
        print(f"Connected to {self.imap_server}")

    def close(self):
        """Close IMAP connection"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
            except:
                try:
                    self.mail.logout()
                except:
                    pass

    def list_folders(self):
        """List all available IMAP folders"""
        status, folders = self.mail.list()
        if status == 'OK':
            return [f.decode() for f in folders]
        return []

    def fetch_from_folder(self, folder_name, days_back=7):
        """
        Fetch emails from specific folder within date range

        Args:
            folder_name: IMAP folder name (e.g., 'INBOX', '[Gmail]/Sent Mail')
            days_back: Number of days to look back (default 7)

        Returns:
            List of email dictionaries
        """
        try:
            # Select folder
            status, _ = self.mail.select(f'"{folder_name}"', readonly=True)
            if status != 'OK':
                print(f"Could not select folder: {folder_name}")
                return []

            # Calculate date threshold
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")

            # Search for emails since date
            status, messages = self.mail.search(None, f'(SINCE {since_date})')
            if status != 'OK':
                print(f"Search failed for folder: {folder_name}")
                return []

            email_ids = messages[0].split()
            print(f"Found {len(email_ids)} emails in {folder_name}")

            emails = []
            for email_id in email_ids:
                email_data = self._fetch_email_by_id(email_id, folder_name)
                if email_data:
                    emails.append(email_data)

            return emails

        except Exception as e:
            print(f"Error fetching from {folder_name}: {e}")
            return []

    def _fetch_email_by_id(self, email_id, folder_name):
        """Fetch and parse a single email"""
        try:
            # Fetch both RFC822 (email content) and INTERNALDATE (received date)
            status, msg_data = self.mail.fetch(email_id, "(RFC822 INTERNALDATE)")
            if status != 'OK':
                return None

            # Parse INTERNALDATE for date_received
            date_received = None
            for response_part in msg_data:
                if isinstance(response_part, bytes):
                    # Extract INTERNALDATE from the response
                    date_received = self._parse_internaldate(response_part.decode())

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    # Extract headers
                    subject = self._decode_header(msg["Subject"])
                    from_address = msg.get("From")
                    to_address = msg.get("To")
                    cc_address = msg.get("Cc")
                    date_str = msg.get("Date")
                    message_id = msg.get("Message-ID")
                    in_reply_to = msg.get("In-Reply-To")
                    references = msg.get("References")

                    # Parse dates
                    date_sent = self._parse_date(date_str)
                    # Use date_received from INTERNALDATE, fallback to date_sent
                    if not date_received:
                        date_received = date_sent

                    # Extract sender name from From address
                    sender_name = self._extract_sender_name(from_address)

                    # Get email body
                    body = self._get_email_body(msg)

                    # Determine if it's a reply
                    is_reply = bool(in_reply_to) or (subject and subject.startswith("Re:"))

                    # Create thread_id (use In-Reply-To or Message-ID)
                    thread_id = in_reply_to if in_reply_to else message_id

                    return {
                        'message_id': message_id,
                        'subject': subject,
                        'from_address': from_address,
                        'sender_name': sender_name,
                        'to_address': to_address,
                        'cc_address': cc_address,
                        'date_sent': date_sent,
                        'date_received': date_received,
                        'body': body,
                        'folder': folder_name,
                        'is_reply': is_reply,
                        'thread_id': thread_id
                    }

        except Exception as e:
            print(f"Error parsing email {email_id}: {e}")
            return None

    def _decode_header(self, header):
        """Decode email header"""
        if header is None:
            return ""
        decoded = decode_header(header)
        result = []
        for content, encoding in decoded:
            if isinstance(content, bytes):
                try:
                    result.append(content.decode(encoding or "utf-8"))
                except:
                    result.append(content.decode("utf-8", errors="ignore"))
            else:
                result.append(str(content))
        return "".join(result)

    def _parse_date(self, date_str):
        """Parse email date string to datetime"""
        if not date_str:
            return datetime.now()

        try:
            # Remove timezone info for simplicity
            # Format: "Mon, 10 Dec 2025 14:30:00 -0500"
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except:
            return datetime.now()

    def _get_email_body(self, msg):
        """Extract email body"""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode()
            except:
                body = str(msg.get_payload())

        return body

    def _parse_internaldate(self, response_str):
        """Parse INTERNALDATE from IMAP response"""
        try:
            # INTERNALDATE format: INTERNALDATE "17-Dec-2025 10:30:45 +0000"
            import re
            match = re.search(r'INTERNALDATE "([^"]+)"', response_str)
            if match:
                date_str = match.group(1)
                # Parse the date string
                return datetime.strptime(date_str.split('+')[0].strip(), "%d-%b-%Y %H:%M:%S")
        except Exception as e:
            pass
        return None

    def _extract_sender_name(self, from_address):
        """Extract sender name from From header

        Examples:
            "John Doe <john@example.com>" -> "John Doe"
            "john@example.com" -> "john@example.com"
            "\"Doe, John\" <john@example.com>" -> "Doe, John"
        """
        if not from_address:
            return ""

        try:
            from email.utils import parseaddr
            name, addr = parseaddr(from_address)
            # If name is available, use it; otherwise use the email address
            return name if name else addr
        except:
            return from_address

    def fetch_all_folders(self, folders=None, days_back=7):
        """
        Fetch emails from multiple folders

        Args:
            folders: List of folder names (default: Gmail folders)
            days_back: Number of days to look back

        Returns:
            List of all emails from all folders
        """
        if folders is None:
            # Default Gmail folders
            folders = [
                'INBOX',
                '[Gmail]/Sent Mail',
                '[Gmail]/Spam',
                '[Gmail]/Promotions'
            ]

        all_emails = []
        for folder in folders:
            print(f"\nFetching from {folder}...")
            emails = self.fetch_from_folder(folder, days_back)
            all_emails.extend(emails)

        print(f"\nTotal emails fetched: {len(all_emails)}")
        return all_emails


if __name__ == "__main__":
    # Test email fetcher
    import os
    from dotenv import load_dotenv

    load_dotenv()

    email_address = os.getenv("EMAIL_ADDRESS")
    email_password = os.getenv("EMAIL_PASSWORD")
    imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")

    if email_address and email_password:
        fetcher = EmailFetcher(email_address, email_password, imap_server)
        try:
            fetcher.connect()
            emails = fetcher.fetch_all_folders(days_back=7)
            print(f"\nSuccessfully fetched {len(emails)} emails")
        finally:
            fetcher.close()
    else:
        print("Please set EMAIL_ADDRESS and EMAIL_PASSWORD in .env file")
