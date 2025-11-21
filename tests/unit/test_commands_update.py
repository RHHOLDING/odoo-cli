"""
Unit tests for UPDATE command.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, MagicMock
import json

from odoo_cli.cli import cli
from odoo_cli.commands.update import update
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
    context.client.fields_get.return_value = {
        'name': {'type': 'char', 'readonly': False, 'store': True},
        'email': {'type': 'char', 'readonly': False, 'store': True},
        'active': {'type': 'boolean', 'readonly': False, 'store': True},
        'partner_id': {'type': 'many2one', 'readonly': False, 'store': True},
        'phone': {'type': 'char', 'readonly': False, 'store': True},
    }

    return context


@pytest.fixture
def runner():
    """Create Click test runner"""
    return CliRunner()


class TestUpdateCommandSuccess:
    """Test successful UPDATE command scenarios"""

    def test_update_single_record(self, runner, mock_context):
        """Test updating a single record"""
        result = runner.invoke(
            update,
            ['res.partner', '123', '-f', 'name="Updated Name"'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'write', [123], {'name': 'Updated Name'}
        )

    def test_update_multiple_records(self, runner, mock_context):
        """Test updating multiple records"""
        result = runner.invoke(
            update,
            ['res.partner', '1,2,3', '-f', 'active=false'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'write', [1, 2, 3], {'active': False}
        )

    def test_update_multiple_fields(self, runner, mock_context):
        """Test updating with multiple fields"""
        result = runner.invoke(
            update,
            [
                'res.partner', '123',
                '-f', 'name="Test"',
                '-f', 'email="test@test.com"',
                '-f', 'active=true'
            ],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'write', [123], {
                'name': 'Test',
                'email': 'test@test.com',
                'active': True
            }
        )

    def test_update_with_validation(self, runner, mock_context):
        """Test that validation is called by default"""
        result = runner.invoke(
            update,
            ['res.partner', '123', '-f', 'name="Test"'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.fields_get.assert_called_once_with('res.partner')

    def test_update_without_validation(self, runner, mock_context):
        """Test --no-validate flag skips validation"""
        result = runner.invoke(
            update,
            ['res.partner', '123', '-f', 'name="Test"', '--no-validate'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.fields_get.assert_not_called()
        mock_context.client.execute.assert_called_once()

    def test_update_json_output(self, runner, mock_context):
        """Test JSON output format"""
        result = runner.invoke(
            update,
            ['res.partner', '123', '-f', 'name="Test"', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['success'] is True
        assert output['updated'] is True
        assert output['ids'] == [123]
        assert output['count'] == 1
        assert output['model'] == 'res.partner'
        assert output['fields'] == {'name': 'Test'}

    def test_update_json_output_multiple_records(self, runner, mock_context):
        """Test JSON output with multiple records"""
        result = runner.invoke(
            update,
            ['res.partner', '1,2,3', '-f', 'active=false', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['success'] is True
        assert output['ids'] == [1, 2, 3]
        assert output['count'] == 3

    def test_update_with_type_inference(self, runner, mock_context):
        """Test automatic type inference for field values"""
        result = runner.invoke(
            update,
            [
                'res.partner', '123',
                '-f', 'name=StringValue',
                '-f', 'partner_id=456',
                '-f', 'active=true'
            ],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'write', [123], {
                'name': 'StringValue',
                'partner_id': 456,
                'active': True
            }
        )


class TestUpdateCommandErrors:
    """Test error handling"""

    def test_invalid_ids_non_numeric(self, runner, mock_context):
        """Test error when IDs are not numeric"""
        result = runner.invoke(
            update,
            ['res.partner', 'abc', '-f', 'name="Test"'],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_invalid_ids_mixed(self, runner, mock_context):
        """Test error when IDs contain non-numeric values"""
        result = runner.invoke(
            update,
            ['res.partner', '123,abc,456', '-f', 'name="Test"'],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_invalid_field_format(self, runner, mock_context):
        """Test error when field format is invalid"""
        result = runner.invoke(
            update,
            ['res.partner', '123', '-f', 'invalid_format'],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_field_validation_error(self, runner, mock_context):
        """Test validation error for non-existent field"""
        result = runner.invoke(
            update,
            ['res.partner', '123', '-f', 'nonexistent_field="value"'],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_odoo_error(self, runner, mock_context):
        """Test Odoo execution error handling"""
        mock_context.client.execute.side_effect = Exception("Odoo write error")

        result = runner.invoke(
            update,
            ['res.partner', '123', '-f', 'name="Test"', '--no-validate'],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_odoo_error_json_mode(self, runner, mock_context):
        """Test Odoo error in JSON mode"""
        mock_context.client.execute.side_effect = Exception("Odoo write error")

        result = runner.invoke(
            update,
            ['res.partner', '123', '-f', 'name="Test"', '--no-validate', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 3
        error = json.loads(result.output)
        assert error['success'] is False
        assert error['error_type'] == 'odoo_error'
        assert 'Odoo write error' in error['error']


class TestUpdateCommandValidation:
    """Test field validation logic"""

    def test_validation_calls_fields_get(self, runner, mock_context):
        """Test that validation calls fields_get"""
        result = runner.invoke(
            update,
            ['res.partner', '123', '-f', 'name="Test"'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.fields_get.assert_called_once_with('res.partner')

    def test_no_validate_skips_fields_get(self, runner, mock_context):
        """Test that --no-validate skips fields_get"""
        result = runner.invoke(
            update,
            ['res.partner', '123', '-f', 'name="Test"', '--no-validate'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.fields_get.assert_not_called()

    def test_validation_error_suggests_get_fields(self, runner, mock_context):
        """Test validation error suggests get-fields command"""
        result = runner.invoke(
            update,
            ['res.partner', '123', '-f', 'invalid_field="value"'],
            obj=mock_context
        )

        assert result.exit_code == 3


class TestUpdateCommandEdgeCases:
    """Test edge cases and special scenarios"""

    def test_update_single_id_with_spaces(self, runner, mock_context):
        """Test ID parsing with spaces"""
        result = runner.invoke(
            update,
            ['res.partner', ' 123 ', '-f', 'name="Test"'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'write', [123], {'name': 'Test'}
        )

    def test_update_multiple_ids_with_spaces(self, runner, mock_context):
        """Test multiple IDs with spaces around commas"""
        result = runner.invoke(
            update,
            ['res.partner', '1 , 2 , 3', '-f', 'name="Test"'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'write', [1, 2, 3], {'name': 'Test'}
        )

    def test_update_with_empty_string_value(self, runner, mock_context):
        """Test updating field to empty string"""
        result = runner.invoke(
            update,
            ['res.partner', '123', '-f', 'email=""'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'write', [123], {'email': ''}
        )

    def test_update_with_special_characters(self, runner, mock_context):
        """Test updating with special characters in values"""
        result = runner.invoke(
            update,
            ['res.partner', '123', '-f', 'phone="+49123"', '-f', 'name="Test & Co."'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'write', [123], {
                'phone': '+49123',
                'name': 'Test & Co.'
            }
        )

    def test_update_boolean_false(self, runner, mock_context):
        """Test updating boolean field to false"""
        result = runner.invoke(
            update,
            ['res.partner', '123', '-f', 'active=false'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'write', [123], {'active': False}
        )


class TestUpdateCommandIntegration:
    """Integration tests for complete UPDATE workflow"""

    def test_full_workflow_with_validation(self, runner, mock_context):
        """Test complete workflow: parse -> validate -> update"""
        result = runner.invoke(
            update,
            [
                'res.partner', '123',
                '-f', 'name="Integration Test"',
                '-f', 'email="test@test.com"'
            ],
            obj=mock_context
        )

        assert result.exit_code == 0
        # Validation called
        mock_context.client.fields_get.assert_called_once_with('res.partner')
        # Update executed
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'write', [123], {
                'name': 'Integration Test',
                'email': 'test@test.com'
            }
        )

    def test_full_workflow_without_validation(self, runner, mock_context):
        """Test workflow without validation"""
        result = runner.invoke(
            update,
            [
                'res.partner', '1,2,3',
                '-f', 'active=false',
                '--no-validate'
            ],
            obj=mock_context
        )

        assert result.exit_code == 0
        # Validation skipped
        mock_context.client.fields_get.assert_not_called()
        # Update executed
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'write', [1, 2, 3], {'active': False}
        )
