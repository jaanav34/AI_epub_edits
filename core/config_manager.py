# core/config_manager.py
import configparser
import os

class ConfigManager:
    """Manages global and project-level configurations."""
    def __init__(self, config_path='config.ini'):
        self.config = configparser.ConfigParser()
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Global configuration file not found at '{config_path}'. Please create it.")
        self.config.read(config_path)

    def get_api_key(self, provider_name: str) -> str:
        """Safely retrieves an API key from the [API_KEYS] section."""
        key_map = {
            "gemini": "GOOGLE_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "aistudio": "AISTUDIO_API_KEY"
        }
        key_name = key_map.get(provider_name.lower())
        if not key_name:
            raise ValueError(f"No API key mapping for provider '{provider_name}'.")
        key = self.config.get('API_KEYS', key_name, fallback=None)
        if not key or "PASTE_YOUR" in key:
            raise ValueError(f"API key for '{provider_name}' is not set in config.ini.")
        return key

    def get_provider_config(self, provider_name: str) -> dict:
        """Returns settings for a specific provider (e.g., rate limits)."""
        section_name = f"{provider_name.upper()}_RATE_LIMITS"
        if self.config.has_section(section_name):
            return {
                'rpm': self.config.getint(section_name, 'rpm', fallback=30),
                'tpm': self.config.getint(section_name, 'tpm', fallback=100000),
                'concurrent_calls': self.config.getint(section_name, 'concurrent_calls', fallback=1),
                'retry_attempts': self.config.getint(section_name, 'retry_attempts', fallback=3),
                'retry_delay': self.config.getfloat(section_name, 'retry_delay', fallback=20.0),
            }
        return {} # Return empty dict if no specific config

    from typing import Optional

    def get_default(self, key: str) -> Optional[str]:
        """Gets a value from the [DEFAULTS] section."""
        return self.config.get('DEFAULTS', key, fallback=None)