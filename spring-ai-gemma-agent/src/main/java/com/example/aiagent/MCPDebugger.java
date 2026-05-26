package com.example.aiagent;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpEntity;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

import java.util.HashMap;
import java.util.Map;

/**
 * Debug utility to test MCP connection and tool availability
 * Run this to troubleshoot MCP integration issues
 */
public class MCPDebugger {
    private static final RestTemplate restTemplate = new RestTemplate();
    private static final ObjectMapper objectMapper = new ObjectMapper();
    private static final String MCP_URL = "http://localhost:6274/";
    private static final String MCP_AUTH_TOKEN = "33afbd33fae662d71b5024cc19348c56cfa3b6dae5a16c389b3015aaabbb6f10";

    public static void main(String[] args) throws Exception {
        System.out.println("=== MCP Debug Utility ===\n");

        // Test 1: List available tools
        System.out.println("Test 1: Listing available tools...");
        listTools();

        // Test 2: Try search_wiki tool
        System.out.println("\n\nTest 2: Calling search_wiki tool...");
        callTool("search_wiki", "{'query': 'Python programming'}");

        // Test 3: Try wikipedia_search tool
        System.out.println("\n\nTest 3: Calling wikipedia_search tool...");
        callTool("wikipedia_search", "{'query': 'Python programming'}");
    }

    private static void listTools() {
        try {
            Map<String, Object> request = new HashMap<>();
            request.put("jsonrpc", "2.0");
            request.put("method", "tools/list");
            request.put("id", 1);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("Accept", "application/json");
            headers.set("User-Agent", "MCP-Debugger/1.0");

            String urlWithAuth = MCP_URL + "?MCP_PROXY_AUTH_TOKEN=" + MCP_AUTH_TOKEN;
            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(request), headers);

            System.out.println("URL: " + MCP_URL);
            System.out.println("Request: " + objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(request));

            ResponseEntity<String> response = restTemplate.postForEntity(urlWithAuth, entity, String.class);

            System.out.println("Status: " + response.getStatusCode());
            System.out.println("Response:\n" + response.getBody());
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private static void callTool(String toolName, String argumentsJson) {
        try {
            Map<String, Object> params = new HashMap<>();
            params.put("query", "What is Python?");

            Map<String, Object> request = new HashMap<>();
            request.put("jsonrpc", "2.0");
            request.put("method", "tools/call");
            request.put("params", Map.of(
                "name", toolName,
                "arguments", params
            ));
            request.put("id", 1);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("Accept", "application/json");
            headers.set("User-Agent", "MCP-Debugger/1.0");

            String urlWithAuth = MCP_URL + "?MCP_PROXY_AUTH_TOKEN=" + MCP_AUTH_TOKEN;
            HttpEntity<String> entity = new HttpEntity<>(objectMapper.writeValueAsString(request), headers);

            System.out.println("Tool: " + toolName);
            System.out.println("URL: " + urlWithAuth);
            System.out.println("Request: " + objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(request));

            ResponseEntity<String> response = restTemplate.postForEntity(urlWithAuth, entity, String.class);

            System.out.println("Status: " + response.getStatusCode());
            System.out.println("Response:\n" + response.getBody());
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
