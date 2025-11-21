"""
Contract tests for the 'execute' command
These tests verify the command interface and behavior
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner


class TestExecuteCommand:
    """Test suite for odoo execute command"""

    def test_execute_command_exists(self, cli_runner):
        """Test that execute command is available"""
        from odoo_cli.cli import cli

        result = cli_runner.invoke(cli, ['execute', '--help'])
        assert result.exit_code == 0
        assert 'Execute arbitrary model method' in result.output

    def test_execute_with_required_args(self, cli_runner, mock_odoo_client):
        """Test execute command with required arguments"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.execute.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.execute.return_value = 42

            result = cli_runner.invoke(cli, [
                'execute',
                'res.partner',
                'search_count',
                '--args', '[[]]'
            ])

            assert result.exit_code == 0
            mock_odoo_client.execute.assert_called_once_with(
                'res.partner', 'search_count', []
            )

    def test_execute_with_kwargs(self, cli_runner, mock_odoo_client):
        """Test execute command with keyword arguments"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.execute.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.execute.return_value = []

            result = cli_runner.invoke(cli, [
                'execute',
                'res.partner',
                'search_read',
                '--args', '[[]]',
                '--kwargs', '{"limit": 10, "fields": ["name", "email"]}'
            ])

            assert result.exit_code == 0

    def test_execute_json_output(self, cli_runner, mock_odoo_client):
        """Test execute command with JSON output"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.execute.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.execute.return_value = {'result': 'test_value'}

            result = cli_runner.invoke(cli, [
                'execute',
                'res.partner',
                'test_method',
                '--json'
            ])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output['success'] is True
            assert 'data' in output

    def test_execute_with_module_upgrade(self, cli_runner, mock_odoo_client):
        """Test execute command for module upgrade scenario"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.execute.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.execute.return_value = True

            result = cli_runner.invoke(cli, [
                'execute',
                'ir.module.module',
                'button_immediate_upgrade',
                '--args', '[[["name", "=", "sale"]]]'
            ])

            assert result.exit_code == 0

    def test_execute_error_handling(self, cli_runner, mock_odoo_client):
        """Test execute command error handling"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.execute.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.execute.side_effect = Exception("Method not found")

            result = cli_runner.invoke(cli, [
                'execute',
                'invalid.model',
                'invalid_method',
                '--json'
            ])

            assert result.exit_code == 3  # Data error
            output = json.loads(result.output)
            assert output['success'] is False
            assert output['error_type'] == 'data'

    def test_execute_connection_error(self, cli_runner):
        """Test execute command with connection error"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.execute.get_odoo_client') as mock_get_client:
            mock_get_client.side_effect = ConnectionError("Connection refused")

            result = cli_runner.invoke(cli, [
                'execute',
                'res.partner',
                'search',
                '--json'
            ])

            assert result.exit_code == 1  # Connection error
            output = json.loads(result.output)
            assert output['success'] is False
            assert output['error_type'] == 'connection'

    def test_execute_auth_error(self, cli_runner):
        """Test execute command with authentication error"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.execute.get_odoo_client') as mock_get_client:
            mock_get_client.side_effect = ValueError("Authentication failed")

            result = cli_runner.invoke(cli, [
                'execute',
                'res.partner',
                'search',
                '--json'
            ])

            assert result.exit_code == 2  # Auth error
            output = json.loads(result.output)
            assert output['success'] is False
            assert output['error_type'] == 'auth'

    def test_execute_missing_model(self, cli_runner):
        """Test execute command with missing model argument"""
        from odoo_cli.cli import cli

        result = cli_runner.invoke(cli, ['execute'])
        assert result.exit_code != 0
        assert 'Missing argument' in result.output or 'required' in result.output.lower()

    def test_execute_invalid_json_args(self, cli_runner):
        """Test execute command with invalid JSON in args"""
        from odoo_cli.cli import cli

        result = cli_runner.invoke(cli, [
            'execute',
            'res.partner',
            'search',
            '--args', 'invalid json'
        ])

        assert result.exit_code != 0