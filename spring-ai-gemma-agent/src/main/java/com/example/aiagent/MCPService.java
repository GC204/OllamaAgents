package com.example.aiagent;

import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpEntity;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.beans.factory.annotation.Value;
import java.util.HashMap;
import java.util.Map;

@Service
public class MCPService {
    private static final Logger logger = LoggerFactory.getLogger(MCPService.class);
    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();
    
    @Value("${mcp.url:http://127.0.0.1:5000}")
    private String mcpUrl;
    
    @Value("${mcp.auth-token:33afbd33fae662d71b5024cc19348c56cfa3b6dae5a16c389b3015aaabbb6f10}")
    private String mcpAuthToken;
    
    @Value("${mcp.tool-name:search_wiki}")
    private String toolName;

    public String searchWikipedia(String query) {
        logger.info("🌐 Calling Flask Wikipedia search for: {}", query);
        
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("User-Agent", "Spring-AI-MCP-Client/1.0");
            headers.set("Accept", "application/json");
            
            // Build request body for Flask API
            Map<String, String> requestBody = new HashMap<>();
            requestBody.put("query", cleaString(query));
            
            String requestJson = objectMapper.writeValueAsString(requestBody);
            logger.info("📤 Request body: {}", requestJson);
            HttpEntity<String> entity = new HttpEntity<>(requestJson, headers);
            
            // Call Flask endpoint instead of MCP JSON-RPC
            String flaskEndpoint = mcpUrl + "/api/google-search";
            logger.info("📤 Sending request to Flask API: {}", flaskEndpoint);
            ResponseEntity<String> response = restTemplate.postForEntity(flaskEndpoint, entity, String.class);
            
            String responseBody = response.getBody();
            logger.info("📥 Response status: {}", response.getStatusCode());
            logger.info("📥 Response body: {}", responseBody);
            
            // Check if response is HTML (error page)
            if (responseBody != null && responseBody.trim().startsWith("<")) {
                logger.error("❌ Flask API returned HTML instead of JSON. This usually indicates an error on the Flask server.");
                logger.debug("HTML Response: {}", responseBody.substring(0, Math.min(500, responseBody.length())));
                return "Error: Flask API server returned an error page";
            }
            
            if (response.getStatusCode().is2xxSuccessful() && responseBody != null) {
                try {
                    JsonNode jsonResponse = objectMapper.readTree(responseBody);
                    
                    // Handle Flask API response format
                    // Check for common response fields
                    if (jsonResponse.has("result")) {
                        String content = jsonResponse.get("result").asText();
                        logger.info("✅ Successfully retrieved results from Flask API");
                        return content;
                    } else if (jsonResponse.has("content")) {
                        String content = jsonResponse.get("content").asText();
                        logger.info("✅ Successfully retrieved results from Flask API");
                        return content;
                    } else if (jsonResponse.has("data")) {
                        JsonNode data = jsonResponse.get("data");
                        if (data.has("pages")) {
                            JsonNode pages = data.get("pages");
                            if (pages.isArray() && pages.size() > 0) {
                                String formattedResults = formatSearchResults(pages);
                                logger.info("✅ Successfully formatted search results from Flask API");
                                return formattedResults;
                            } else if (pages.isArray() && pages.size() == 0) {
                                logger.warn("⚠️  Flask API returned empty pages array for query: {}", query);
                                return "No results found for: " + query;
                            }
                        }
                        String content = data.isTextual() ? data.asText() : data.toString();
                        logger.info("✅ Successfully retrieved results from Flask API");
                        return content;
                    }
                    
                    // If error in response
                    if (jsonResponse.has("error")) {
                        String error = jsonResponse.get("error").asText();
                        logger.error("❌ Flask API returned error: {}", error);
                        return "Error from Flask API: " + error;
                    }
                    
                    // Return the entire response if it's valid JSON
                    logger.info("✅ Retrieved response from Flask API");
                    return responseBody;
                } catch (Exception e) {
                    logger.error("❌ Failed to parse Flask API response as JSON: {}", e.getMessage());
                    return "Error: Invalid JSON response from Flask API";
                }
            } else {
                logger.error("❌ Flask API call failed with status: {}", response.getStatusCode());
                return "Error: Flask API search failed with status " + response.getStatusCode();
            }
            
        } catch (Exception e) {
            logger.error("❌ Error calling MCP service: {}", e.getMessage(), e);
            return "Error occurred while searching via MCP: " + e.getMessage();
        }
    }

    private String formatSearchResults(JsonNode pages) {
        StringBuilder formatted = new StringBuilder();
        formatted.append("SEARCH RESULTS:\n\n");
        
        int count = 0;
        for (JsonNode page : pages) {
            if (count >= 5) break; // Limit to top 5 results
            
            String title = page.has("title") ? page.get("title").asText() : "Unknown";
            String description = page.has("description") ? page.get("description").asText() : "";
            String excerpt = page.has("excerpt") ? page.get("excerpt").asText() : "";
            
            // Remove HTML tags from excerpt
            excerpt = excerpt.replaceAll("<[^>]*>", "");
            
            formatted.append(count + 1).append(". ").append(title).append("\n");
            if (!description.isEmpty()) {
                formatted.append("   Description: ").append(description).append("\n");
            }
            if (!excerpt.isEmpty()) {
                formatted.append("   ").append(excerpt).append("\n");
            }
            formatted.append("\n");
            
            count++;
        }
        
        return formatted.toString();
    }

    private String cleaString(String query){
        query = query.replaceAll("[^a-zA-Z0-9\\s]", "");
        query = query.replaceAll("\\s+", " ").trim();
        return query;
    }
}
