import requests
import json
import logging
import time
from typing import Optional, Generator

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama LLM server."""
    
    def __init__(
        self, 
        base_url: str, 
        model: str = "gemma4",
        generate_timeout: int = 60,
        pull_timeout: int = 300,
        check_timeout: int = 5,
        max_retries: int = 2
    ):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Base URL of Ollama server (e.g., "http://localhost:11434")
            model: Model name to use (default: gemma4)
            generate_timeout: Timeout for generation requests in seconds
            pull_timeout: Timeout for pull requests in seconds
            check_timeout: Timeout for availability checks in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.generate_url = f"{self.base_url}/api/generate"
        self.pull_url = f"{self.base_url}/api/pull"
        self.tags_url = f"{self.base_url}/api/tags"
        self.generate_timeout = generate_timeout
        self.pull_timeout = pull_timeout
        self.check_timeout = check_timeout
        self.max_retries = max_retries
    
    def is_available(self) -> bool:
        """
        Check if Ollama server is available.
        
        Returns:
            bool: True if server is reachable
        """
        try:
            response = requests.get(self.tags_url, timeout=self.check_timeout)
            return response.status_code == 200
        except requests.Timeout:
            logger.error(f"Ollama server availability check timed out (timeout: {self.check_timeout}s)")
            return False
        except Exception as e:
            logger.error(f"Ollama server not available: {e}")
            return False
    
    def list_models(self) -> list:
        """
        List available models on Ollama server.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(self.tags_url, timeout=self.check_timeout)
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                logger.info(f"Available models: {models}")
                return models
            return []
        except requests.Timeout:
            logger.error(f"Timeout listing models (timeout: {self.check_timeout}s)")
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def ensure_model_available(self) -> bool:
        """
        Ensure the specified model is available, pull if necessary.
        
        Returns:
            bool: True if model is available
        """
        models = self.list_models()
        
        # Check for exact match or partial match (with version tag)
        model_found = any(self.model in m for m in models)
        
        if not model_found:
            logger.info(f"Model {self.model} not found, attempting to pull...")
            return self.pull_model()
        
        logger.info(f"Model {self.model} is available")
        return True
    
    def pull_model(self) -> bool:
        """
        Pull a model from Ollama registry.
        
        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Pulling model: {self.model}")
            response = requests.post(
                self.pull_url,
                json={"name": self.model},
                timeout=self.pull_timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully pulled model: {self.model}")
                return True
            else:
                logger.error(f"Failed to pull model: {response.text}")
                return False
        except requests.Timeout:
            logger.error(f"Model pull timed out after {self.pull_timeout}s")
            return False
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40,
        stream: bool = False
    ) -> Optional[str]:
        """
        Generate text using Ollama with retry logic.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0 to 1.0)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stream: Whether to stream response
            
        Returns:
            Generated text or None if failed
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "stream": stream
                }
                
                logger.info(
                    f"Generating text (attempt {attempt + 1}/{self.max_retries + 1}, "
                    f"timeout: {self.generate_timeout}s)"
                )
                
                response = requests.post(
                    self.generate_url,
                    json=payload,
                    timeout=self.generate_timeout,
                    stream=stream
                )
                
                if response.status_code != 200:
                    logger.error(
                        f"Ollama generation failed with status {response.status_code}: "
                        f"{response.text[:200]}"
                    )
                    last_error = f"HTTP {response.status_code}"
                    continue
                
                if stream:
                    # Return generator for streaming response
                    return self._parse_stream(response)
                else:
                    # Return complete response
                    data = response.json()
                    result = data.get("response", "")
                    logger.info(f"Successfully generated text (length: {len(result)} chars)")
                    return result
            
            except requests.Timeout:
                last_error = f"Request timed out after {self.generate_timeout}s"
                logger.warning(
                    f"Ollama request timed out (attempt {attempt + 1}/{self.max_retries + 1}). "
                    f"Timeout: {self.generate_timeout}s"
                )
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s...
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            
            except (requests.ConnectionError, requests.RequestException) as e:
                last_error = str(e)
                logger.warning(
                    f"Ollama connection error (attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                )
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            
            except Exception as e:
                last_error = str(e)
                logger.error(f"Unexpected error generating text: {e}", exc_info=True)
                break  # Don't retry on unexpected errors
        
        logger.error(f"Failed to generate text after {self.max_retries + 1} attempts. Last error: {last_error}")
        return None
    
    def generate_stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 0.95,
        top_k: int = 40
    ) -> Generator[str, None, None]:
        """
        Generate text using Ollama with streaming and retry logic.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            
        Yields:
            Generated text chunks
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "stream": True
                }
                
                logger.info(
                    f"Starting streaming generation (attempt {attempt + 1}/{self.max_retries + 1}, "
                    f"timeout: {self.generate_timeout}s)"
                )
                
                response = requests.post(
                    self.generate_url,
                    json=payload,
                    timeout=self.generate_timeout,
                    stream=True
                )
                
                if response.status_code != 200:
                    logger.error(
                        f"Ollama streaming generation failed with status {response.status_code}: "
                        f"{response.text[:200]}"
                    )
                    last_error = f"HTTP {response.status_code}"
                    if attempt < self.max_retries:
                        wait_time = 2 ** attempt
                        logger.info(f"Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    continue
                
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            chunk = data.get("response", "")
                            if chunk:
                                yield chunk
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse response line: {line}")
                            continue
                
                # Success
                logger.info("Streaming generation completed successfully")
                return
            
            except requests.Timeout:
                last_error = f"Request timed out after {self.generate_timeout}s"
                logger.warning(
                    f"Ollama streaming request timed out (attempt {attempt + 1}/{self.max_retries + 1}). "
                    f"Timeout: {self.generate_timeout}s"
                )
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            
            except (requests.ConnectionError, requests.RequestException) as e:
                last_error = str(e)
                logger.warning(
                    f"Ollama connection error (attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                )
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            
            except Exception as e:
                last_error = str(e)
                logger.error(f"Unexpected error in streaming generation: {e}", exc_info=True)
                break
        
        logger.error(f"Streaming generation failed after {self.max_retries + 1} attempts. Last error: {last_error}")
    
    def _parse_stream(self, response) -> Generator[str, None, None]:
        """
        Parse streaming response from Ollama.
        
        Args:
            response: Streaming response object
            
        Yields:
            Generated text chunks
        """
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    chunk = data.get("response", "")
                    if chunk:
                        yield chunk
                except json.JSONDecodeError:
                    continue
