"""Configuration management for PMS."""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

# Default configuration
DEFAULT_CONFIG = {
    "api": {
        "email": "",  # Required by NCBI
        "tool": "pms",  # Tool name for NCBI
        "api_key": "",  # Optional API key for higher rate limits
        "max_retries": 3,
        "retry_delay": 5,
        "requests_per_second": 3,  # Default rate limit without API key (conservative)
    },
    "storage": {
        "database_path": "~/.local/share/pms/pms.db",
        "data_dir": "~/.local/share/pms/data",
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "~/.local/share/pms/pms.log",
    },
}


class Config:
    """Configuration manager for PMS."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file. If None, uses the default
                         location (~/.config/pms/config.json).
        """
        self.config_path = Path(
            config_path or os.path.expanduser("~/.config/pms/config.json")
        )
        self.config = DEFAULT_CONFIG.copy()
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file if it exists."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                    self._update_nested_dict(self.config, user_config)
            except Exception as e:
                logging.warning(f"Failed to load config from {self.config_path}: {e}")
                logging.warning("Using default configuration")

    def _update_nested_dict(self, d: Dict[str, Any], u: Dict[str, Any]) -> None:
        """Update a nested dictionary with another dictionary.

        Args:
            d: Dictionary to update
            u: Dictionary with updates
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v

    def save(self) -> None:
        """Save the current configuration to file."""
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)

    def get(self, section: str, key: str) -> Any:
        """Get a configuration value.

        Args:
            section: The configuration section
            key: The configuration key

        Returns:
            The configuration value
        """
        return self.config.get(section, {}).get(key)

    def set(self, section: str, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            section: The configuration section
            key: The configuration key
            value: The configuration value
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        # Expand user directory
        db_path = os.path.expanduser(self.config["storage"]["database_path"])
        data_dir = os.path.expanduser(self.config["storage"]["data_dir"])

        # Ensure parent directories exist
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(data_dir).mkdir(parents=True, exist_ok=True)


# Global configuration instance
config = Config()
