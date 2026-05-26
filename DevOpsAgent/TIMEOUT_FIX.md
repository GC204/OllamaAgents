# Ollama Timeout Error - Fix Summary

## Problem
The application was experiencing timeout errors when trying to get AI responses from the Ollama LLM server:
```
2026-04-12 21:35:10,845 - llm.ollama_client - ERROR - Ollama request timed out
```

This resulted in HTTP 500 Internal Server Errors when calling `/api/sessions/{session_id}/ai-response`.

## Root Cause
1. **Excessive timeout value**: The original timeout was set to 300 seconds (5 minutes), which is too long and could cause client/server hangs
2. **No retry logic**: When a timeout occurred, the request would fail immediately without retry
3. **Poor error messaging**: Users received a generic 500 error instead of a specific timeout message

## Solution Implemented

### 1. **Configurable Timeouts** (in `.env`)
Added timeout settings that can be adjusted without restarting:
```env
OLLAMA_GENERATE_TIMEOUT=60          # 60 seconds for generation requests
OLLAMA_PULL_TIMEOUT=300             # 5 minutes for model pulls
OLLAMA_CHECK_TIMEOUT=5              # 5 seconds for availability checks
OLLAMA_MAX_RETRIES=2                # Retry up to 2 times on timeout/connection errors
```

### 2. **Exponential Backoff Retry Logic**
- Automatically retries failed requests with exponential backoff: 1s → 2s → 4s
- Only retries on temporary errors (timeout, connection issues)
- Gives up immediately on permanent errors (e.g., invalid model)

### 3. **Better Error Handling**
- Changed HTTP status code from 500 → 504 (Gateway Timeout) for timeout errors
- Returns specific error messages to the client:
  ```json
  {
    "detail": "LLM request timed out. Please try again. (Timeout limit: 60s)"
  }
  ```

### 4. **Enhanced Logging**
- Logs each retry attempt with attempt number and timeout value
- Logs the final error after all retries fail
- Provides better debugging information for troubleshooting

## Files Modified

1. **backend/config/settings.py**
   - Added timeout configuration options
   - Moved timeout from hardcoded to configurable

2. **backend/llm/ollama_client.py**
   - Constructor now accepts timeout parameters
   - Added retry logic with exponential backoff to `generate()` and `generate_stream()`
   - Updated all methods to use configurable timeouts

3. **backend/routes/chat.py**
   - Updated OllamaClient initialization with timeout settings
   - Changed error response to 504 with descriptive message
   - Improved error logging

4. **.env**
   - Added new timeout configuration variables

## Troubleshooting Guide

### If you still get timeouts:

1. **Check Ollama is running**
   ```bash
   curl http://localhost:11434/api/tags
   ```
   If this fails, Ollama isn't running.

2. **Check model is loaded**
   - Look for the model in Ollama UI or run: `ollama list`
   - If not loaded, it will auto-pull with a 5-minute timeout

3. **Increase timeout if needed** (for slower systems)
   ```env
   OLLAMA_GENERATE_TIMEOUT=120  # Increase to 2 minutes
   OLLAMA_MAX_RETRIES=3         # More retries
   ```

4. **Check system resources**
   - Ollama needs sufficient RAM/GPU memory for the model
   - Run `ollama show <model-name>` to see requirements

5. **Enable debug logging**
   ```env
   DEBUG=True
   ```
   Look for detailed logs in the console showing timeout/retry attempts

### Expected behavior:
- Request times out after 60 seconds (default)
- Automatically retries up to 2 times with delays
- Total time: ~60 + 1 + 2 = 63 seconds max
- Returns clear error message if all retries fail

## Configuration Examples

### For fast responses (aggressive):
```env
OLLAMA_GENERATE_TIMEOUT=30
OLLAMA_MAX_RETRIES=1
```

### For slow systems (patient):
```env
OLLAMA_GENERATE_TIMEOUT=180
OLLAMA_MAX_RETRIES=3
```

### For production (balanced):
```env
OLLAMA_GENERATE_TIMEOUT=90
OLLAMA_MAX_RETRIES=2
```

## Testing the Fix

```bash
# 1. Start backend with new settings
cd backend
python -m uvicorn app:app --reload

# 2. Create a session
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"repo_name": "test/repo", "release_branch": "main"}'

# 3. Send a chat message
curl -X POST http://localhost:8000/api/sessions/{session_id}/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "What should I test?"}'

# 4. Get AI response (should now handle timeouts gracefully)
curl -X POST http://localhost:8000/api/sessions/{session_id}/ai-response \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello, can you help?"}'
```

## Performance Notes

- **First request**: May be slower if model isn't loaded (~30-60s depending on model size)
- **Subsequent requests**: Should be faster (~5-10s) as model stays in memory
- **Retries**: Only happen if initial request times out or fails, most requests complete on first try
