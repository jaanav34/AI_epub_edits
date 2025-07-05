import logging
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from google.api_core.exceptions import ResourceExhausted
from .base_provider import AIProvider

class AIStudioProvider(AIProvider):
    """AI Provider implementation for Google AI Studio (Gemini)."""

    def __init__(self, api_key: str, model_name: str, config: dict):
        super().__init__(api_key, model_name, config)
        print(f"Using API key: {repr(self.api_key)}")
        genai.configure(api_key=self.api_key)  # type: ignore
        self.model = genai.GenerativeModel(self.model_name)  # type: ignore
        logging.info(f"AIStudioProvider initialized with model: {self.model_name}")

    async def _perform_rewrite(self, prompt: str, temperature: float) -> str:
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=GenerationConfig(temperature=temperature),
                # You may adjust safety settings if needed
                safety_settings={
                    "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                    "HARM_CATEGORY_SEXUAL": "BLOCK_NONE",
                    "HARM_CATEGORY_DANGEROUS": "BLOCK_NONE",
                    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE"
                }
            )
            if not response.parts:
                finish_reason = response.prompt_feedback.block_reason.name if response.prompt_feedback else "UNKNOWN"
                raise ValueError(f"AI Studio response was empty or blocked. Reason: {finish_reason}")
            return response.text
        except ResourceExhausted as e:
            logging.warning("AI Studio API resource exhausted. This may trigger a longer retry delay.")
            raise e  # Let the retry logic handle this
        except Exception as e:
            logging.error(f"An unexpected error occurred in AI Studio provider: {e}", exc_info=True)
            raise

    async def count_tokens(self, text: str) -> int:
        try:
            token_info = await self.model.count_tokens_async(text)
            return token_info.total_tokens
        except Exception as e:
            logging.warning(f"AI Studio token count failed: {e}. Estimating based on character length.")
            return len(text) // 4  # Fallback token estimation
