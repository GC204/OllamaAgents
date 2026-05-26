package com.example.aiagent;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Description;
import java.util.function.Function;

@Configuration
public class ToolConfiguration {

    @Bean
    @Description("Search the web for current information or specific queries to get real-time data")
    public Function<SearchRequest, SearchResponse> webSearchTool(WebSearchService webSearchService) {
        return request -> {
            String results = webSearchService.search(request.query());
            return new SearchResponse(results);
        };
    }

    public record SearchRequest(String query) {}
    public record SearchResponse(String content) {}
}
