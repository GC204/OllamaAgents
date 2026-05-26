#!/usr/bin/env python3
import requests
import json

base_url = "http://localhost:5000/api"

print("Testing Google Search Endpoint...")
print("=" * 60)

payload = {
    "query": "Python programming",
    "num_results": 3
}

try:
    response = requests.post(f"{base_url}/google-search", json=payload, timeout=60)
    print(f"Status Code: {response.status_code}")
    print(f"\nResponse:")
    result = response.json()
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {str(e)}")
