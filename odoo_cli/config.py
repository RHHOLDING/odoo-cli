"""
Configuration loading for Odoo CLI
Handles .env files, environment variables, and config files
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv, find_dotenv


def load_config(
    config_file: Optional[str] = None,
    url: Optional[str] = None,
    db: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    timeout: Optional[int] = None,
    verify_ssl: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Load configuration from multiple sources with priority:
    1. Command-line arguments (highest priority)
    2. Environment variables
    3. .env file in current directory
    4. ~/.odoo_cli.env file
    5. Config file (JSON)

    Args:
        config_file: Path to custom config file
        url: Override URL
        db: Override database
        username: Override username
        password: Override password
        timeout: Override timeout
        verify_ssl: Override SSL verification

    Returns:
        Dictionary with configuration values
    """
    config = {}

    # Load from .env files (lowest priority)
    # Try current directory first
    local_env = find_dotenv('.env', usecwd=True)
    if local_env:
        load_dotenv(local_env, override=False)

    # Try home directory
    home_env = Path.home() / '.odoo_cli.env'
    if home_env.exists():
        load_dotenv(home_env, override=False)

    # Load from custom config file if provided
    if config_file:
        config_path = Path(config_file).expanduser()
        if config_path.exists():
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)

    # Load from environment variables (medium priority)
    env_config = {
        'url': os.getenv('ODOO_URL'),
        'db': os.getenv('ODOO_DB') or os.getenv('ODOO_DATABASE'),
        'username': os.getenv('ODOO_USERNAME'),
        'password': os.getenv('ODOO_PASSWORD'),
        'timeout': os.getenv('ODOO_TIMEOUT'),
        'verify_ssl': os.getenv('ODOO_VERIFY_SSL', '').lower() not in ('false', '0', 'no'),
    }

    # Update with non-None environment values
    for key, value in env_config.items():
        if value is not None:
            if key == 'timeout':
                try:
                    config[key] = int(value)
                except (ValueError, TypeError):
                    config[key] = 30
            else:
                config[key] = value

    # Override with command-line arguments (highest priority)
    if url is not None:
        config['url'] = url
    if db is not None:
        config['db'] = db
    if username is not None:
        config['username'] = username
    if password is not None:
        config['password'] = password
    if timeout is not None:
        config['timeout'] = timeout
    if verify_ssl is not None:
        config['verify_ssl'] = verify_ssl

    # Set defaults
    config.setdefault('timeout', 30)
    config.setdefault('verify_ssl', True)

    # Check for no-verify-ssl flag
    if os.getenv('ODOO_NO_VERIFY_SSL', '').lower() in ('true', '1', 'yes'):
        config['verify_ssl'] = False

    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate that required configuration values are present

    Args:
        config: Configuration dictionary

    Raises:
        ValueError: If required configuration is missing
    """
    required = ['url', 'db', 'username', 'password']
    missing = [key for key in required if not config.get(key)]

    if missing:
        raise ValueError(
            f"Missing required configuration: {', '.join(missing)}. "
            f"Please set via environment variables (ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD) "
            f"or create a .env file."
        )