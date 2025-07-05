# core/orchestrator.py
import asyncio
import logging
import os
import json
from typing import Optional
from tqdm import tqdm
from .project_manager import ProjectManager
from .config_manager import ConfigManager
from .context_manager import ContextManager
from ai_providers.base_provider import AIProvider
from ai_providers.gemini_provider import GeminiProvider
from ai_providers.openai_provider import OpenAIProvider
from ai_providers.aistudio_provider import AIStudioProvider
# from ai_providers.anthropic_provider import AnthropicProvider # Uncomment when implemented

class Orchestrator:
    def __init__(self, project: ProjectManager, config: ConfigManager, overrides: Optional[dict] = None):
        self.project = project
        self.global_config = config
        self.project_config = project.load_config()
        self.overrides = overrides or {}

        # Setup logging for the project
        self._setup_logging()
        
        self.provider_name = self.overrides.get('provider', self.global_config.get_default('provider'))
        self.model_name = self.overrides.get('model', self.global_config.get_default('model'))
        max_chapters_value = self.global_config.get_default('max_chapters_per_run')
        if max_chapters_value is None:
            max_chapters_value = 1  # or another sensible default
        self.max_chapters = self.overrides.get('max_chapters_per_run', int(max_chapters_value))

        self.ai_provider = self._select_ai_provider()
        self.context_manager = ContextManager(self.project, self.ai_provider)
        
        logging.info(f"Orchestrator initialized for project '{project.project_name}'")
        logging.info(f"Using Provider: {self.provider_name}, Model: {self.model_name}")

    def _setup_logging(self):
        """Sets up logging to file and console for the project."""
        # Clear previous handlers to avoid duplicate logs
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.project.log_path, 'a', 'utf-8'),
                logging.StreamHandler()
            ]
        )
        # Clear prompt log for new run
        if os.path.exists(self.project.prompt_log_path):
            os.remove(self.project.prompt_log_path)

    def _select_ai_provider(self) -> AIProvider:
        """Factory method to instantiate and return the correct AI provider."""
        provider_config = self.global_config.get_provider_config(self.provider_name)
        api_key = self.global_config.get_api_key(self.provider_name)

        if self.provider_name == 'gemini':
            return GeminiProvider(api_key, self.model_name, provider_config)
        elif self.provider_name == 'openai':
            return OpenAIProvider(api_key, self.model_name, provider_config)
        elif self.provider_name == 'aistudio':
            return AIStudioProvider(api_key, self.model_name, provider_config)
        # elif self.provider_name == 'anthropic':
        #     return AnthropicProvider(api_key, self.model_name, provider_config)
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider_name}")

    def _load_prompt_template(self) -> str:
        """Loads the content of the selected prompt template."""
        template_name = self.global_config.get_default('prompt_template')
        if not template_name or not isinstance(template_name, str):
            raise ValueError("Prompt template name is missing or invalid in configuration.")
        template_path = os.path.join('prompt_templates', template_name)
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _build_master_prompt(self, chapter_text: str, chapter_index: int) -> str:
        """Constructs the full, context-aware prompt for a chapter."""
        base_template = self._load_prompt_template()
        
        # Get context components
        style_ref = self.project_config['styleReferenceText']
        glossary = self.context_manager.get_glossary_as_text()
        rolling_context = self.context_manager.get_rolling_context(chapter_index)

        # Assemble the prompt
        prompt = base_template.format(
            style_reference=style_ref,
            context_glossary=glossary,
            rolling_context=rolling_context,
            chapter_text=chapter_text
        )
        return prompt

    async def run_pipeline(self, start_chapter: int = 1, end_chapter: int = 0):
        pending_chapters = self.project.get_pending_chapters(
            self.max_chapters,
            start_chapter=start_chapter,
            end_chapter=end_chapter
        )
        pending_chapters.sort(key=lambda ch: ch['index'])  # Ensure spine order

        prev_summary = ""
        prev_index = start_chapter - 1

        # 🧠 Ensure previous summary is available
        if prev_index > 0:
            state = self.project.load_state()
            prev_chap = state["chapters"].get(str(prev_index))

            if prev_chap:
                if not prev_chap["summary"]:
                    print(f"📝 Generating missing summary for Chapter {prev_index}...")
                    rewritten_path = os.path.join(self.project.rewritten_txt_dir, prev_chap["rewritten_text_file"])
                    if os.path.exists(rewritten_path):
                        with open(rewritten_path, 'r', encoding='utf-8') as f:
                            prev_text = f.read()
                    else:
                        prev_text = prev_chap["original_text"]

                    prev_summary = await self.context_manager.generate_chapter_summary(prev_text)

                    self.project.update_chapter_state(
                        chapter_index=prev_index,
                        status=prev_chap["status"],
                        summary=prev_summary
                    )
                else:
                    prev_summary = prev_chap["summary"]

        # 🔁 Rewrite loop with rolling context already handled inside _build_master_prompt
        for chapter in tqdm(pending_chapters, desc=f"Rewriting Chapters ({self.provider_name})"):
            index = chapter['index']
            try:
                print(f"\n▶️ Starting Chapter {index}: {chapter['title']}")
                chapter_text = chapter['original_text']

                prompt = self._build_master_prompt(chapter_text, index)

                rewritten_text = await self.ai_provider.rewrite_chapter(prompt)
                summary = await self.context_manager.generate_chapter_summary(rewritten_text)

                self.project.update_chapter_state(
                    chapter_index=index,
                    status="completed",
                    rewritten_text=rewritten_text,
                    summary=summary
                )

                prev_summary = summary  # continue rolling

            except Exception as e:
                print(f"❌ Chapter {index} failed: {e}")
                self.project.update_chapter_state(
                    chapter_index=index,
                    status="failed",
                    error=str(e)
                )
