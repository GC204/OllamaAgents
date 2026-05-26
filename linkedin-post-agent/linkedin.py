"""LinkedIn browser automation using Playwright."""

import asyncio
import json
from typing import Optional, Tuple
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD, DATA_DIR


class LinkedInBrowser:
    """Handles LinkedIn browser automation for posting."""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.session_file = DATA_DIR / "linkedin_session.json"

    async def initialize(self, headless: bool = False) -> bool:
        """Initialize browser and login to LinkedIn."""
        try:
            playwright = await async_playwright().start()

            # Launch browser
            self.browser = await playwright.chromium.launch(
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )

            # Try to load existing session
            if self.session_file.exists():
                loaded = await self._load_session()
                if loaded:
                    return True

            # Create new context and login
            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )

            self.page = await self.context.new_pages()[0]

            # Login to LinkedIn
            logged_in = await self._login()
            if logged_in:
                await self._save_session()
            return logged_in

        except Exception as e:
            print(f"Error initializing LinkedIn browser: {e}")
            return False

    async def _login(self) -> bool:
        """Login to LinkedIn."""
        if not self.page:
            return False

        try:
            # Navigate to LinkedIn
            await self.page.goto("https://www.linkedin.com/login", wait_until="networkidle")

            # Check if already logged in
            if "feed" in self.page.url:
                return True

            # Fill credentials
            await self.page.fill('input[id="username"]', LINKEDIN_EMAIL)
            await self.page.fill('input[id="password"]', LINKEDIN_PASSWORD)

            # Submit form
            await self.page.click('button[type="submit"]')

            # Wait for navigation to feed
            await self.page.wait_for_url("https://www.linkedin.com/feed/*", timeout=30000)

            # Small delay to ensure page is fully loaded
            await asyncio.sleep(2)

            # Check if we're on the feed page
            return "feed" in self.page.url

        except Exception as e:
            print(f"Login error: {e}")
            return False

    async def _save_session(self):
        """Save browser session cookies."""
        if not self.context or not self.session_file:
            return

        try:
            cookies = await self.context.cookies()
            session_data = {
                "cookies": cookies,
                "saved_at": asyncio.get_event_loop().time(),
            }
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f)
        except Exception as e:
            print(f"Error saving session: {e}")

    async def _load_session(self) -> bool:
        """Load browser session cookies."""
        if not self.context or not self.session_file.exists():
            return False

        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)

            cookies = session_data.get("cookies", [])
            await self.context.add_cookies(cookies)

            # Navigate to LinkedIn to verify session
            self.page = await self.context.new_pages()[0]
            await self.page.goto("https://www.linkedin.com/feed", wait_until="networkidle")

            # Check if session is still valid
            if "feed" in self.page.url or "login" not in self.page.url:
                return True

            # Session expired, clear and re-login
            await self.context.clear_cookies()
            self.session_file.unlink()
            return False

        except Exception as e:
            print(f"Error loading session: {e}")
            return False

    async def create_post(self, content: str) -> Tuple[bool, str]:
        """Create a post on LinkedIn.

        Returns:
            Tuple of (success: bool, post_url: str)
        """
        if not self.page:
            return False, "Browser not initialized"

        try:
            # Navigate to feed if not already there
            if "feed" not in self.page.url:
                await self.page.goto("https://www.linkedin.com/feed", wait_until="networkidle")

            # Click on the post creation box
            await asyncio.sleep(1)
            start_post_btn = self.page.locator('button[aria-label="Start a post"]').first
            await start_post_btn.click()

            # Wait for post dialog to open
            await asyncio.sleep(2)

            # Find the text editor and fill content
            # LinkedIn uses a contenteditable div
            editor = self.page.locator('div[contenteditable="true"][role="textbox"]').first
            await editor.click()

            # Clear any existing content first
            await self.page.keyboard.press("Control+A")
            await self.page.keyboard.press("Delete")

            # Type the post content (in chunks to avoid detection)
            await self._type_slowly(editor, content)

            # Wait for content to be recognized
            await asyncio.sleep(1)

            # Click the Post button
            post_btn = self.page.locator('button:has-text("Post")').first
            await post_btn.click()

            # Wait for post to be published
            await asyncio.sleep(3)

            # Check if post was successful
            current_url = self.page.url
            if "feed" in current_url or "activity" in current_url:
                # Try to get the post URL
                if "activity" in current_url:
                    return True, current_url
                return True, "https://www.linkedin.com/feed"

            return False, "Post may not have been published"

        except Exception as e:
            return False, f"Error creating post: {e}"

    async def _type_slowly(self, element, text: str, delay: float = 0.05):
        """Type text with small delays to appear human-like."""
        # For long text, use fill instead
        if len(text) > 500:
            await element.fill(text)
        else:
            for char in text:
                await self.page.keyboard.type(char)
                if char in ".!?\n":
                    await asyncio.sleep(delay * 3)  # Pause at sentence breaks
                else:
                    await asyncio.sleep(delay)

    async def get_feed_content(self, limit: int = 10) -> list:
        """Get recent posts from LinkedIn feed for trend analysis."""
        if not self.page:
            return []

        try:
            if "feed" not in self.page.url:
                await self.page.goto("https://www.linkedin.com/feed", wait_until="networkidle")

            # Wait for feed to load
            await asyncio.sleep(2)

            # Get post elements
            posts = []
            post_elements = self.page.locator('div[data-id="urn:li:activity:"]')
            count = min(limit, await post_elements.count())

            for i in range(count):
                try:
                    post = post_elements.nth(i)
                    content = await post.inner_text()
                    # Extract hashtags
                    hashtags = await post.locator('a[href*="/hashtag/"]').all_text_contents()

                    posts.append({
                        "content": content[:500],  # Truncate for storage
                        "hashtags": hashtags[:5],
                    })
                except Exception:
                    continue

            return posts

        except Exception as e:
            print(f"Error fetching feed: {e}")
            return []

    async def close(self):
        """Close browser and cleanup."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None


# Global instance
linkedin_browser = LinkedInBrowser()
