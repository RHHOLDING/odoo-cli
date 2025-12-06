"""
CLI context model for sharing state across commands
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from rich.console import Console
from odoo_cli.client import OdooClient


@dataclass
class CliContext:
    """Shared state across Click commands"""

    config: Dict[str, Any]
    json_mode: bool
    console: Console
    force_mode: bool = False  # Global --force flag to override readonly
    _client: Optional[OdooClient] = None

    @property
    def client(self) -> OdooClient:
        """Lazy-load and cache the Odoo client"""
        if self._client is None:
            from odoo_cli.client import get_odoo_client
            self._client = get_odoo_client(
                url=self.config.get('url'),
                db=self.config.get('db'),
                username=self.config.get('username'),
                password=self.config.get('password'),
                timeout=self.config.get('timeout', 30),
                verify_ssl=self.config.get('verify_ssl', True),
                readonly=self.config.get('readonly', False)
            )
            # Apply global force mode if set
            if self.force_mode:
                self._client._force_write = True
        return self._client

    def output(self, result: 'CommandResult') -> None:
        """Output result based on mode (JSON or Rich)"""
        if self.json_mode:
            import click
            click.echo(result.to_json())
        else:
            if result.success:
                # Format successful output (implement based on data type)
                self._format_success_output(result.data)
            else:
                self.console.print(f"[red]✗ {result.error}[/red]")
                if result.details:
                    self.console.print(f"  Details: {result.details}")
                if result.suggestion:
                    self.console.print(f"  [yellow]Suggestion: {result.suggestion}[/yellow]")

    def _format_success_output(self, data: Any) -> None:
        """Format successful output for console display"""
        from rich.table import Table
        from rich.pretty import pprint

        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                # Create table for list of dicts
                table = Table(title="Results")
                if data:
                    # Add columns from first item
                    for key in data[0].keys():
                        table.add_column(str(key))
                    # Add rows
                    for item in data:
                        table.add_row(*[str(item.get(k, '')) for k in data[0].keys()])
                self.console.print(table)
            else:
                # Simple list
                for item in data:
                    self.console.print(f"• {item}")
        elif isinstance(data, dict):
            # Pretty print dict
            pprint(data, console=self.console, expand_all=True)
        else:
            # Simple output
            self.console.print(str(data))