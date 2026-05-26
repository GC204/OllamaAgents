#!/usr/bin/env python3
import json
import subprocess
import sys
import time

# Start the server process
server_process = subprocess.Popen(
    [sys.executable, 'server.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

msg_id = 0

def send_request(method, **kwargs):
    """Send a JSON-RPC request to the server"""
    global msg_id
    msg_id += 1
    request = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "method": method,
        **kwargs
    }
    request_str = json.dumps(request)
    print(f">>> Sending: {request_str}", file=sys.stderr)
    server_process.stdin.write(request_str + '\n')
    server_process.stdin.flush()
    
    # Read response
    time.sleep(0.5)  # Give server time to respond
    response_line = server_process.stdout.readline()
    if response_line:
        print(f"<<< Received: {response_line.strip()}", file=sys.stderr)
        return json.loads(response_line)
    return None

# Initialize the client
print("Step 1: Initializing client...", file=sys.stderr)
init_response = send_request(
    "initialize",
    params={
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    }
)
print("\nInitialization Response:")
print(json.dumps(init_response, indent=2))

# Test: List tools
print("\nStep 2: Listing available tools...", file=sys.stderr)
tools_response = send_request("tools/list", params={})
print("\nTools List Response:")
print(json.dumps(tools_response, indent=2))

# Test: Call search_wiki tool
print("\nStep 3: Calling search_wiki tool...", file=sys.stderr)
wiki_response = send_request(
    "tools/call",
    params={
        "name": "search_wiki",
        "arguments": {
            "query": "Python"
        }
    }
)
print("\nSearch Wiki Response:")
print(json.dumps(wiki_response, indent=2))

# Close server
print("\nClosing server...", file=sys.stderr)
server_process.terminate()
server_process.wait(timeout=5)
