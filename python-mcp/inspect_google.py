#!/usr/bin/env python3
"""
Quick diagnostic script to inspect Google search page structure
"""
from playwright.sync_api import sync_playwright
import json

query = "Python programming"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.set_extra_http_headers({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    search_url = f"https://www.google.com/search?q={query}"
    print(f"Loading: {search_url}")
    page.goto(search_url, wait_until="networkidle")
    
    print("Page loaded. Let me find results...")
    
    # Try different selectors
    selectors_to_try = [
        'div[data-sokoban-container]',
        'div.Gx5Zad',
        'div.g',
        'a[href*="/url?q="]',
        'h3',
        'div[data-type="searchResult"]'
    ]
    
    for selector in selectors_to_try:
        try:
            elements = page.query_selector_all(selector)
            print(f"✓ Selector '{selector}': Found {len(elements)} elements")
        except:
            print(f"✗ Selector '{selector}': No elements found")
    
    # Get page content snippet
    content = page.content()
    print(f"\n=== Page Content (first 2000 chars) ===")
    print(content[:2000])
    print("\n=== Looking for result patterns ===")
    if 'data-sokoban' in content:
        print("✓ Found 'data-sokoban' in page content")
    if 'Gx5Zad' in content:
        print("✓ Found 'Gx5Zad' class in page content")
    if 'class="g"' in content:
        print("✓ Found 'class=\"g\"' in page content")
    
    browser.close()
