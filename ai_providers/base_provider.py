# ai_providers/base_provider.py
from abc import ABC, abstractmethod
import asyncio
import time
import logging

class RateLimiter:
    """Manages API call rates for TPM and RPM with a unified delay mechanism."""
    def __init__(self, tpm_limit: int, rpm_limit: int, concurrent_calls: int):
        self.tpm_capacity = float(tpm_limit)
        self.tokens = float(tpm_limit)
        self.refill_rate_per_second = float(tpm_limit) / 60.0
        self.last_refill_time = time.monotonic()
        self._rpm_delay = 60.0 / rpm_limit if rpm_limit > 0 else 0
        self.concurrent_calls = concurrent_calls
        self._lock = asyncio.Lock()
        self._last_call_time = 0

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill_time
        self.tokens = min(self.tpm_capacity, self.tokens + elapsed * self.refill_rate_per_second)
        self.last_refill_time = now

    async def wait(self, tokens_to_consume: int):
        async with self._lock:
            # Enforce RPM
            now = time.monotonic()
            time_since_last_call = now - self._last_call_time
            if time_since_last_call < self._rpm_delay:
                wait_duration = self._rpm_delay - time_since_last_call
                logging.info(f"RPM Limit: Pausing for {wait_duration:.2f}s.")
                await asyncio.sleep(wait_duration)
            
            # Enforce TPM
            self._refill()
            if tokens_to_consume > self.tpm_capacity:
                logging.warning(f"Request for {tokens_to_consume} tokens exceeds bucket capacity of {self.tpm_capacity}.")

            wait_time = 0
            if tokens_to_consume > self.tokens:
                required_tokens = tokens_to_consume - self.tokens
                wait_time = required_tokens / self.refill_rate_per_second
            
            if wait_time > 0:
                logging.info(f"TPM Limit: Pausing for {wait_time:.2f}s to acquire {tokens_to_consume} tokens.")
                await asyncio.sleep(wait_time)
                self._refill()
            
            self.tokens -= tokens_to_consume
            self._last_call_time = time.monotonic()


class AIProvider(ABC):
    """Abstract Base Class for all AI providers."""
    def __init__(self, api_key: str, model_name: str, config: dict):
        self.api_key = api_key
        self.model_name = model_name
        self.config = config
        self.rate_limiter = RateLimiter(
            tpm_limit=config.get('tpm', 80000),
            rpm_limit=config.get('rpm', 14),
            concurrent_calls=config.get('concurrent_calls', 1)
        )
        self.retry_attempts = config.get('retry_attempts', 3)
        self.retry_delay = config.get('retry_delay', 2)

    @abstractmethod
    async def _perform_rewrite(self, prompt: str, temperature: float) -> str:
        """The specific API call logic for the provider."""
        pass

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Token counting logic specific to the provider."""
        pass

    async def rewrite_chapter(self, prompt: str, temperature: float = 0.7) -> str:
        """A robust, retry-enabled wrapper for rewriting a chapter."""
        
        # We don't know output tokens, so we estimate. A 1:2 ratio is safe.
        # A more advanced implementation might count prompt tokens and estimate output.
        estimated_total_tokens = await self.count_tokens(prompt) * 2
        await self.rate_limiter.wait(estimated_total_tokens)
        
        for attempt in range(self.retry_attempts + 1):
            try:
                logging.info(f"Submitting request to {self.__class__.__name__} (Attempt {attempt + 1})...")
                response = await self._perform_rewrite(prompt, temperature)
                return response
            except Exception as e:
                logging.warning(f"API call failed on attempt {attempt + 1}: {e}")
                if attempt < self.retry_attempts:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logging.info(f"Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logging.error(f"All {self.retry_attempts + 1} rewrite attempts failed.")
                    raise  # Re-raise the final exception
        # This should never be reached, but added to satisfy type checker
        raise RuntimeError("rewrite_chapter failed to return a response after all retries.")