package com.example.aiagent;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import reactor.core.publisher.Flux;

import org.springframework.http.MediaType;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@RestController
public class AgentController {
    private static final Logger logger = LoggerFactory.getLogger(AgentController.class);

    private final AgentService agentService;

    public AgentController(AgentService agentService) {
        this.agentService = agentService;
    }

    @GetMapping("/ai/chat")
    public Flux<String> chat(@RequestParam(value = "message") String message) {
        return agentService.chat(message);
    }

    @GetMapping(value = "/ai/chat-stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter chatStream(@RequestParam(value = "message") String message) {
        SseEmitter emitter = new SseEmitter(60000L); // 60 second timeout
        
        Thread thread = new Thread(() -> {
            try {
                agentService.chatStreaming(message, emitter);
                emitter.complete();
            } catch (Exception e) {
                logger.error("Error in streaming response", e);
                try {
                    emitter.completeWithError(e);
                } catch (Exception ex) {
                    logger.error("Error completing emitter", ex);
                }
            }
        });
        thread.start();
        
        return emitter;
    }
}
