import yaml
from dataclasses import dataclass
from typing import List, Optional


@dataclass 
class LLMConfig:
    """Configuration for LLM integration."""
    base_url: str = "http://localhost:11434"
    model_name: str = "sequentialthought"
    timeout_seconds: int = 30
    enable_linear_fallback: bool = True
    fallback_team_id: str = "b5f1d099-acc2-4e51-a415-76c00c00f23b"
    fallback_project_id: Optional[str] = None


@dataclass
class AppConfig:
    """Dataclass holding the application configuration."""
    watch_directory: str
    log_level: str
    include_patterns: List[str]
    exclude_patterns: List[str]
    llm: LLMConfig


def load_config(path: str = "config.yml") -> AppConfig:
    """Loads configuration from a YAML file."""
    try:
        with open(path, 'r') as f:
            raw_config = yaml.safe_load(f)
        
        # Basic validation
        if not raw_config or 'watch_directory' not in raw_config:
            raise ValueError("Configuration must define 'watch_directory'")

        # Parse LLM configuration
        llm_config_data = raw_config.get('llm', {})
        llm_config = LLMConfig(
            base_url=llm_config_data.get('base_url', 'http://localhost:11434'),
            model_name=llm_config_data.get('model_name', 'sequentialthought'),
            timeout_seconds=llm_config_data.get('timeout_seconds', 30),
            enable_linear_fallback=llm_config_data.get('enable_linear_fallback', True),
            fallback_team_id=llm_config_data.get('fallback_team_id', 'b5f1d099-acc2-4e51-a415-76c00c00f23b'),
            fallback_project_id=llm_config_data.get('fallback_project_id')
        )

        return AppConfig(
            watch_directory=raw_config.get('watch_directory'),
            log_level=raw_config.get('log_level', 'INFO'),
            include_patterns=raw_config.get('include_patterns', ['*']),
            exclude_patterns=raw_config.get('exclude_patterns', []),
            llm=llm_config
        )
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at: {path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}") 