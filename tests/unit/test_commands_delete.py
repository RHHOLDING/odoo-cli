"""
Unit tests for DELETE command.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch
import json

from odoo_cli.cli import cli
from odoo_cli.commands.delete import delete
from odoo_cli.models.context import CliContext


@pytest.fixture
def mock_context():
    """Create mock CLI context"""
    context = Mock(spec=CliContext)
    context.client = Mock()
    context.console = Mock()
    context.json_mode = False

    # Setup default client mock behavior
    context.client.execute.return_value = True

    return context


@pytest.fixture
def runner():
    """Create Click test runner"""
    return CliRunner()


class TestDeleteCommandSuccess:
    """Test successful DELETE command scenarios"""

    @patch('click.confirm')
    def test_delete_single_record_with_confirmation(self, mock_confirm, runner, mock_context):
        """Test deleting a single record with user confirmation"""
        mock_confirm.return_value = True  # User confirms

        result = runner.invoke(
            delete,
            ['res.partner', '123'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_confirm.assert_called_once()
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'unlink', [123]
        )

    @patch('click.confirm')
    def test_delete_single_record_cancelled(self, mock_confirm, runner, mock_context):
        """Test user cancels deletion"""
        mock_confirm.return_value = False  # User cancels

        result = runner.invoke(
            delete,
            ['res.partner', '123'],
            obj=mock_context
        )

        assert result.exit_code == 130  # Cancelled exit code
        mock_confirm.assert_called_once()
        mock_context.client.execute.assert_not_called()

    def test_delete_with_force_flag(self, runner, mock_context):
        """Test --force flag bypasses confirmation"""
        result = runner.invoke(
            delete,
            ['res.partner', '123', '--force'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'unlink', [123]
        )

    @patch('click.confirm')
    def test_delete_multiple_records(self, mock_confirm, runner, mock_context):
        """Test deleting multiple records"""
        mock_confirm.return_value = True

        result = runner.invoke(
            delete,
            ['res.partner', '1,2,3'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'unlink', [1, 2, 3]
        )

    def test_delete_json_output(self, runner, mock_context):
        """Test JSON output format (bypasses confirmation)"""
        result = runner.invoke(
            delete,
            ['res.partner', '123', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['success'] is True
        assert output['deleted'] is True
        assert output['ids'] == [123]
        assert output['count'] == 1
        assert output['model'] == 'res.partner'

    def test_delete_json_output_multiple_records(self, runner, mock_context):
        """Test JSON output with multiple records"""
        result = runner.invoke(
            delete,
            ['res.partner', '1,2,3', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['success'] is True
        assert output['ids'] == [1, 2, 3]
        assert output['count'] == 3

    def test_delete_force_and_json(self, runner, mock_context):
        """Test combining --force and --json flags"""
        result = runner.invoke(
            delete,
            ['res.partner', '123', '--force', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['success'] is True


class TestDeleteCommandErrors:
    """Test error handling"""

    def test_invalid_ids_non_numeric(self, runner, mock_context):
        """Test error when IDs are not numeric"""
        result = runner.invoke(
            delete,
            ['res.partner', 'abc', '--force'],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_invalid_ids_mixed(self, runner, mock_context):
        """Test error when IDs contain non-numeric values"""
        result = runner.invoke(
            delete,
            ['res.partner', '123,abc,456', '--force'],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_odoo_error(self, runner, mock_context):
        """Test Odoo execution error handling"""
        mock_context.client.execute.side_effect = Exception("Record does not exist")

        result = runner.invoke(
            delete,
            ['res.partner', '123', '--force'],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_odoo_error_json_mode(self, runner, mock_context):
        """Test Odoo error in JSON mode"""
        mock_context.client.execute.side_effect = Exception("Access denied")

        result = runner.invoke(
            delete,
            ['res.partner', '123', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 3
        error = json.loads(result.output)
        assert error['success'] is False
        assert error['error_type'] == 'odoo_error'
        assert 'Access denied' in error['error']

    def test_invalid_ids_json_mode(self, runner, mock_context):
        """Test invalid IDs error in JSON mode"""
        result = runner.invoke(
            delete,
            ['res.partner', 'invalid', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 3
        error = json.loads(result.output)
        assert error['success'] is False
        assert error['error_type'] == 'invalid_ids'


class TestDeleteCommandConfirmation:
    """Test confirmation prompt logic"""

    @patch('click.confirm')
    def test_confirmation_shows_warning(self, mock_confirm, runner, mock_context):
        """Test that confirmation prompt is shown with warning"""
        mock_confirm.return_value = True

        result = runner.invoke(
            delete,
            ['res.partner', '123'],
            obj=mock_context
        )

        assert result.exit_code == 0
        # Confirm should be called
        mock_confirm.assert_called_once()

    def test_force_skips_confirmation(self, runner, mock_context):
        """Test --force skips confirmation"""
        with patch('click.confirm') as mock_confirm:
            result = runner.invoke(
                delete,
                ['res.partner', '123', '--force'],
                obj=mock_context
            )

            assert result.exit_code == 0
            # Confirm should NOT be called
            mock_confirm.assert_not_called()

    def test_json_skips_confirmation(self, runner, mock_context):
        """Test --json skips confirmation"""
        with patch('click.confirm') as mock_confirm:
            result = runner.invoke(
                delete,
                ['res.partner', '123', '--json'],
                obj=mock_context
            )

            assert result.exit_code == 0
            # Confirm should NOT be called
            mock_confirm.assert_not_called()

    @patch('click.confirm')
    def test_confirmation_default_false(self, mock_confirm, runner, mock_context):
        """Test confirmation default is False (safe default)"""
        mock_confirm.return_value = False

        result = runner.invoke(
            delete,
            ['res.partner', '123'],
            obj=mock_context
        )

        # Should be cancelled
        assert result.exit_code == 130
        # Verify default=False was passed
        mock_confirm.assert_called_once()
        call_kwargs = mock_confirm.call_args[1]
        assert call_kwargs.get('default') is False


class TestDeleteCommandEdgeCases:
    """Test edge cases and special scenarios"""

    def test_delete_single_id_with_spaces(self, runner, mock_context):
        """Test ID parsing with spaces"""
        result = runner.invoke(
            delete,
            ['res.partner', ' 123 ', '--force'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'unlink', [123]
        )

    def test_delete_multiple_ids_with_spaces(self, runner, mock_context):
        """Test multiple IDs with spaces around commas"""
        result = runner.invoke(
            delete,
            ['res.partner', '1 , 2 , 3', '--force'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'unlink', [1, 2, 3]
        )

    @patch('click.confirm')
    def test_delete_large_batch(self, mock_confirm, runner, mock_context):
        """Test deleting many records at once"""
        mock_confirm.return_value = True
        ids = ','.join(str(i) for i in range(1, 101))  # 100 IDs

        result = runner.invoke(
            delete,
            ['res.partner', ids],
            obj=mock_context
        )

        assert result.exit_code == 0
        expected_ids = list(range(1, 101))
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'unlink', expected_ids
        )


class TestDeleteCommandIntegration:
    """Integration tests for complete DELETE workflow"""

    @patch('click.confirm')
    def test_full_workflow_with_confirmation(self, mock_confirm, runner, mock_context):
        """Test complete workflow: parse -> confirm -> delete"""
        mock_confirm.return_value = True

        result = runner.invoke(
            delete,
            ['res.partner', '123,456'],
            obj=mock_context
        )

        assert result.exit_code == 0
        # Confirmation shown
        mock_confirm.assert_called_once()
        # Delete executed
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'unlink', [123, 456]
        )

    def test_full_workflow_force_mode(self, runner, mock_context):
        """Test workflow with --force (no confirmation)"""
        result = runner.invoke(
            delete,
            ['sale.order', '1,2,3', '--force'],
            obj=mock_context
        )

        assert result.exit_code == 0
        # Delete executed
        mock_context.client.execute.assert_called_once_with(
            'sale.order', 'unlink', [1, 2, 3]
        )

    def test_full_workflow_json_mode(self, runner, mock_context):
        """Test workflow with --json (no confirmation, JSON output)"""
        result = runner.invoke(
            delete,
            ['res.partner', '123', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        # JSON output
        output = json.loads(result.output)
        assert output['success'] is True
        assert output['ids'] == [123]
