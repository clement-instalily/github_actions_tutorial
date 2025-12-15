#!/usr/bin/env python3
"""
Test script for Email Insight Engine API
Demonstrates how to use the API endpoints
"""

import requests
import json
from datetime import datetime


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(title)
    print("="*60)


def test_health_check(base_url):
    """Test the health check endpoint"""
    print_section("1. Testing Health Check Endpoint")

    try:
        response = requests.get(f"{base_url}/health")
        response.raise_for_status()

        data = response.json()
        print(f"✓ Status: {data['status']}")
        print(f"✓ Message: {data['message']}")
        print(f"✓ Timestamp: {data['timestamp']}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        return False


def test_get_categories(base_url):
    """Test the categories endpoint"""
    print_section("2. Testing Get Categories Endpoint")

    try:
        response = requests.get(f"{base_url}/categories")
        response.raise_for_status()

        data = response.json()
        print(f"✓ Available categories:")
        for category, description in data['categories'].items():
            print(f"   - {category}: {description}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        return False


def test_analyze_emails(base_url, payload):
    """Test the analyze emails endpoint"""
    print_section("3. Testing Analyze Emails Endpoint")

    print(f"Request payload:")
    print(json.dumps(payload, indent=2))
    print("\nSending request... (this may take a while)")

    try:
        response = requests.post(
            f"{base_url}/analyze",
            json=payload,
            timeout=300  # 5 minute timeout
        )
        response.raise_for_status()

        data = response.json()

        print(f"\n✓ Status: {data['status']}")
        print(f"✓ Message: {data['message']}")
        print(f"✓ Timestamp: {data['timestamp']}")

        print(f"\nSummary:")
        for category, count in data['summary'].items():
            print(f"   - {category}: {count} emails")

        # Show sample results for categories with emails
        print(f"\nSample Results:")
        for category, emails in data['results'].items():
            if emails and len(emails) > 0:
                print(f"\n   {category} (showing first email):")
                email = emails[0]
                print(f"      From: {email.get('sender_name', 'N/A')} <{email.get('from_address', 'N/A')}>")
                print(f"      Date: {email.get('date_sent', 'N/A')}")
                summary = email.get('summary', 'N/A')
                if len(summary) > 100:
                    summary = summary[:100] + "..."
                print(f"      Summary: {summary}")

        return True
    except requests.exceptions.Timeout:
        print(f"✗ Error: Request timed out after 5 minutes")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return False


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("EMAIL INSIGHT ENGINE API - TEST SCRIPT")
    print("="*60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Configuration
    BASE_URL = "http://localhost:8000"

    # Test payload for analyze endpoint
    # Using minimal configuration - will use env vars for credentials
    test_payload = {
        "days_back": 3,  # Analyze last 3 days (faster for testing)
        "batch_size": 5,  # Smaller batch size
        "folders": ["INBOX"],  # Only analyze INBOX
        "confidence_threshold": 0.6,
        "max_retries": 3
    }

    print(f"\nAPI Base URL: {BASE_URL}")
    print(f"Note: Make sure the API is running before executing these tests")
    print(f"      Start the API with: python app/api.py")

    # Run tests
    results = []

    # Test 1: Health Check
    results.append(test_health_check(BASE_URL))

    # Test 2: Get Categories
    results.append(test_get_categories(BASE_URL))

    # Test 3: Analyze Emails
    # Ask user if they want to run the full analysis
    print_section("3. Analyze Emails Test")
    response = input("\nThis will analyze your emails. Continue? (y/n): ")

    if response.lower() == 'y':
        results.append(test_analyze_emails(BASE_URL, test_payload))
    else:
        print("Skipping email analysis test.")
        results.append(None)

    # Print summary
    print_section("Test Summary")
    test_names = ["Health Check", "Get Categories", "Analyze Emails"]

    for i, (name, result) in enumerate(zip(test_names, results), 1):
        if result is None:
            status = "⊘ SKIPPED"
        elif result:
            status = "✓ PASSED"
        else:
            status = "✗ FAILED"
        print(f"{i}. {name}: {status}")

    passed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is False)
    skipped = sum(1 for r in results if r is None)

    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped")
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
