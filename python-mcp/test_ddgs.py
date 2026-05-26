#!/usr/bin/env python3
import json
from ddgs import DDGS

print("Testing DuckDuckGo search directly...")

try:
    with DDGS() as ddgs:
        results = ddgs.text("Python", max_results=5)
        print(f"Found {len(list(results))} results")
        
        # Reset and get results again
        results = ddgs.text("Python", max_results=5)
        for i, r in enumerate(results, 1):
            print(f"\n{i}. {r.get('title', 'No title')}")
            print(f"   URL: {r.get('href', 'No URL')}")
            print(f"   Snippet: {r.get('body', 'No snippet')[:100]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
