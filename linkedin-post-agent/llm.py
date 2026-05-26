"""LLM interface for post generation using Ollama."""

import requests
import json
from typing import Optional, List
from config import OLLAMA_BASE_URL, OLLAMA_MODEL


class OllamaClient:
    """Client for interacting with Ollama LLM."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url
        self.model = model

    def _check_connection(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def _check_model_available(self) -> bool:
        """Check if the configured model is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(self.model in m.get("name", "") for m in models)
        except requests.exceptions.RequestException:
            pass
        return False

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Generate text using Ollama."""
        if not self._check_connection():
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running (ollama serve)."
            )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        if system:
            payload["system"] = system

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.Timeout:
            raise TimeoutError("LLM generation timed out. Try a shorter prompt.")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"LLM request failed: {e}")

    def generate_with_context(
        self,
        system_prompt: str,
        messages: List[dict],
        temperature: float = 0.7,
    ) -> str:
        """Generate text using Ollama with chat format."""
        if not self._check_connection():
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running (ollama serve)."
            )

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except requests.exceptions.Timeout:
            raise TimeoutError("LLM generation timed out. Try a shorter prompt.")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"LLM request failed: {e}")

    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m.get("name", "") for m in models]
        except requests.exceptions.RequestException:
            pass
        return []


# Global client instance
llm_client = OllamaClient()
