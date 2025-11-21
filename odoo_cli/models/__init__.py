"""Data models for the Odoo CLI"""

from odoo_cli.models.config import OdooConfig
from odoo_cli.models.result import CommandResult
from odoo_cli.models.session import ShellSession
from odoo_cli.models.context import CliContext

__all__ = ['OdooConfig', 'CommandResult', 'ShellSession', 'CliContext']