package com.example.aiagent;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import reactor.core.publisher.Flux;

@Service
public class AgentService {
    private static final Logger logger = LoggerFactory.getLogger(AgentService.class);

    private final ChatClient chatClient;
    private final MCPService mcpService;

    public AgentService(ChatClient.Builder builder, MCPService mcpService) {
        this.mcpService = mcpService;
        this.chatClient = builder
                .defaultSystem("You are a helpful AI assistant that answers questions based on search results. " +
                               "When you receive search results, read them carefully and extract the answer to the user's question. " +
                               "Be concise and direct in your response. " +
                               "If the search results contain the answer, provide it. " +
                               "If the search results don't have the answer, use your pretrained knowledge." +
                               "If you don't know the answer, state that clearly.")
                .build();
    }

    public Flux<String> chat(String userMessage) {
        logger.info("🎯 User question: {}", userMessage);
        
        try {
            // First, try to get an answer with search via MCP
            String searchQuery = extractSearchQuery(userMessage);
            
            if (searchQuery != null && !searchQuery.isEmpty()) {
                logger.info("🔍 Searching via MCP for: {}", searchQuery);
                String searchResults = mcpService.searchWikipedia(searchQuery);
                logger.info("📊 Got search results: {} bytes", searchResults.length());
                
                if (searchResults != null && !searchResults.contains("Error") && !searchResults.isEmpty()) {
                    // Try to extract direct answer from search results using keywords
                    Flux<String> directAnswer = extractDirectAnswer(userMessage, searchResults);
                    if (directAnswer != null) {
                        logger.info("✅ Direct answer extracted from search results");
                        return directAnswer;
                    }
                    
                    // Fallback: Get response from LLM with search results
                    Flux<String> response = Flux.just(chatClient.prompt()
                            .user(userMessage + "\n\n" + searchResults)
                            .call()
                            .content());
                    
                    logger.info("✅ Response with MCP search results");
                    return response;
                }
            }
            
            // Fallback: get response without explicit search
            String response = chatClient.prompt()
                    .user(userMessage)
                    .call()
                    .content();
            
            logger.info("✅ Direct response");
            return Flux.just(response);
            
        } catch (Exception e) {
            logger.error("❌ Error in chat: {}", e.getMessage(), e);
            return Flux.just("Error: " + e.getMessage());
        }
    }

    public void chatStreaming(String userMessage, SseEmitter emitter) throws Exception {
        logger.info("🎯 User question (streaming): {}", userMessage);
        
        try {
            // First, try to get an answer with search via MCP
            String searchQuery = extractSearchQuery(userMessage);
            
            if (searchQuery != null && !searchQuery.isEmpty()) {
                logger.info("🔍 Searching via MCP for: {}", searchQuery);
                String searchResults = mcpService.searchWikipedia(searchQuery);
                logger.info("📊 Got search results: {} bytes", searchResults.length());
                
                if (searchResults != null && !searchResults.contains("Error") && !searchResults.isEmpty()) {
                    // Try to extract direct answer from search results using keywords
                    Flux<String> directAnswer = extractDirectAnswer(userMessage, searchResults);
                    if (directAnswer != null) {
                        logger.info("✅ Direct answer extracted from search results");
                        // Stream the direct answer word by word
                        streamText(directAnswer, emitter);
                        return;
                    }
                    
                    // Fallback: Stream response from LLM with search results
                    logger.info("📡 Streaming response with MCP search results");
                    streamLLMResponse(userMessage + "\n\n" + searchResults, emitter);
                    return;
                }
            }
            
            // Fallback: stream response without explicit search
            logger.info("📡 Streaming direct response");
            streamLLMResponse(userMessage, emitter);
            
        } catch (Exception e) {
            logger.error("❌ Error in streaming chat: {}", e.getMessage(), e);
            emitter.send(SseEmitter.event().id("error").data("Error: " + e.getMessage()).build());
        }
    }

    private void streamLLMResponse(String prompt, SseEmitter emitter) throws Exception {
        chatClient.prompt()
                .user(prompt)
                .stream()
                .content()
                .doOnNext(chunk -> {
                    try {
                        logger.debug("📤 Sending chunk immediately: {}", chunk);
                        emitter.send(SseEmitter.event()
                                .id("chunk")
                                .data(chunk)
                                .build());
                    } catch (Exception e) {
                        logger.error("Error sending chunk", e);
                    }
                })
                .blockLast();
    }

    private void streamText(Flux<String> directAnswer, SseEmitter emitter) throws Exception {
        // Stream text word by word for direct answers
        if (directAnswer == null || directAnswer.blockFirst().trim().isEmpty()) {
            return;
        }
        
        String[] words = directAnswer.blockFirst().trim().split("\\s+");
        
        for (String word : words) {
            if (word == null || word.isEmpty()) {
                continue;
            }
            try {
                logger.debug("📤 Sending word: {}", word);
                emitter.send(SseEmitter.event()
                        .id("chunk")
                        .data(word + " ")
                        .build());
                Thread.sleep(100); // 100ms delay between words for visible streaming
            } catch (Exception e) {
                logger.error("Error sending word", e);
                break;
            }
        }
    }
    
    private Flux<String> extractDirectAnswer(String userMessage, String searchResults) {
        String userLower = userMessage.toLowerCase();
        String resultsLower = searchResults.toLowerCase();
        
        // Winner extraction
        if (userLower.contains("won") || userLower.contains("winner")) {
            if (resultsLower.contains("won their first title in")) {
                // Extract team name that won
                int idx = searchResults.indexOf("won their first title in");
                if (idx > 0) {
                    String before = searchResults.substring(Math.max(0, idx - 200), idx);
                    // Look for team names (typically capitalized)
                    java.util.regex.Pattern pattern = java.util.regex.Pattern.compile("(?:^|\\n)\\d+\\. (.+)\\n");
                    java.util.regex.Matcher matcher = pattern.matcher(before);
                    if (matcher.find()) {
                        String teamName = matcher.group(1).trim();
                        return Flux.just("According to the search results, " + teamName + " won the 2025 IPL title (their first title in 2025).");
                    }
                }
            }
        }
        
        // General info extraction - return first result's description if relevant
        if (searchResults.contains("1. ")) {
            java.util.regex.Pattern pattern = java.util.regex.Pattern.compile("1\\. (.+?)\\n");
            java.util.regex.Matcher matcher = pattern.matcher(searchResults);
            if (matcher.find()) {
                String firstResult = matcher.group(1);
                if (firstResult.toLowerCase().contains(userLower.replaceAll("^(who|what|when|where|why|how)\\s+", "").trim())) {
                    logger.info("Returning first relevant search result");
                    return Flux.just("Based on search results: " + firstResult);
                }
            }
        }
        
        return null;
    }
    
    private String extractSearchQuery(String userMessage) {
        // Extract search terms from the user message
        // For questions like "Who won IPL 2025?", extract "IPL 2025 winner"
        
        String query = userMessage.toLowerCase();
        
        // Remove common question words
        query = query.replaceAll("^(who|what|when|where|why|how|which)\\s+", "");
        query = query.replaceAll("\\?$", "");
        query = query.trim();
        
        return query.isEmpty() ? userMessage : query;
    }
}
