# core/context_manager.py
import json
import logging
from ai_providers.base_provider import AIProvider

class ContextManager:
    """Manages the creation and retrieval of contextual information for prompts."""
    def __init__(self, project_manager, ai_provider: AIProvider):
        self.project = project_manager
        self.ai_provider = ai_provider
        self.glossary_path = project_manager.glossary_path

    async def build_initial_glossary(self):
        """Analyzes the entire book to extract key terms, names, and concepts."""
        state = self.project.load_state()
        all_text = "\n\n".join([ch_data['original_text'] for ch_data in state['chapters'].values()])
        
        # Take a representative sample to avoid huge token counts
        sample_text = (all_text[:40000] + '...' + all_text[-40000:]) if len(all_text) > 80000 else all_text

        prompt = f"""
Analyze the following text from a book. Your task is to identify and extract all significant proper nouns, including:
- Character names (full names and aliases)
- Place names (cities, countries, specific locations)
- Faction or organization names
- Unique in-world terms, concepts, or systems (e.g., "Legacy Tombs", "Mana Core", "System Window")

Return your findings as a single, clean JSON object. The keys should be the categories (e.g., "characters", "locations", "terms"), and the values should be arrays of the extracted strings. Do not add any explanatory text outside of the JSON object.

Example format:
{{
  "characters": ["Alex", "Master Elara"],
  "locations": ["The Crimson City", "Mount Cinder"],
  "organizations": ["The Silver Hand"],
  "terms": ["Aura Manifestation", "Rift Stones"]
}}

TEXT TO ANALYZE:
---
{sample_text}
---
        """
        
        try:
            response_text = await self.ai_provider.rewrite_chapter(prompt, temperature=0.1)
            # Clean and parse the JSON response
            json_str = response_text.strip().replace("```json", "").replace("```", "")
            glossary_data = json.loads(json_str)
            with open(self.glossary_path, 'w', encoding='utf-8') as f:
                json.dump(glossary_data, f, indent=2)
            logging.info(f"Glossary successfully created at {self.glossary_path}")
        except Exception as e:
            logging.error(f"Failed to build initial glossary: {e}")
            # Create an empty glossary file to prevent future attempts
            with open(self.glossary_path, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def get_glossary_as_text(self) -> str:
        """Loads the glossary and formats it as a string for the prompt."""
        if not hasattr(self, '_glossary_cache'):
            try:
                with open(self.glossary_path, 'r', encoding='utf-8') as f:
                    self._glossary_cache = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                self._glossary_cache = {}

        if not self._glossary_cache:
            return "No glossary available."

        text_parts = ["Key Terminology and Names (Must be Preserved):"]
        for category, terms in self._glossary_cache.items():
            if terms:
                text_parts.append(f"- {category.capitalize()}: {', '.join(terms)}")
        
        return "\n".join(text_parts)

    def get_rolling_context(self, current_chapter_index: int) -> str:
        """Gets the summary of the previous chapter to provide short-term memory."""
        if current_chapter_index <= 1:
            return "This is the first chapter."

        state = self.project.load_state()
        previous_chapter_key = str(current_chapter_index - 1)
        previous_chapter = state.get('chapters', {}).get(previous_chapter_key)

        if not previous_chapter:
            logging.warning(f"No previous chapter found for chapter {current_chapter_index}")
            return "No summary available for the previous chapter."

        prev_summary = previous_chapter.get('summary', '')
        if prev_summary:
            return f"Context from Previous Chapter: {prev_summary}"
        else:
            logging.warning(f"Chapter {previous_chapter_key} has no summary yet.")
            return "No summary available for the previous chapter."


    async def generate_chapter_summary(self, rewritten_text: str) -> str:
        """Creates a concise summary of a rewritten chapter for the rolling context."""
        prompt = f"""
Summarize the following book chapter in 2-4 sentences. Focus on the key events, character developments, and the state of things at the very end of the chapter. This summary will be used as context for rewriting the next chapter.

CHAPTER TEXT:
---
{rewritten_text}
---

SUMMARY:
"""
        try:
            summary = await self.ai_provider.rewrite_chapter(prompt, temperature=0.3)
            return summary.strip()
        except Exception as e:
            logging.warning(f"Could not generate chapter summary: {e}")
            return ""