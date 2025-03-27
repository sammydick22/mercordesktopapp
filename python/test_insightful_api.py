"""
Test script for Insightful-compatible API endpoints.

This script demonstrates how to use the Insightful-compatible API endpoints
with the Time Tracker app. These endpoints use your local database but
provide responses in Insightful's API format.

Usage:
    1. Make sure your Time Tracker API is running
    2. Run the script:
       python test_insightful_api.py
"""
import os
import sys
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables (for any other config)
load_dotenv()

# Set up API URL
API_BASE_URL = "http://localhost:8000"

# Get auth token from environment or use a default test token
AUTH_TOKEN = os.getenv('AUTH_TOKEN')
if not AUTH_TOKEN:
    print("Note: No AUTH_TOKEN found in .env file. You may need a valid auth token.")
    # You might want to login and get a token here
    # For now, we'll continue for demonstration purposes

# Helper function to make API requests
def call_api(endpoint, method='GET', params=None, data=None):
    """Make an API request to the local TimeTracker API."""
    url = f"{API_BASE_URL}{endpoint}"
    
    # Use auth token if available
    headers = {}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        if hasattr(e, 'response') and e.response:
            try:
                error_data = e.response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Status code: {e.response.status_code}")
                print(f"Response text: {e.response.text}")
        sys.exit(1)

def main():
    """Run tests for Insightful-compatible API endpoints."""
    print("Testing Insightful-Compatible API Endpoints\n")
    
    # Calculate time range (last 24 hours)
    end_time = int(datetime.now().timestamp() * 1000)  # Convert to milliseconds
    start_time = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
    
    # Example 1: Get screenshots
    print("Example 1: Get screenshots from the last 24 hours")
    params = {
        "start": start_time,
        "end": end_time,
        "limit": 5  # Limit to 5 results for demonstration
    }
    
    try:
        screenshots_response = call_api("/insightful/screenshots", params=params)
        if screenshots_response and 'data' in screenshots_response:
            screenshots = screenshots_response['data']
            print(f"Found {len(screenshots)} screenshots")
            print(f"Sample screenshot: {json.dumps(screenshots[0] if screenshots else {}, indent=2)}")
        else:
            print("No screenshots found in the specified time range")
    except Exception as e:
        print(f"Error fetching screenshots: {e}")
    
    print("\n" + "-" * 50 + "\n")
    
    # Example 2: Get time windows
    print("Example 2: Get time windows from the last 24 hours")
    
    try:
        time_windows = call_api("/insightful/time-windows", params=params)
        if time_windows:
            print(f"Found {len(time_windows)} time windows")
            print(f"Sample time window: {json.dumps(time_windows[0] if isinstance(time_windows, list) else time_windows, indent=2)}")
        else:
            print("No time windows found in the specified time range")
    except Exception as e:
        print(f"Error fetching time windows: {e}")
    
    print("\n" + "-" * 50 + "\n")
    
    # Example 3: Get project time
    print("Example 3: Get project time from the last 24 hours")
    
    try:
        project_time = call_api("/insightful/project-time", params=params)
        if project_time:
            print(f"Project time data: {json.dumps(project_time, indent=2)}")
        else:
            print("No project time data found in the specified time range")
    except Exception as e:
        print(f"Error fetching project time: {e}")
    
    print("\nTests completed.")

if __name__ == "__main__":
    main()
