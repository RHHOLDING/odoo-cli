"""
Configuration loading for Odoo CLI
Handles .env files, YAML profiles, environment variables, and config files

Config Priority Order (highest to lowest):
1. Command-line arguments (--url, --db, --username, --password)
2. Profile from YAML config (--profile or ODOO_PROFILE) - OVERRIDES .env
3. Environment variables / .env files (ODOO_URL, ODOO_DB, etc.)
4. Config file via --config flag (JSON)
5. Default values

.env File Search Order:
1. ODOO_CONFIG environment variable (explicit path)
2. .env in current directory
3. .env in parent directories (up to 5 levels, like Git)
4. ~/.config/odoo-cli/.env (XDG standard)
5. ~/.odoo-cli.env or ~/.odoo_cli.env (legacy)

IMPORTANT: --profile always wins over .env files!
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Import ProfileManager (lazy to avoid circular imports)
_profile_manager = None


# Maximum levels to search up for .env files
MAX_PARENT_SEARCH_LEVELS = 5


def find_env_file(start_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Find .env file by searching current directory and parent directories.
    Similar to how Git finds .git directory.

    Args:
        start_dir: Directory to start searching from (default: current working directory)

    Returns:
        Path to .env file if found, None otherwise
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    for _ in range(MAX_PARENT_SEARCH_LEVELS + 1):
        env_file = current / '.env'
        if env_file.exists():
            return env_file

        # Also check for .odoo-cli.env in case project uses that naming
        odoo_env_file = current / '.odoo-cli.env'
        if odoo_env_file.exists():
            return odoo_env_file

        parent = current.parent
        if parent == current:  # Reached root
            break
        current = parent

    return None


def get_config_search_paths() -> List[Path]:
    """
    Get list of config file paths to search, in priority order.

    Returns:
        List of paths to check for config files
    """
    paths = []

    # 1. ODOO_CONFIG environment variable (explicit path)
    explicit_config = os.getenv('ODOO_CONFIG')
    if explicit_config:
        paths.append(Path(explicit_config).expanduser())

    # 2. Current directory .env
    paths.append(Path.cwd() / '.env')

    # 3. Parent directory search
    parent_env = find_env_file()
    if parent_env and parent_env not in paths:
        paths.append(parent_env)

    # 4. XDG config directory (Linux/Mac standard)
    xdg_config = os.getenv('XDG_CONFIG_HOME', str(Path.home() / '.config'))
    paths.append(Path(xdg_config) / 'odoo-cli' / '.env')
    paths.append(Path(xdg_config) / 'odoo-cli' / 'config.env')

    # 5. Legacy home directory locations
    paths.append(Path.home() / '.odoo-cli.env')
    paths.append(Path.home() / '.odoo_cli.env')

    return paths


def get_profile_manager():
    """Get or create ProfileManager instance."""
    global _profile_manager
    if _profile_manager is None:
        from odoo_cli.models.profile import ProfileManager
        _profile_manager = ProfileManager()
    return _profile_manager


def load_config(
    config_file: Optional[str] = None,
    profile: Optional[str] = None,
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
    3. Profile from YAML config (--profile or ODOO_PROFILE)
    4. ODOO_CONFIG environment variable (explicit path)
    5. .env file in current directory
    6. .env file in parent directories (up to 5 levels)
    7. ~/.config/odoo-cli/.env (XDG standard)
    8. ~/.odoo-cli.env or ~/.odoo_cli.env (legacy)
    9. Config file (JSON) via --config flag

    Args:
        config_file: Path to custom config file
        profile: Profile name to use
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
    config['_config_source'] = None  # Track where config was loaded from
    config['_profile'] = None  # Track active profile

    # Load from .env files FIRST (lowest priority for connection params)
    env_loaded = False
    for env_path in get_config_search_paths():
        if env_path.exists():
            load_dotenv(env_path, override=False)
            if not env_loaded:
                config['_config_source'] = str(env_path)
                env_loaded = True

    # Load from environment variables (set by .env or shell)
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

    # Load from custom config file if provided
    if config_file:
        config_path = Path(config_file).expanduser()
        if config_path.exists():
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)

    # Profile OVERRIDES .env (--profile wins over .env file)
    profile_name = profile or os.getenv('ODOO_PROFILE')

    # Always try to load a profile (get_config will auto-select default if profile_name is None)
    try:
        pm = get_profile_manager()
        profile_config = pm.get_config(profile_name)
        if profile_config:
            config.update(profile_config)  # Profile overwrites .env values
            # Determine which profile was actually loaded
            loaded_profile = pm.get_profile(profile_name)
            if loaded_profile:
                config['_config_source'] = f"profile:{loaded_profile.name}"
                config['_profile'] = loaded_profile.name
    except Exception:
        pass  # Fall through to existing config

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
        # Build helpful error message with search paths
        search_paths = get_config_search_paths()
        paths_str = "\n  ".join(str(p) for p in search_paths[:5])

        raise ValueError(
            f"Missing required configuration: {', '.join(missing)}.\n\n"
            f"Set via environment variables:\n"
            f"  ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD\n\n"
            f"Or create a .env file in one of these locations:\n"
            f"  {paths_str}\n\n"
            f"Or set ODOO_CONFIG=/path/to/.env"
        )


def get_config_info() -> Dict[str, Any]:
    """
    Get information about config discovery for debugging and agent-info.

    Returns:
        Dictionary with config source information
    """
    search_paths = get_config_search_paths()
    found_path = None

    for path in search_paths:
        if path.exists():
            found_path = path
            break

    return {
        "search_paths": [str(p) for p in search_paths],
        "found": str(found_path) if found_path else None,
        "env_vars": {
            "ODOO_URL": bool(os.getenv('ODOO_URL')),
            "ODOO_DB": bool(os.getenv('ODOO_DB')),
            "ODOO_USERNAME": bool(os.getenv('ODOO_USERNAME')),
            "ODOO_PASSWORD": bool(os.getenv('ODOO_PASSWORD')),
            "ODOO_CONFIG": os.getenv('ODOO_CONFIG'),
        }
    }