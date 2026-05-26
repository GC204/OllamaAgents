#!/usr/bin/env python3
import requests
import json

base_url = "http://localhost:5000/api"

print("Searching for: Narendra Modi")
print("=" * 70)

payload = {
    "query": "Narendra Modi",
    "num_results": 5
}

try:
    response = requests.post(f"{base_url}/google-search", json=payload, timeout=30)
    result = response.json()
    
    if result.get('num_results', 0) > 0:
        print(f"\nFound {result['num_results']} results:\n")
        for item in result['results']:
            print(f"Rank {item['rank']}: {item['title']}")
            print(f"URL: {item['url']}")
            print(f"Snippet: {item['snippet']}")
            print()
    else:
        print("No results found.")
        
except Exception as e:
    print(f"Error: {str(e)}")
