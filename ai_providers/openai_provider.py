# ai_providers/openai_provider.py
import logging
from openai import AsyncOpenAI
from .base_provider import AIProvider
import tiktoken

class OpenAIProvider(AIProvider):
    """AI Provider implementation for OpenAI GPT models."""
    def __init__(self, api_key: str, model_name: str, config: dict):
        super().__init__(api_key, model_name, config)
        self.client = AsyncOpenAI(api_key=self.api_key)
        try:
            # Get the tokenizer for the specified model
            self.tokenizer = tiktoken.encoding_for_model(self.model_name)
        except KeyError:
            # Fallback for models not in tiktoken's registry
            logging.warning(f"No tokenizer found for model {self.model_name}. Using 'cl100k_base'.")
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        logging.info(f"OpenAIProvider initialized with model: {self.model_name}")

    async def _perform_rewrite(self, prompt: str, temperature: float) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a master literary editor. Follow the user's instructions precisely."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logging.error(f"An unexpected error occurred with OpenAI API: {e}")
            raise

    async def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))