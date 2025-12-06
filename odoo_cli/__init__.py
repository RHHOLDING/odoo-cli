"""
Odoo XML-RPC CLI Tool

A standalone, LLM-optimized command-line interface for Odoo operations.
"""

__version__ = "1.7.1"
__author__ = "Andre Kremer"
__email__ = "andre@solarcraft.gmbh"

# Export main client for convenience
from odoo_cli.client import OdooClient, get_odoo_client

__all__ = ['OdooClient', 'get_odoo_client']