import yaml
from dataclasses import dataclass
from typing import List


@dataclass
class AppConfig:
    """Dataclass holding the application configuration."""
    watch_directory: str
    log_level: str
    include_patterns: List[str]
    exclude_patterns: List[str]


def load_config(path: str = "config.yml") -> AppConfig:
    """Loads configuration from a YAML file."""
    try:
        with open(path, 'r') as f:
            raw_config = yaml.safe_load(f)
        
        # Basic validation
        if not raw_config or 'watch_directory' not in raw_config:
            raise ValueError("Configuration must define 'watch_directory'")

        return AppConfig(
            watch_directory=raw_config.get('watch_directory'),
            log_level=raw_config.get('log_level', 'INFO'),
            include_patterns=raw_config.get('include_patterns', ['*']),
            exclude_patterns=raw_config.get('exclude_patterns', [])
        )
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at: {path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}") 