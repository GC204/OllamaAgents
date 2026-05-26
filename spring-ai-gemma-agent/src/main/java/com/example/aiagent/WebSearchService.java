package com.example.aiagent;

import org.springframework.stereotype.Service;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.beans.factory.annotation.Autowired;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.List;

@Service
public class WebSearchService {
    private static final Logger logger = LoggerFactory.getLogger(WebSearchService.class);
    private final RestTemplate restTemplate = new RestTemplate();
    
    @Autowired
    private MCPService mcpService;

    public String search(String query) {
        logger.info("🔍 Searching for: {}", query);
        
        // Try MCP first (your Wikipedia search tool)
        try {
            String mcpResults = mcpService.searchWikipedia(query);
            if (mcpResults != null && !mcpResults.contains("Error")) {
                logger.info("✅ Using MCP results for query: {}", query);
                return mcpResults;
            }
        } catch (Exception e) {
            logger.warn("⚠️  MCP search failed, falling back to direct Wikipedia API: {}", e.getMessage());
        }
        
        // Fallback to direct Wikipedia REST API if MCP fails
        return fallbackWikipediaSearch(query);
    }

    private String fallbackWikipediaSearch(String query) {
        logger.info("Using fallback Wikipedia REST API for: {}", query);

        try {
            // Use Wikipedia REST API for search
            String encodedQuery = URLEncoder.encode(query, StandardCharsets.UTF_8);
            String wikiUrl = "https://en.wikipedia.org/w/rest.php/v1/search/page?q=" + 
                            encodedQuery + "&limit=5";
            
            logger.info("Calling Wikipedia REST API: {}", wikiUrl);
            
            // Create headers with User-Agent
            HttpHeaders headers = new HttpHeaders();
            headers.set("User-Agent", "Spring-AI-Agent/1.0 (Spring Boot Application; +https://github.com)");
            HttpEntity<String> entity = new HttpEntity<>(headers);
            
            ResponseEntity<Map> response = restTemplate.exchange(wikiUrl, HttpMethod.GET, entity, Map.class);
            Map<String, Object> responseBody = response.getBody();
            
            if (responseBody == null || !responseBody.containsKey("pages")) {
                logger.warn("Wikipedia API returned no response or missing pages");
                return "No search results found for: " + query;
            }
            
            List<Map<String, Object>> pages = (List<Map<String, Object>>) responseBody.get("pages");
            
            if (pages == null || pages.isEmpty()) {
                logger.info("No Wikipedia results found for: {}", query);
                return "No search results found for: " + query;
            }

            StringBuilder resultContents = new StringBuilder();
            
            for (Map<String, Object> page : pages) {
                String title = (String) page.get("title");
                String excerpt = (String) page.get("excerpt");
                
                // Clean HTML tags from excerpt
                excerpt = excerpt.replaceAll("<[^>]*>", "").trim();
                
                resultContents.append("Title: ").append(title)
                        .append("\nContent: ").append(excerpt)
                        .append("\nURL: https://en.wikipedia.org/wiki/").append(title.replace(" ", "_"))
                        .append("\n\n--- New Result ---\n\n");
            }

            logger.info("✅ Successfully retrieved {} results from Wikipedia", pages.size());
            logger.info("Search results content: {}", resultContents.toString());
            return resultContents.toString();

        } catch (Exception e) {
            logger.error("Error during web search: {}", e.getMessage(), e);
            return "Error occurred while searching: " + e.getMessage();
        }
    }
}
