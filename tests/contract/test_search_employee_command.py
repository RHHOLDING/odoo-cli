"""
Contract tests for the 'search-employee' command
"""

import pytest
import json
from unittest.mock import patch
from click.testing import CliRunner


class TestSearchEmployeeCommand:
    """Test suite for odoo search-employee command"""

    def test_search_employee_command_exists(self, cli_runner):
        """Test that search-employee command is available"""
        from odoo_cli.cli import cli

        result = cli_runner.invoke(cli, ['search-employee', '--help'])
        assert result.exit_code == 0
        assert 'Search employees by name' in result.output

    def test_search_employee_basic(self, cli_runner, mock_odoo_client, sample_employees):
        """Test basic employee search"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.search_employee.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.search_employees.return_value = sample_employees

            result = cli_runner.invoke(cli, ['search-employee', 'John'])

            assert result.exit_code == 0
            assert 'John Smith' in result.output
            mock_odoo_client.search_employees.assert_called_once_with('John', limit=20)

    def test_search_employee_with_limit(self, cli_runner, mock_odoo_client):
        """Test employee search with custom limit"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.search_employee.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.search_employees.return_value = []

            result = cli_runner.invoke(cli, [
                'search-employee', 'Jane', '--limit', '5'
            ])

            assert result.exit_code == 0
            mock_odoo_client.search_employees.assert_called_once_with('Jane', limit=5)

    def test_search_employee_json_output(self, cli_runner, mock_odoo_client, sample_employees):
        """Test employee search with JSON output"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.search_employee.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.search_employees.return_value = sample_employees

            result = cli_runner.invoke(cli, [
                'search-employee', 'John', '--json'
            ])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output['success'] is True
            assert len(output['data']) == 2
            assert output['data'][0]['name'] == 'John Smith'

    def test_search_employee_no_results(self, cli_runner, mock_odoo_client):
        """Test employee search with no results"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.search_employee.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.search_employees.return_value = []

            result = cli_runner.invoke(cli, [
                'search-employee', 'NonExistent', '--json'
            ])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output['success'] is True
            assert output['data'] == []

    def test_search_employee_rich_output_format(self, cli_runner, mock_odoo_client, sample_employees):
        """Test employee search rich table output format"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.search_employee.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.search_employees.return_value = sample_employees

            result = cli_runner.invoke(cli, ['search-employee', 'all'])

            assert result.exit_code == 0
            # Should show table headers
            assert 'Name' in result.output or 'name' in result.output.lower()
            assert 'Email' in result.output or 'email' in result.output.lower()
            assert 'Department' in result.output or 'department' in result.output.lower()

    def test_search_employee_missing_name_argument(self, cli_runner):
        """Test search-employee without name argument"""
        from odoo_cli.cli import cli

        result = cli_runner.invoke(cli, ['search-employee'])
        assert result.exit_code != 0
        assert 'Missing argument' in result.output or 'required' in result.output.lower()

    def test_search_employee_error_handling(self, cli_runner, mock_odoo_client):
        """Test search-employee error handling"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.search_employee.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.search_employees.side_effect = Exception("Model not found")

            result = cli_runner.invoke(cli, [
                'search-employee', 'John', '--json'
            ])

            assert result.exit_code == 3  # Data error
            output = json.loads(result.output)
            assert output['success'] is False
            assert output['error_type'] == 'data'