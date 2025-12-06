"""
Environment Profile Management for Odoo CLI.

Allows switching between different Odoo environments (production, staging, dev)
without editing config files.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List
import os
import yaml


@dataclass
class Profile:
    """Represents an Odoo environment profile."""

    name: str
    url: str
    db: str
    username: str
    password: str
    timeout: int = 30
    verify_ssl: bool = True
    default: bool = False
    readonly: bool = False  # If True, write operations are blocked
    protected: bool = False  # If True, profile can't be modified via CLI
    context: Optional[Dict[str, Any]] = None

    def to_config(self) -> Dict[str, Any]:
        """Convert profile to config dictionary."""
        return {
            "url": self.url,
            "db": self.db,
            "username": self.username,
            "password": self.password,
            "timeout": self.timeout,
            "verify_ssl": self.verify_ssl,
            "readonly": self.readonly,
            "_profile": self.name,
        }

    def to_dict(self, mask_password: bool = True) -> Dict[str, Any]:
        """Convert to dictionary for display."""
        return {
            "name": self.name,
            "url": self.url,
            "db": self.db,
            "username": self.username,
            "password": "***" if mask_password else self.password,
            "timeout": self.timeout,
            "verify_ssl": self.verify_ssl,
            "default": self.default,
            "readonly": self.readonly,
            "protected": self.protected,
        }


class ProfileManager:
    """Manages environment profiles from config file."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize ProfileManager.

        Args:
            config_path: Path to config file. If None, searches standard locations.
        """
        self.config_path = config_path or self._find_config_file()
        self.profiles: Dict[str, Profile] = {}
        self._legacy_config: Optional[Dict[str, Any]] = None
        self._load_profiles()

    def _find_config_file(self) -> Optional[Path]:
        """Find config file in standard locations."""
        search_paths = [
            Path.cwd() / ".odoo-cli.yaml",
            Path.cwd() / "odoo-cli.yaml",
        ]

        # Parent directory search
        current = Path.cwd()
        for _ in range(5):
            search_paths.append(current / ".odoo-cli.yaml")
            search_paths.append(current / "odoo-cli.yaml")
            parent = current.parent
            if parent == current:
                break
            current = parent

        # XDG config
        xdg_config = os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        search_paths.append(Path(xdg_config) / "odoo-cli" / "config.yaml")
        search_paths.append(Path(xdg_config) / "odoo-cli" / "profiles.yaml")

        # Legacy
        search_paths.append(Path.home() / ".odoo-cli.yaml")

        for path in search_paths:
            if path.exists():
                return path

        return None

    def _load_profiles(self) -> None:
        """Load profiles from config file."""
        if not self.config_path or not self.config_path.exists():
            return

        try:
            with open(self.config_path, "r") as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            return

        # Load profiles section
        profiles_data = data.get("profiles", {})
        for name, profile_data in profiles_data.items():
            if isinstance(profile_data, dict):
                self.profiles[name] = Profile(
                    name=name,
                    url=profile_data.get("url", ""),
                    db=profile_data.get("db", ""),
                    username=profile_data.get("username", ""),
                    password=profile_data.get("password", ""),
                    timeout=profile_data.get("timeout", 30),
                    verify_ssl=profile_data.get("verify_ssl", True),
                    default=profile_data.get("default", False),
                    readonly=profile_data.get("readonly", False),
                    protected=profile_data.get("protected", False),
                    context=profile_data.get("context"),
                )

        # Store legacy top-level config if present
        if "url" in data:
            self._legacy_config = {
                "url": data.get("url"),
                "db": data.get("db"),
                "username": data.get("username"),
                "password": data.get("password"),
                "timeout": data.get("timeout", 30),
                "verify_ssl": data.get("verify_ssl", True),
            }

    def get_profile(self, name: Optional[str] = None) -> Optional[Profile]:
        """
        Get profile by name.

        Priority:
        1. Explicit name parameter
        2. ODOO_PROFILE environment variable
        3. Profile marked as default
        4. First profile in list

        Args:
            name: Profile name (optional)

        Returns:
            Profile if found, None otherwise
        """
        # 1. Explicit name
        if name:
            return self.profiles.get(name)

        # 2. Environment variable
        env_profile = os.getenv("ODOO_PROFILE")
        if env_profile and env_profile in self.profiles:
            return self.profiles[env_profile]

        # 3. Default profile
        for profile in self.profiles.values():
            if profile.default:
                return profile

        # 4. First profile
        if self.profiles:
            return next(iter(self.profiles.values()))

        return None

    def get_config(self, profile_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get config dictionary for a profile.

        Args:
            profile_name: Profile name (optional)

        Returns:
            Config dictionary if profile found, None otherwise
        """
        profile = self.get_profile(profile_name)
        if profile:
            return profile.to_config()

        # Fall back to legacy config
        if self._legacy_config:
            return self._legacy_config

        return None

    def list_profiles(self) -> List[str]:
        """List all profile names."""
        return list(self.profiles.keys())

    def has_profiles(self) -> bool:
        """Check if any profiles are defined."""
        return len(self.profiles) > 0

    def get_active_profile_name(self, explicit_name: Optional[str] = None) -> Optional[str]:
        """
        Get the name of the active profile.

        Args:
            explicit_name: Explicitly specified profile name

        Returns:
            Active profile name or None
        """
        if explicit_name and explicit_name in self.profiles:
            return explicit_name

        env_profile = os.getenv("ODOO_PROFILE")
        if env_profile and env_profile in self.profiles:
            return env_profile

        for name, profile in self.profiles.items():
            if profile.default:
                return name

        if self.profiles:
            return next(iter(self.profiles.keys()))

        return None

    def validate_profile(self, name: str) -> Dict[str, Any]:
        """
        Validate that a profile exists and has required fields.

        Args:
            name: Profile name

        Returns:
            Dictionary with validation result
        """
        if name not in self.profiles:
            available = ", ".join(self.profiles.keys()) if self.profiles else "none"
            return {
                "valid": False,
                "error": f"Profile '{name}' not found",
                "available_profiles": available,
            }

        profile = self.profiles[name]
        missing = []

        if not profile.url:
            missing.append("url")
        if not profile.db:
            missing.append("db")
        if not profile.username:
            missing.append("username")
        if not profile.password:
            missing.append("password")

        if missing:
            return {
                "valid": False,
                "error": f"Profile '{name}' missing required fields: {', '.join(missing)}",
                "profile": name,
            }

        return {"valid": True, "profile": name}

    def _get_default_config_path(self) -> Path:
        """Get the default config file path for writing."""
        xdg_config = os.getenv("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        config_dir = Path(xdg_config) / "odoo-cli"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.yaml"

    def _save_profiles(self) -> None:
        """Save profiles to config file."""
        if not self.config_path:
            self.config_path = self._get_default_config_path()

        # Build profiles dict
        profiles_data = {}
        for name, profile in self.profiles.items():
            profiles_data[name] = {
                "url": profile.url,
                "db": profile.db,
                "username": profile.username,
                "password": profile.password,
                "timeout": profile.timeout,
                "verify_ssl": profile.verify_ssl,
            }
            if profile.default:
                profiles_data[name]["default"] = True
            if profile.readonly:
                profiles_data[name]["readonly"] = True
            if profile.protected:
                profiles_data[name]["protected"] = True
            if profile.context:
                profiles_data[name]["context"] = profile.context

        # Write to file
        data = {"profiles": profiles_data}
        with open(self.config_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def add_profile(
        self,
        name: str,
        url: str,
        db: str,
        username: str,
        password: str,
        timeout: int = 30,
        verify_ssl: bool = True,
        default: bool = False,
        readonly: bool = False,
    ) -> Dict[str, Any]:
        """
        Add a new profile.

        Args:
            name: Profile name
            url: Odoo server URL
            db: Database name
            username: Login username
            password: Login password
            timeout: Connection timeout
            readonly: If True, block write operations
            verify_ssl: SSL verification
            default: Set as default profile

        Returns:
            Result dictionary
        """
        if name in self.profiles:
            return {"success": False, "error": f"Profile '{name}' already exists"}

        # If setting as default, unset other defaults
        if default:
            for profile in self.profiles.values():
                profile.default = False

        self.profiles[name] = Profile(
            name=name,
            url=url,
            db=db,
            username=username,
            password=password,
            timeout=timeout,
            verify_ssl=verify_ssl,
            default=default,
            readonly=readonly,
        )

        self._save_profiles()
        return {"success": True, "profile": name, "message": f"Profile '{name}' created"}

    def update_profile(self, name: str, confirmed: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Update an existing profile.

        Args:
            name: Profile name
            confirmed: If True, bypass readonly removal confirmation
            **kwargs: Fields to update (url, db, username, password, timeout, verify_ssl, readonly)

        Returns:
            Result dictionary with possible 'requires_confirmation' flag
        """
        if name not in self.profiles:
            return {"success": False, "error": f"Profile '{name}' not found"}

        profile = self.profiles[name]

        # Check if profile is protected
        if profile.protected:
            return {
                "success": False,
                "error": f"Profile '{name}' is protected and cannot be modified via CLI",
                "hint": "Edit ~/.config/odoo-cli/config.yaml directly to modify protected profiles",
            }

        # Check if trying to remove readonly protection - requires confirmation
        if "readonly" in kwargs and kwargs["readonly"] is False and profile.readonly:
            if not confirmed:
                return {
                    "success": False,
                    "requires_confirmation": True,
                    "error": f"Removing readonly from '{name}' allows write operations",
                    "warning": "This will allow create, write, unlink, and copy operations on this profile",
                }

        # Update fields
        if "url" in kwargs and kwargs["url"]:
            profile.url = kwargs["url"]
        if "db" in kwargs and kwargs["db"]:
            profile.db = kwargs["db"]
        if "username" in kwargs and kwargs["username"]:
            profile.username = kwargs["username"]
        if "password" in kwargs and kwargs["password"]:
            profile.password = kwargs["password"]
        if "timeout" in kwargs and kwargs["timeout"] is not None:
            profile.timeout = kwargs["timeout"]
        if "verify_ssl" in kwargs and kwargs["verify_ssl"] is not None:
            profile.verify_ssl = kwargs["verify_ssl"]
        if "readonly" in kwargs and kwargs["readonly"] is not None:
            profile.readonly = kwargs["readonly"]

        self._save_profiles()
        return {"success": True, "profile": name, "message": f"Profile '{name}' updated"}

    def delete_profile(self, name: str) -> Dict[str, Any]:
        """
        Delete a profile.

        Args:
            name: Profile name

        Returns:
            Result dictionary
        """
        if name not in self.profiles:
            return {"success": False, "error": f"Profile '{name}' not found"}

        profile = self.profiles[name]

        # Check if profile is protected
        if profile.protected:
            return {
                "success": False,
                "error": f"Profile '{name}' is protected and cannot be deleted via CLI",
                "hint": "Edit ~/.config/odoo-cli/config.yaml directly to delete protected profiles",
            }

        del self.profiles[name]
        self._save_profiles()
        return {"success": True, "profile": name, "message": f"Profile '{name}' deleted"}

    def rename_profile(self, old_name: str, new_name: str) -> Dict[str, Any]:
        """
        Rename a profile.

        Args:
            old_name: Current profile name
            new_name: New profile name

        Returns:
            Result dictionary
        """
        if old_name not in self.profiles:
            return {"success": False, "error": f"Profile '{old_name}' not found"}

        if new_name in self.profiles:
            return {"success": False, "error": f"Profile '{new_name}' already exists"}

        profile = self.profiles[old_name]

        # Check if profile is protected
        if profile.protected:
            return {
                "success": False,
                "error": f"Profile '{old_name}' is protected and cannot be renamed via CLI",
                "hint": "Edit ~/.config/odoo-cli/config.yaml directly to rename protected profiles",
            }

        profile.name = new_name
        self.profiles[new_name] = profile
        del self.profiles[old_name]

        self._save_profiles()
        return {
            "success": True,
            "old_name": old_name,
            "new_name": new_name,
            "message": f"Profile renamed from '{old_name}' to '{new_name}'",
        }

    def set_default(self, name: str) -> Dict[str, Any]:
        """
        Set a profile as the default.

        Args:
            name: Profile name

        Returns:
            Result dictionary
        """
        if name not in self.profiles:
            return {"success": False, "error": f"Profile '{name}' not found"}

        # Unset all defaults
        for profile in self.profiles.values():
            profile.default = False

        # Set new default
        self.profiles[name].default = True

        self._save_profiles()
        return {"success": True, "profile": name, "message": f"Profile '{name}' set as default"}
