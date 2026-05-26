package com.example.ollamachat.controller;

import com.example.ollamachat.service.ChatService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.Map;

@RestController
@RequestMapping("/chat")
public class ChatController {

    private final ChatService chatService;

    public ChatController(ChatService chatService) {
        this.chatService = chatService;
    }

    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
    public Map<String, String> chat(@RequestBody Map<String,String> request) {
        String message = request.getOrDefault("message", "");
        String response = chatService.chat(message);
        return Map.of("response", response);
    }

    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamChat(@RequestParam("message") String message) {
        SseEmitter emitter = new SseEmitter(0L);

        chatService.streamChat(message).subscribe(
                token -> sendEvent(emitter, "token", token),
                error -> {
                    sendEvent(emitter, "error", "Failed to generate response");
                    emitter.completeWithError(error);
                },
                () -> {
                    sendEvent(emitter, "done", "complete");
                    emitter.complete();
                }
        );

        return emitter;
    }

    private void sendEvent(SseEmitter emitter, String eventName, String data) {
        try {
            emitter.send(SseEmitter.event().name(eventName).data(data));
        } catch (IOException sendError) {
            emitter.completeWithError(sendError);
        }
    }
}
