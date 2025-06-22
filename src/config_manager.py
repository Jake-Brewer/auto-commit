"""
Configuration Manager for hierarchical include/exclude rules.

This module implements the ConfigurationManager class that handles
hierarchical .gitinclude and .gitignore files to determine file processing
decisions.
"""

import fnmatch
from pathlib import Path
from typing import List, Tuple
from enum import Enum
import logging


class FileAction(Enum):
    """Possible actions for a file based on configuration rules."""
    INCLUDE = "include"
    IGNORE = "ignore"
    REVIEW = "review"  # Ambiguous - needs human review


class ConfigurationManager:
    """
    Manages hierarchical .gitinclude and .gitignore files.
    
    This class walks up the directory tree to find configuration files
    and applies rules in the correct precedence order.
    """
    
    def __init__(self, watch_directory: str):
        """
        Initialize the ConfigurationManager.
        
        Args:
            watch_directory: Root directory being watched
        """
        self.watch_directory = Path(watch_directory).resolve()
        self.logger = logging.getLogger("ConfigurationManager")
        
        # Cache for parsed configuration files
        self._config_cache: dict[Path, List[str]] = {}
        
    def _find_config_files(self, file_path: Path) -> List[Tuple[Path, str]]:
        """
        Find all .gitinclude and .gitignore files from root to file location.
        
        Args:
            file_path: Path to the file being checked
            
        Returns:
            List of (config_file_path, config_type) tuples in precedence order
        """
        config_files: List[Tuple[Path, str]] = []
        
        # Start from the file's directory and walk up to watch_directory
        current_dir = file_path.parent if file_path.is_file() else file_path
        
        # Ensure we're within the watch directory
        try:
            current_dir.relative_to(self.watch_directory)
        except ValueError:
            self.logger.warning(f"File {file_path} is outside watch directory")
            return config_files
            
        # Walk up the directory tree
        while True:
            # Check for .gitinclude
            gitinclude_path = current_dir / ".gitinclude"
            if gitinclude_path.exists():
                config_files.append((gitinclude_path, "include"))
                
            # Check for .gitignore
            gitignore_path = current_dir / ".gitignore"
            if gitignore_path.exists():
                config_files.append((gitignore_path, "ignore"))
                
            # Stop if we've reached the watch directory
            if current_dir == self.watch_directory:
                break
                
            # Move up one directory
            parent = current_dir.parent
            if parent == current_dir:  # Reached filesystem root
                break
            current_dir = parent
            
        # Reverse to get root-to-leaf order (lower precedence to higher)
        return list(reversed(config_files))
        
    def _parse_config_file(self, config_path: Path) -> List[str]:
        """
        Parse a configuration file and return list of patterns.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            List of patterns from the file
        """
        if config_path in self._config_cache:
            return self._config_cache[config_path]
            
        patterns = []
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        patterns.append(line)
                        
            self._config_cache[config_path] = patterns
            self.logger.debug(f"Parsed {len(patterns)} patterns from {config_path}")
            
        except Exception as e:
            self.logger.error(f"Error parsing config file {config_path}: {e}")
            
        return patterns
        
    def _matches_pattern(self, file_path: Path, pattern: str, 
                        config_dir: Path) -> bool:
        """
        Check if a file path matches a pattern.
        
        Args:
            file_path: Absolute path to the file
            pattern: Pattern to match against
            config_dir: Directory containing the config file
            
        Returns:
            True if the pattern matches
        """
        try:
            # Make file path relative to config directory
            rel_path = file_path.relative_to(config_dir)
            rel_path_str = str(rel_path).replace('\\', '/')
            
            # Handle directory patterns (ending with /)
            if pattern.endswith('/'):
                # Match if file is in this directory
                dir_pattern = pattern.rstrip('/')
                return (rel_path_str.startswith(dir_pattern + '/') or 
                       rel_path_str == dir_pattern)
            
            # Regular file pattern matching
            return fnmatch.fnmatch(rel_path_str, pattern)
            
        except ValueError:
            # File is not under config directory
            return False
        except Exception as e:
            self.logger.error(f"Error matching pattern {pattern}: {e}")
            return False
            
    def get_file_action(self, file_path: str) -> FileAction:
        """
        Determine the action for a file based on configuration rules.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            FileAction indicating what to do with the file
        """
        file_path_obj = Path(file_path).resolve()
        
        # Find all relevant config files
        config_files = self._find_config_files(file_path_obj)
        
        if not config_files:
            # No config files found - default to review for safety
            self.logger.debug(f"No config files found for {file_path}, defaulting to REVIEW")
            return FileAction.REVIEW
            
        include_matches = []
        ignore_matches = []
        
        # Process config files in precedence order
        for config_path, config_type in config_files:
            patterns = self._parse_config_file(config_path)
            config_dir = config_path.parent
            
            for pattern in patterns:
                if self._matches_pattern(file_path_obj, pattern, config_dir):
                    if config_type == "include":
                        include_matches.append((config_path, pattern))
                    else:  # ignore
                        ignore_matches.append((config_path, pattern))
                        
        # Apply precedence rules:
        # 1. If both include and ignore matches exist, it's ambiguous -> REVIEW
        # 2. If only ignore matches exist -> IGNORE
        # 3. If only include matches exist -> INCLUDE
        # 4. If no matches exist -> REVIEW (default to safe)
        
        if include_matches and ignore_matches:
            self.logger.info(f"Ambiguous rules for {file_path}: "
                           f"include={len(include_matches)}, "
                           f"ignore={len(ignore_matches)}")
            return FileAction.REVIEW
        elif ignore_matches:
            self.logger.debug(f"File {file_path} ignored by {len(ignore_matches)} rules")
            return FileAction.IGNORE
        elif include_matches:
            self.logger.debug(f"File {file_path} included by {len(include_matches)} rules")
            return FileAction.INCLUDE
        else:
            # No explicit rules found - default to review
            self.logger.debug(f"No matching rules for {file_path}, defaulting to REVIEW")
            return FileAction.REVIEW
            
    def clear_cache(self):
        """Clear the configuration file cache."""
        self._config_cache.clear()
        self.logger.debug("Configuration cache cleared")
        
    def get_stats(self) -> dict:
        """
        Get statistics about the configuration manager.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "watch_directory": str(self.watch_directory),
            "cached_config_files": len(self._config_cache),
            "cache_files": list(str(p) for p in self._config_cache.keys())
        } 