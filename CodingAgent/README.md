# CodingAgent — Spring Boot & Spring AI Assistant

This workspace is configured so the AI acts as a **coding assistant specialized in Spring Boot and Spring AI** only.

## What’s configured

- **Cursor rule** (`.cursor/rules/springboot-specialist.mdc`)  
  Always-on rule in this project: the assistant behaves as a Spring Boot and Spring AI specialist and stays within that scope.

- **Cursor skill** (`.cursor/skills/springboot-spring-ai-assistant/`)  
  Skill the agent can use when you’re building or editing Spring Boot or Spring AI apps. It provides conventions for:
  - Spring Boot: structure, REST, config, testing
  - Spring AI: ChatClient, embeddings, RAG, vector stores, configuration

## How to use

1. Open this folder in Cursor.
2. Ask for help with Spring Boot or Spring AI (e.g. “Create a Spring Boot REST API for …”, “Add Spring AI chat with Ollama”, “Set up RAG with embeddings”).
3. The assistant will follow Spring Boot and Spring AI conventions and will redirect if you ask for something outside that scope.

## Starting a new app

- Use [Spring Initializr](https://start.spring.io/) with **Spring Boot 3.x** and, for AI features, add the **Spring AI** dependencies (e.g. OpenAI or Ollama).
- You can also ask the assistant to propose a `pom.xml` or `build.gradle` and a basic project layout.
