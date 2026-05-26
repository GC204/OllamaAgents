# Spring AI Chat with Ollama

A minimal Spring Boot application that uses **Spring AI** and **Ollama** for chat completion.

## Prerequisites

1. **Ollama** installed and running locally ([ollama.com](https://ollama.com)).
2. At least one model pulled, e.g.:
   ```bash
   ollama pull llama3.2
   ```
3. **Java 21** and **Maven**.

## Configuration

- **Ollama URL**: `http://localhost:11434` (override with `spring.ai.ollama.base-url`).
- **Model**: `llama3.2` (override in `application.yml` under `spring.ai.ollama.chat.options.model`).

## Run

```bash
cd app
mvn spring-boot:run
```

## API

**POST** `/chat`

- **Request body (JSON):** `{ "message": "Your question or prompt" }`
- **Response (JSON):** `{ "response": "Model reply text" }`

Example with curl:

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What is Spring Boot?\"}"
```

## Project layout

- `ChatController` – REST endpoint for `/chat`.
- `ChatService` – Uses Spring AI `ChatClient` (Ollama-backed) to call the model.
- `application.yml` – Ollama base URL and chat model name.
