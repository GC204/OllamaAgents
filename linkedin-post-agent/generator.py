"""Post generation module using LLM with RAG context."""

import json
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
from llm import OllamaClient
from config import POST_SETTINGS, DRAFTS_DIR
from rag import rag_search


class PostGenerator:
    """Generates LinkedIn posts based on topics and user style."""

    def __init__(self):
        self.llm = OllamaClient()
        self.style_profile = self._load_style_profile()

    def _load_style_profile(self) -> Dict:
        """Load user's writing style profile."""
        style_path = Path("data/style_profile.json")
        if style_path.exists():
            with open(style_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return self._default_style_profile()

    def _default_style_profile(self) -> Dict:
        """Default style profile."""
        return {
            "tone": POST_SETTINGS.get("tone", "professional"),
            "use_emoji": POST_SETTINGS.get("include_emoji", False),
            "typical_length": "medium",
            "preferred_structure": "hook-body-cta",
            "avoid_patterns": ["excessive hashtags", "clickbait"],
            "voice_notes": "",
        }

    def save_style_profile(self, profile: Dict):
        """Save updated style profile."""
        style_path = Path("data/style_profile.json")
        with open(style_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

    def analyze_writing_style(self, sample_posts: List[str]) -> Dict:
        """Analyze writing style from sample posts."""
        system_prompt = """You are a writing style analyst. Analyze the provided LinkedIn posts
        and extract the writer's style characteristics. Output valid JSON only."""

        prompt = f"""Analyze these LinkedIn posts and extract style characteristics:

        {'---'.join(sample_posts)}

        Output JSON with these fields:
        - tone: one of (professional, casual, enthusiastic, thought-leader, motivational)
        - use_emoji: boolean
        - typical_length: short/medium/long
        - preferred_structure: describe the structure pattern
        - common_opening_styles: list of patterns
        - common_closing_styles: list of patterns
        - hashtag_usage: description
        - voice_notes: any distinctive voice characteristics

        Respond with valid JSON only, no markdown."""

        response = self.llm.generate(prompt, system=system_prompt)

        # Try to parse JSON from response
        import re
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                profile = json.loads(json_match.group())
                self.save_style_profile(profile)
                return profile
            except json.JSONDecodeError:
                pass

        return self._default_style_profile()

    def generate_post(
        self,
        topic: str,
        trend_context: Optional[str] = None,
        angle: Optional[str] = None,
        use_rag: bool = True,
    ) -> str:
        """Generate a LinkedIn post draft with optional RAG context."""

        # Fetch RAG context if enabled
        rag_context = None
        if use_rag:
            try:
                rag_context = rag_search.get_context_for_topic(topic, max_results=3)
            except Exception as e:
                print(f"RAG search failed: {e}")
                rag_context = None

        system_prompt = f"""You are a LinkedIn content creator. Write engaging, authentic posts
        that follow LinkedIn best practices.

        Style guidelines:
        - Tone: {self.style_profile.get('tone', 'professional')}
        - Use emoji: {self.style_profile.get('use_emoji', False)}
        - Structure: {self.style_profile.get('preferred_structure', 'hook-body-cta')}
        - Max length: {POST_SETTINGS['max_length']} characters
        - Include {POST_SETTINGS['max_hashtags']} or fewer relevant hashtags

        Key principles:
        - Start with a strong hook (first 2 lines must grab attention)
        - Use short paragraphs and white space
        - Be authentic, not salesy
        - End with a call-to-action or thought-provoking question
        - Add relevant hashtags at the end
        - Incorporate recent facts/trends from the provided context naturally"""

        prompt = self._build_generation_prompt(topic, trend_context, angle, rag_context)
        post = self.llm.generate(prompt, system=system_prompt)

        # Clean up the post
        post = post.strip()
        # Remove any markdown code blocks if present
        post = post.replace("```", "").strip()

        return post

    def _build_generation_prompt(
        self,
        topic: str,
        trend_context: Optional[str],
        angle: Optional[str],
        rag_context: Optional[str] = None,
    ) -> str:
        """Build the prompt for post generation."""
        parts = [f"Generate a LinkedIn post about: {topic}"]

        if trend_context:
            parts.append(f"\nTrend context: {trend_context}")

        if angle:
            parts.append(f"\nContent angle: {angle}")
        else:
            parts.append(
                "\nChoose an engaging angle: share an insight, challenge a misconception, "
                "or tell a relevant story."
            )

        if rag_context:
            parts.append(f"\n\nRecent context from web search:\n{rag_context}")

        parts.append(
            "\n\nThe post should feel natural and human-written, not AI-generated. "
            "Avoid clichés like 'In today's fast-paced world' or 'Let's dive in'. "
            "If web context is provided, weave in relevant facts naturally without citing sources explicitly."
        )

        return "".join(parts)

    def generate_variations(
        self,
        topic: str,
        count: int = 3,
        trend_context: Optional[str] = None,
    ) -> List[str]:
        """Generate multiple post variations for the same topic."""
        angles = [
            "Share a personal learning or 'aha' moment",
            "Challenge a common misconception in the industry",
            "Make a bold prediction about the future",
        ]

        variations = []
        for i in range(count):
            angle = angles[i % len(angles)]
            post = self.generate_post(topic, trend_context, angle)
            variations.append(post)

        return variations

    def save_draft(self, post: str, topic: str, metadata: Optional[Dict] = None) -> str:
        """Save a post draft to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"draft_{timestamp}_{topic[:30].replace(' ', '_')}.json"
        filepath = DRAFTS_DIR / filename

        draft_data = {
            "topic": topic,
            "content": post,
            "character_count": len(post),
            "created_at": datetime.now().isoformat(),
            "status": "draft",  # draft, reviewed, posted
            "metadata": metadata or {},
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(draft_data, f, indent=2)

        return str(filepath)

    def get_pending_drafts(self) -> List[Dict]:
        """Get all pending draft posts."""
        drafts = []
        for draft_file in DRAFTS_DIR.glob("draft_*.json"):
            with open(draft_file, "r", encoding="utf-8") as f:
                draft = json.load(f)
                if draft.get("status") == "draft":
                    draft["filepath"] = str(draft_file)
                    drafts.append(draft)
        return sorted(drafts, key=lambda d: d.get("created_at", ""), reverse=True)

    def mark_as_reviewed(self, filepath: str):
        """Mark a draft as reviewed."""
        with open(filepath, "r", encoding="utf-8") as f:
            draft = json.load(f)
        draft["status"] = "reviewed"
        draft["reviewed_at"] = datetime.now().isoformat()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(draft, f, indent=2)

    def mark_as_posted(self, filepath: str, post_url: str):
        """Mark a draft as posted."""
        with open(filepath, "r", encoding="utf-8") as f:
            draft = json.load(f)
        draft["status"] = "posted"
        draft["posted_at"] = datetime.now().isoformat()
        draft["post_url"] = post_url
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(draft, f, indent=2)


# Global instance
post_generator = PostGenerator()
