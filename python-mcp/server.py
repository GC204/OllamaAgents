from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from pathlib import Path
import requests
import json
from flask import Flask, jsonify, request
from ddgs import DDGS
import time
import asyncio

mcp = FastMCP(
    name="Demo MCP Server",
    dependencies=["pillow"]
)

app = Flask(__name__)

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two integers and return the sum."""
    return a + b

@mcp.tool()
def search_wiki(query: str) -> str:
    """Search Wikipedia for a query and return the summary."""
    url = 'https://en.wikipedia.org/w/rest.php/v1/search/page'
    headers = {
    	'User-Agent': 'MediaWiki REST API docs examples/0.1 (https://www.mediawiki.org/wiki/API_talk:REST_API)'
    }
    params = {
    	'q': query,
    	'limit': '10'
	}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    return json.dumps(data, indent=2)

@mcp.tool()
def google_search(query: str, num_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo and return results.
    Returns the top search results with title, URL, and snippet.
    """
    results = []
    try:
        with DDGS() as ddgs:
            search_results = ddgs.text(query, max_results=num_results)
            
            for i, result in enumerate(search_results, 1):
                results.append({
                    "rank": i,
                    "title": result.get('title', 'No title'),
                    "url": result.get('href', ''),
                    "snippet": result.get('body', 'No snippet')[:200]
                })
        
        if not results:
            return json.dumps({
                "query": query,
                "num_results": 0,
                "results": [],
                "message": "No results found"
            }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "message": "Failed to perform web search"
        }, indent=2)
    
    return json.dumps({
        "query": query,
        "num_results": len(results),
        "results": results,
        "source": "DuckDuckGo"
    }, indent=2)

# HTTP Endpoints for REST API access
@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "MCP Server"})

@app.route('/api/tools', methods=['GET'])
def list_tools():
    """List all available tools"""
    return jsonify({
        "tools": [
            {
                "name": "add_numbers",
                "description": "Add two integers and return the sum.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "integer", "description": "First number"},
                        "b": {"type": "integer", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "search_wiki",
                "description": "Search Wikipedia for a query and return the summary.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "google_search",
                "description": "Search Google and scrape search results using Playwright.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "num_results": {"type": "integer", "description": "Number of results to return (default: 5)"}
                    },
                    "required": ["query"]
                }
            }
        ]
    })

@app.route('/api/search-wiki', methods=['POST'])
def api_search_wiki():
    """Search Wikipedia via HTTP endpoint"""
    data = request.get_json()
    query = data.get('query')
    
    if not query:
        return jsonify({"error": "query parameter is required"}), 400
    
    try:
        result = search_wiki(query)
        return jsonify({"data": json.loads(result)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/google-search', methods=['POST'])
def api_google_search():
    """Search Google via HTTP endpoint"""
    data = request.get_json()
    query = data.get('query')
    num_results = data.get('num_results', 5)
    
    if not query:
        return jsonify({"error": "query parameter is required"}), 400
    
    try:
        result = google_search(query, int(num_results))
        return jsonify(json.loads(result))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/add-numbers', methods=['POST'])
def api_add_numbers():
    """Add two numbers via HTTP endpoint"""
    data = request.get_json()
    a = data.get('a')
    b = data.get('b')
    
    if a is None or b is None:
        return jsonify({"error": "a and b parameters are required"}), 400
    
    try:
        result = add_numbers(int(a), int(b))
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Run Flask app on port 5000
    app.run(host='0.0.0.0', port=5000, debug=False)

    
        