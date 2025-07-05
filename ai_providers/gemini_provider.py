# ai_providers/gemini_provider.py
import logging
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from google.api_core.exceptions import ResourceExhausted
from .base_provider import AIProvider

class GeminiProvider(AIProvider):
    """AI Provider implementation for Google Gemini."""
    def __init__(self, api_key: str, model_name: str, config: dict):
        super().__init__(api_key, model_name, config)
        genai.configure(api_key=self.api_key) # type: ignore
        self.model = genai.GenerativeModel(self.model_name) # type: ignore
        logging.info(f"GeminiProvider initialized with model: {self.model_name}")

    async def _perform_rewrite(self, prompt: str, temperature: float) -> str:
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=GenerationConfig(temperature=temperature),
                safety_settings={'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE'} # Adjust as needed
            )
            # Handle cases where the response might be blocked or empty
            if not response.parts:
                finish_reason = response.prompt_feedback.block_reason.name if response.prompt_feedback else "UNKNOWN"
                raise ValueError(f"Gemini response was empty or blocked. Reason: {finish_reason}")
            return response.text
        except ResourceExhausted as e:
            logging.warning("Gemini API resource exhausted. This may trigger a longer retry delay.")
            raise e # Re-raise to be handled by the retry logic
        except Exception as e:
            logging.error(f"An unexpected error occurred with Gemini API: {e}")
            raise

    async def count_tokens(self, text: str) -> int:
        try:
            token_count = await self.model.count_tokens_async(text)
            return token_count.total_tokens
        except Exception as e:
            logging.warning(f"Gemini token counting failed: {e}. Estimating based on character count.")
            return len(text) // 4 # Fallback estimation