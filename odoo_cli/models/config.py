"""
Configuration model for Odoo connection
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class OdooConfig:
    """Store connection and authentication details for Odoo instance"""

    url: str
    database: str
    username: str
    password: str
    timeout: int = 30
    verify_ssl: bool = True

    def validate(self) -> None:
        """Validate configuration completeness and format"""
        if not all([self.url, self.database, self.username, self.password]):
            raise ValueError("Incomplete configuration: URL, database, username, and password are required")

        if not self.url.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid URL format: {self.url}. Must start with http:// or https://")

        if self.timeout <= 0:
            raise ValueError(f"Invalid timeout: {self.timeout}. Must be positive")

    @classmethod
    def from_dict(cls, config_dict: dict) -> 'OdooConfig':
        """Create OdooConfig from dictionary"""
        return cls(
            url=config_dict.get('url', ''),
            database=config_dict.get('db') or config_dict.get('database', ''),
            username=config_dict.get('username', ''),
            password=config_dict.get('password', ''),
            timeout=config_dict.get('timeout', 30),
            verify_ssl=config_dict.get('verify_ssl', True)
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'url': self.url,
            'database': self.database,
            'username': self.username,
            'password': self.password,
            'timeout': self.timeout,
            'verify_ssl': self.verify_ssl
        }