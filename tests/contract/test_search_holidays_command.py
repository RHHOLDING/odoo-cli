"""
Contract tests for the 'search-holidays' command
"""

import pytest
import json
from unittest.mock import patch
from click.testing import CliRunner


class TestSearchHolidaysCommand:
    """Test suite for odoo search-holidays command"""

    def test_search_holidays_command_exists(self, cli_runner):
        """Test that search-holidays command is available"""
        from odoo_cli.cli import cli

        result = cli_runner.invoke(cli, ['search-holidays', '--help'])
        assert result.exit_code == 0
        assert 'Search time-off records' in result.output

    def test_search_holidays_no_filters(self, cli_runner, mock_odoo_client, sample_holidays):
        """Test holiday search without filters"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.search_holidays.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.search_holidays.return_value = sample_holidays

            result = cli_runner.invoke(cli, ['search-holidays'])

            assert result.exit_code == 0
            mock_odoo_client.search_holidays.assert_called_once_with(
                employee_name=None,
                state=None,
                limit=20
            )

    def test_search_holidays_with_employee(self, cli_runner, mock_odoo_client, sample_holidays):
        """Test holiday search filtered by employee"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.search_holidays.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.search_holidays.return_value = [sample_holidays[0]]

            result = cli_runner.invoke(cli, [
                'search-holidays', '--employee', 'John'
            ])

            assert result.exit_code == 0
            mock_odoo_client.search_holidays.assert_called_once_with(
                employee_name='John',
                state=None,
                limit=20
            )

    def test_search_holidays_with_state(self, cli_runner, mock_odoo_client, sample_holidays):
        """Test holiday search filtered by state"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.search_holidays.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            validated = [h for h in sample_holidays if h['state'] == 'validate']
            mock_odoo_client.search_holidays.return_value = validated

            result = cli_runner.invoke(cli, [
                'search-holidays', '--state', 'validate'
            ])

            assert result.exit_code == 0
            mock_odoo_client.search_holidays.assert_called_once_with(
                employee_name=None,
                state='validate',
                limit=20
            )

    def test_search_holidays_all_filters(self, cli_runner, mock_odoo_client):
        """Test holiday search with all filters"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.search_holidays.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.search_holidays.return_value = []

            result = cli_runner.invoke(cli, [
                'search-holidays',
                '--employee', 'Jane',
                '--state', 'draft',
                '--limit', '50'
            ])

            assert result.exit_code == 0
            mock_odoo_client.search_holidays.assert_called_once_with(
                employee_name='Jane',
                state='draft',
                limit=50
            )

    def test_search_holidays_json_output(self, cli_runner, mock_odoo_client, sample_holidays):
        """Test holiday search with JSON output"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.search_holidays.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.search_holidays.return_value = sample_holidays

            result = cli_runner.invoke(cli, [
                'search-holidays', '--json'
            ])

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output['success'] is True
            assert len(output['data']) == 2
            assert 'employee_id' in output['data'][0]
            assert 'state' in output['data'][0]

    def test_search_holidays_invalid_state(self, cli_runner):
        """Test holiday search with invalid state value"""
        from odoo_cli.cli import cli

        result = cli_runner.invoke(cli, [
            'search-holidays', '--state', 'invalid_state'
        ])

        # Should either fail or show error message
        assert result.exit_code != 0 or 'invalid' in result.output.lower()

    def test_search_holidays_rich_output(self, cli_runner, mock_odoo_client, sample_holidays):
        """Test holiday search rich table output"""
        from odoo_cli.cli import cli

        with patch('odoo_cli.commands.search_holidays.get_odoo_client') as mock_get_client:
            mock_get_client.return_value = mock_odoo_client
            mock_odoo_client.search_holidays.return_value = sample_holidays

            result = cli_runner.invoke(cli, ['search-holidays'])

            assert result.exit_code == 0
            # Should show relevant headers
            assert 'Employee' in result.output or 'employee' in result.output.lower()
            assert 'State' in result.output or 'state' in result.output.lower()
            assert 'Days' in result.output or 'days' in result.output.lower()