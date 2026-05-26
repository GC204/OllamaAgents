package com.example.ollamachat.service;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.prompt.ChatOptions;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

@Service
public class ChatService {

    private final ChatClient chatClient;
    private final String primaryModel;
    private final String fallbackModel;

    public ChatService(
            ChatClient.Builder chatClientBuilder,
            @Value("${app.ai.primary-model:gemma4:31b-cloud}") String primaryModel,
            @Value("${app.ai.fallback-model:llama3.2}") String fallbackModel) {
        this.chatClient = chatClientBuilder.build();
        this.primaryModel = primaryModel;
        this.fallbackModel = fallbackModel;
    }

    public String chat(String userMessage) {
        try {
            return callWithModel(userMessage, primaryModel);
        } catch (Exception primaryFailure) {
            return callWithModel(userMessage, fallbackModel);
        }
    }

    public Flux<String> streamChat(String userMessage) {
        return streamWithModel(userMessage, primaryModel)
                .onErrorResume(primaryFailure -> streamWithModel(userMessage, fallbackModel));
    }

    private String callWithModel(String userMessage, String model) {
        return chatClient.prompt()
                .user(userMessage)
                .options(ChatOptions.builder().model(model).build())
                .call()
                .content();
    }

    private Flux<String> streamWithModel(String userMessage, String model) {
        return chatClient.prompt()
                .user(userMessage)
                .options(ChatOptions.builder().model(model).build())
                .stream()
                .content();
    }
}
