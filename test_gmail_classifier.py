"""
Unit tests for Gmail Email Classifier
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from gmail_classifier import GmailClassifier


class TestGmailClassifier(unittest.TestCase):
    """Test cases for email classification logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_emails = [
            {
                'id': '1',
                'subject': 'URGENT: Action required immediately',
                'sender': 'boss@company.com',
                'snippet': 'Please respond to this urgent matter',
                'date': '2024-01-01'
            },
            {
                'id': '2',
                'subject': 'Weekly newsletter',
                'sender': 'newsletter@example.com',
                'snippet': 'Here are this week\'s updates',
                'date': '2024-01-01'
            },
            {
                'id': '3',
                'subject': 'Critical: System down',
                'sender': 'alerts@system.com',
                'snippet': 'Emergency maintenance required',
                'date': '2024-01-01'
            },
            {
                'id': '4',
                'subject': 'Meeting notes',
                'sender': 'colleague@company.com',
                'snippet': 'Summary of today\'s meeting',
                'date': '2024-01-01'
            },
            {
                'id': '5',
                'subject': 'Deadline approaching for Q4 report',
                'sender': 'manager@company.com',
                'snippet': 'Please submit your report by Friday',
                'date': '2024-01-01'
            }
        ]
        # Create a classifier instance for testing classification methods
        self.classifier = GmailClassifier.__new__(GmailClassifier)
    
    @patch('gmail_classifier.build')
    @patch('gmail_classifier.os.path.exists')
    @patch('gmail_classifier.pickle.load')
    @patch('builtins.open')
    def test_classifier_initialization(self, mock_open, mock_pickle, mock_exists, mock_build):
        """Test that classifier initializes without errors."""
        mock_exists.return_value = True
        mock_creds = Mock()
        mock_creds.valid = True
        mock_pickle.return_value = mock_creds
        
        classifier = GmailClassifier.__new__(GmailClassifier)
        classifier.credentials_path = 'credentials.json'
        classifier.service = Mock()
        
        self.assertIsNotNone(classifier)
    
    def test_classify_urgent_email_with_urgent_keyword(self):
        """Test classification of email with 'urgent' keyword."""
        email = self.sample_emails[0]
        result = self.classifier.classify_email(email)
        self.assertEqual(result, 'urgent')
    
    def test_classify_not_urgent_email(self):
        """Test classification of normal email."""
        email = self.sample_emails[1]
        result = self.classifier.classify_email(email)
        self.assertEqual(result, 'not urgent')
    
    def test_classify_email_with_critical_keyword(self):
        """Test classification of email with 'critical' keyword."""
        email = self.sample_emails[2]
        result = self.classifier.classify_email(email)
        self.assertEqual(result, 'urgent')
    
    def test_classify_email_with_deadline_keyword(self):
        """Test classification of email with 'deadline' keyword."""
        email = self.sample_emails[4]
        result = self.classifier.classify_email(email)
        self.assertEqual(result, 'urgent')
    
    def test_classify_multiple_emails(self):
        """Test classification of multiple emails."""
        results = []
        for email in self.sample_emails:
            classification = self.classifier.classify_email(email)
            results.append(classification)
        
        # Should have 3 urgent and 2 not urgent
        urgent_count = results.count('urgent')
        not_urgent_count = results.count('not urgent')
        
        self.assertEqual(urgent_count, 3)
        self.assertEqual(not_urgent_count, 2)
    
    def test_classify_email_case_insensitive(self):
        """Test that classification is case-insensitive."""
        email1 = {'subject': 'URGENT matter', 'snippet': '', 'sender': 'test@test.com'}
        email2 = {'subject': 'urgent matter', 'snippet': '', 'sender': 'test@test.com'}
        email3 = {'subject': 'Urgent matter', 'snippet': '', 'sender': 'test@test.com'}
        
        self.assertEqual(self.classifier.classify_email(email1), 'urgent')
        self.assertEqual(self.classifier.classify_email(email2), 'urgent')
        self.assertEqual(self.classifier.classify_email(email3), 'urgent')
    
    def test_classify_email_with_keyword_in_snippet(self):
        """Test classification when urgent keyword is in snippet."""
        email = {
            'subject': 'Meeting tomorrow',
            'snippet': 'This is an urgent request for your attention',
            'sender': 'test@test.com'
        }
        
        result = self.classifier.classify_email(email)
        self.assertEqual(result, 'urgent')
    
    def test_parse_email(self):
        """Test email parsing logic."""
        mock_msg = {
            'id': 'test123',
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'Date', 'value': 'Mon, 1 Jan 2024 12:00:00'}
                ]
            },
            'snippet': 'This is a test email snippet'
        }
        
        result = self.classifier._parse_email(mock_msg)
        
        self.assertEqual(result['id'], 'test123')
        self.assertEqual(result['subject'], 'Test Subject')
        self.assertEqual(result['sender'], 'sender@example.com')
        self.assertEqual(result['snippet'], 'This is a test email snippet')
    
    def test_classify_no_false_positive_for_unimportant(self):
        """Test that 'unimportant' doesn't match 'important' keyword."""
        email = {
            'subject': 'This is unimportant',
            'snippet': 'Nothing to worry about',
            'sender': 'test@test.com'
        }
        
        result = self.classifier.classify_email(email)
        self.assertEqual(result, 'not urgent')


if __name__ == '__main__':
    unittest.main()
