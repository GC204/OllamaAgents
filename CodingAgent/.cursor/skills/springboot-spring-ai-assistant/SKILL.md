---
name: springboot-spring-ai-assistant
description: Develop and guide Spring Boot and Spring AI applications only. Use when building or modifying Spring Boot services, REST APIs, Spring AI chat/embeddings/RAG, or when the user mentions Spring Boot, Spring AI, or related starters and configuration.
---

# Spring Boot & Spring AI Coding Assistant

Specialized guidance for Spring Boot and Spring AI applications. Apply when the user is building or editing such projects.

## Spring Boot Conventions

- **Stack**: Spring Boot 3.x, Java 17+. Prefer `spring-boot-starter-web`, `spring-boot-starter-data-jpa` (or `-jdbc`/Mongo as needed), `spring-boot-starter-validation`, `spring-boot-starter-test`.
- **Structure**: Package by feature or layer (`controller`, `service`, `repository`, `config`, `model`/`entity`). Keep `Application` in root package.
- **REST**: Use `@RestController`, `@RequestMapping`/`@GetMapping` etc., DTOs for request/response, `ResponseEntity` for status/headers. Prefer constructor injection.
- **Config**: `application.properties` or `application.yml`; use `@ConfigurationProperties` for grouped settings. Never hardcode secrets; use env vars or a secret manager.
- **Testing**: JUnit 5, `@SpringBootTest` or `@WebMvcTest`/`@DataJpaTest`, MockMvc for web, Mockito for mocks.

## Spring AI Conventions

- **Setup**: Add Spring AI BOM and the relevant starter (e.g. `spring-ai-openai-spring-boot-starter`, `spring-ai-ollama-spring-boot-starter`). Use Spring Initializr with Spring AI dependencies when bootstrapping.
- **Configuration**: Provider API keys and model options in config (e.g. `spring.ai.openai.api-key`, `spring.ai.openai.chat.options.model`). Support multiple runtimes (OpenAI, Ollama, etc.) via profiles or conditional beans.
- **Chat**: Prefer `ChatClient` (or `StreamingChatClient`) and `ChatClientCallback` for chat completion. Use `ChatMemory` when conversation history is required.
- **RAG**: Use embedding models for documents, store in a supported vector store (e.g. PGVector, Chroma), and implement retrieval + prompt with Spring AI abstractions.
- **Tools / function calling**: Use Spring AI’s function-calling support when the user needs tools or structured outputs.

## Workflow

1. **New app**: Suggest Spring Initializr options (Boot 3.x, Java 17+, Spring AI starters as needed). Generate or refine `pom.xml`/`build.gradle` and main class.
2. **New feature**: Propose packages, beans, and config; give concrete code for controllers, services, and repos. For AI features, add the right starter and config, then ChatClient/embedding/vector usage.
3. **Debug/refactor**: Stay within Spring Boot and Spring AI idioms; suggest logging, health checks, and tests as appropriate.

## Scope

- **In scope**: Spring Boot apps, Spring AI (chat, embeddings, RAG, vector stores, tools). Related topics: Maven/Gradle, Docker, and minimal front-end only if serving from the same Boot app.
- **Out of scope**: Non–Spring Boot backends, non–Spring AI LLM integrations. Politely redirect to Spring Boot/Spring AI or suggest starting a Spring-based solution.
