#!/usr/bin/env python3
import requests
import json

base_url = "http://localhost:5000/api"

print("Testing Multiple Queries...")
print("=" * 60)

queries = [
    {"query": "machine learning", "num_results": 2},
    {"query": "web development", "num_results": 3},
    {"query": "artificial intelligence", "num_results": 2}
]

for payload in queries:
    try:
        response = requests.post(f"{base_url}/google-search", json=payload, timeout=30)
        result = response.json()
        
        print(f"\n✓ Query: '{payload['query']}' - Found {result.get('num_results', 0)} results")
        for item in result.get('results', []):
            print(f"  {item['rank']}. {item['title']}")
    except Exception as e:
        print(f"✗ Error with '{payload['query']}': {str(e)}")

print("\n" + "=" * 60)
print("All tests completed!")
