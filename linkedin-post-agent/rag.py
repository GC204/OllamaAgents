"""RAG (Retrieval-Augmented Generation) module for fetching and processing web content."""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

from duckduckgo_search import DDGS
from newspaper import Article
import nltk
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

from config import DATA_DIR

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)


@dataclass
class SearchResult:
    """Represents a search result with content."""
    title: str
    url: str
    content: str
    summary: str
    published_date: Optional[str]
    source: str
    relevance_score: float
    fetched_at: str


class RAGSearch:
    """Retrieval-Augmented Generation search for trending tech topics."""

    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or DATA_DIR / "rag_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.search_index_file = self.cache_dir / "search_index.json"
        self.vector_index_file = self.cache_dir / "vector_index.faiss"
        self.embeddings_file = self.cache_dir / "embeddings.npy"

        # Initialize embedding model (lightweight)
        self.embedding_model = None
        self.vector_index = None
        self.search_cache: Dict[str, SearchResult] = {}

    def _load_cache(self):
        """Load search cache from disk."""
        if self.search_index_file.exists():
            with open(self.search_index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.search_cache = {k: SearchResult(**v) for k, v in data.items()}

    def _save_cache(self):
        """Save search cache to disk."""
        data = {k: asdict(v) for k, v in self.search_cache.items()}
        with open(self.search_index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _init_embeddings(self):
        """Initialize sentence transformer for embeddings."""
        if self.embedding_model is None:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                print(f"Warning: Could not load embedding model: {e}")
                self.embedding_model = None

    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding vector for text."""
        if self.embedding_model is None:
            self._init_embeddings()

        if self.embedding_model:
            return self.embedding_model.encode([text])[0]
        return None

    def _build_vector_index(self, documents: List[str]):
        """Build FAISS vector index for documents."""
        if not documents:
            return

        if self.embedding_model is None:
            self._init_embeddings()

        if self.embedding_model:
            embeddings = self.embedding_model.encode(documents)
            dimension = embeddings.shape[1]
            self.vector_index = faiss.IndexFlatL2(dimension)
            self.vector_index.add(embeddings.astype('float32'))

    def search_web(
        self,
        query: str,
        num_results: int = 10,
        category: str = "tech",
        time_range: str = "w",  # d=day, w=week, m=month, y=year
    ) -> List[SearchResult]:
        """Search the web for trending topics."""

        # Check cache first
        cache_key = hashlib.md5(f"{query}_{category}_{time_range}".encode()).hexdigest()
        if cache_key in self.search_cache:
            result = self.search_cache[cache_key]
            if (datetime.now() - datetime.fromisoformat(result.fetched_at)).total_seconds() < 3600:
                return [result]

        results = []

        try:
            # Search using DuckDuckGo
            with DDGS() as ddgs:
                search_results = list(ddgs.text(
                    query,
                    region="en-us",
                    safesearch="moderate",
                    timelimit=time_range,
                    max_results=num_results,
                ))

                for item in search_results[:num_results]:
                    title = item.get("title", "")
                    url = item.get("href", "")
                    snippet = item.get("body", "")

                    # Fetch full article content
                    content, published_date = self._fetch_article_content(url)

                    if content:
                        # Generate AI summary
                        summary = self._generate_summary(title, snippet)

                        result = SearchResult(
                            title=title,
                            url=url,
                            content=content[:2000],  # Truncate for storage
                            summary=summary,
                            published_date=published_date,
                            source=self._extract_source(url),
                            relevance_score=0.8,  # Placeholder
                            fetched_at=datetime.now().isoformat(),
                        )

                        results.append(result)
                        self.search_cache[cache_key] = result

        except Exception as e:
            print(f"Search error: {e}")
            # Fallback to mock results for testing
            results = self._get_fallback_results(query)

        self._save_cache()
        return results

    def _fetch_article_content(self, url: str) -> Tuple[str, Optional[str]]:
        """Fetch and extract article content from URL."""
        try:
            article = Article(url)
            article.download()
            article.parse()

            # Try to extract publish date
            published_date = None
            if article.publish_date:
                published_date = article.publish_date.isoformat()

            return article.text, published_date

        except Exception as e:
            print(f"Error fetching article {url}: {e}")
            return "", None

    def _generate_summary(self, title: str, snippet: str) -> str:
        """Generate a concise summary from title and snippet."""
        # Simple extractive summary for now
        # Could be enhanced with LLM summarization
        words = snippet.split()
        if len(words) <= 30:
            return snippet
        return " ".join(words[:30]) + "..."

    def _extract_source(self, url: str) -> str:
        """Extract source domain from URL."""
        match = re.search(r"(?:https?://)?(?:www\.)?([^/]+)", url)
        if match:
            domain = match.group(1)
            # Remove common TLDs
            domain = re.sub(r"\.(com|org|net|io|co|uk)$", "", domain)
            return domain.capitalize()
        return "Unknown"

    def _get_fallback_results(self, query: str) -> List[SearchResult]:
        """Fallback results when search fails."""
        return [
            SearchResult(
                title=f"Trending: {query}",
                url="https://example.com",
                content=f"Recent developments in {query} are shaping the industry. "
                        "Experts highlight key innovations and emerging patterns.",
                summary=f"Key trends in {query}",
                published_date=datetime.now().isoformat(),
                source="Fallback",
                relevance_score=0.5,
                fetched_at=datetime.now().isoformat(),
            )
        ]

    def search_trending_tech(self, topics: List[str] = None) -> List[SearchResult]:
        """Search for trending tech topics."""

        if topics is None:
            topics = [
                "artificial intelligence breakthroughs",
                "machine learning trends 2026",
                "generative AI applications",
                "LLM developments",
                "AI in business",
                "tech industry news",
                "startup funding tech",
                "cybersecurity trends",
                "cloud computing innovations",
                "quantum computing advances",
            ]

        all_results = []
        for topic in topics[:5]:  # Limit to avoid rate limits
            results = self.search_web(topic, num_results=3)
            all_results.extend(results)

        # Sort by relevance
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return all_results[:15]

    def get_context_for_topic(self, topic: str, max_results: int = 5) -> str:
        """Get contextual information about a topic from web search."""

        results = self.search_web(topic, num_results=max_results)

        if not results:
            return f"No recent information found about {topic}."

        # Build context from results
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Source {i}: {result.source}]\n"
                f"Title: {result.title}\n"
                f"Summary: {result.summary}\n"
                f"Key points: {result.content[:300]}...\n"
            )

        context = "\n---\n".join(context_parts)

        return f"Recent information about '{topic}':\n\n{context}"

    def search_and_embed(
        self,
        query: str,
        num_results: int = 5,
        top_k: int = 3,
    ) -> List[Dict]:
        """Search, retrieve, and find most relevant content chunks."""

        # Search web
        results = self.search_web(query, num_results=num_results)

        if not results:
            return []

        # Chunk content for finer retrieval
        chunks = []
        for result in results:
            # Split content into sentences (simple chunking)
            sentences = re.split(r'(?<=[.!?])\s+', result.content)
            for i in range(0, len(sentences), 3):
                chunk = " ".join(sentences[i:i+3])
                if len(chunk) > 50:
                    chunks.append({
                        "text": chunk,
                        "source": result.source,
                        "title": result.title,
                        "url": result.url,
                    })

        # Build vector index for chunks
        if chunks and self.embedding_model:
            self._init_embeddings()
            texts = [c["text"] for c in chunks]
            self._build_vector_index(texts)

            # Get query embedding and find similar
            query_embedding = self._get_embedding(query)
            if query_embedding is not None and self.vector_index:
                scores, indices = self.vector_index.search(
                    np.array([query_embedding]).astype('float32'),
                    min(top_k, len(chunks))
                )

                relevant_chunks = []
                for idx in indices[0]:
                    chunk = chunks[idx].copy()
                    chunk["relevance"] = float(scores[0][list(indices[0]).index(idx)])
                    relevant_chunks.append(chunk)

                return relevant_chunks

        # Fallback: return first chunks
        return chunks[:top_k]

    def clear_cache(self):
        """Clear the search cache."""
        self.search_cache.clear()
        if self.search_index_file.exists():
            self.search_index_file.unlink()
        print("Cache cleared.")


# Global instance
rag_search = RAGSearch()
