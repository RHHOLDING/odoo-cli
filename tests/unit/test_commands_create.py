"""
Unit tests for CREATE command.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from odoo_cli.commands.create import create
from odoo_cli.models.context import CliContext


@pytest.fixture
def mock_context():
    """Create mock CLI context"""
    context = Mock(spec=CliContext)
    context.client = Mock()
    context.console = Mock()
    context.json_mode = False
    return context


@pytest.fixture
def runner():
    """Create Click test runner"""
    return CliRunner()


class TestCreateCommandSuccess:
    """Test successful record creation scenarios"""

    def test_create_simple_record(self, runner, mock_context):
        """Test creating a simple record with basic fields"""
        # Mock client.execute to return record ID
        mock_context.client.execute.return_value = 123
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False},
            'email': {'type': 'char', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'name=Test', '-f', 'email=test@test.com'],
            obj=mock_context
        )

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify client.execute was called correctly
        mock_context.client.execute.assert_called_once_with(
            'res.partner',
            'create',
            {'name': 'Test', 'email': 'test@test.com'}
        )

        # Verify console was used for output (success message)
        assert mock_context.console.print.called
        # Check that success message contains record ID
        calls = [str(call) for call in mock_context.console.print.call_args_list]
        assert any('123' in call for call in calls)

    def test_create_with_multiple_field_types(self, runner, mock_context):
        """Test creating record with different field types"""
        mock_context.client.execute.return_value = 456
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False},
            'partner_id': {'type': 'many2one', 'readonly': False},
            'active': {'type': 'boolean', 'readonly': False},
            'price': {'type': 'float', 'readonly': False}
        }

        result = runner.invoke(
            create,
            [
                'sale.order',
                '-f', 'name="Test Order"',
                '-f', 'partner_id=123',
                '-f', 'active=true',
                '-f', 'price=99.99'
            ],
            obj=mock_context
        )

        assert result.exit_code == 0

        # Verify parsed values have correct types
        call_args = mock_context.client.execute.call_args
        field_dict = call_args[0][2]
        assert field_dict['name'] == 'Test Order'
        assert field_dict['partner_id'] == 123
        assert field_dict['active'] is True
        assert field_dict['price'] == 99.99

    def test_create_with_json_output(self, runner, mock_context):
        """Test JSON output mode"""
        mock_context.client.execute.return_value = 789
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'name=Test', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)
        assert output_data['success'] is True
        assert output_data['id'] == 789
        assert output_data['model'] == 'res.partner'
        assert output_data['fields']['name'] == 'Test'

    def test_create_with_no_validate_flag(self, runner, mock_context):
        """Test --no-validate flag skips validation"""
        mock_context.client.execute.return_value = 111

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'name=Test', '--no-validate'],
            obj=mock_context
        )

        assert result.exit_code == 0

        # Verify fields_get was NOT called (validation skipped)
        mock_context.client.fields_get.assert_not_called()

    def test_create_with_quoted_strings(self, runner, mock_context):
        """Test quoted string values"""
        mock_context.client.execute.return_value = 222
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False},
            'note': {'type': 'text', 'readonly': False}
        }

        result = runner.invoke(
            create,
            [
                'res.partner',
                '-f', 'name="Test Partner"',
                '-f', 'note="Long description here"'
            ],
            obj=mock_context
        )

        assert result.exit_code == 0

        # Verify quotes were removed
        call_args = mock_context.client.execute.call_args
        field_dict = call_args[0][2]
        assert field_dict['name'] == 'Test Partner'
        assert field_dict['note'] == 'Long description here'

    def test_create_with_unquoted_string(self, runner, mock_context):
        """Test unquoted string values"""
        mock_context.client.execute.return_value = 333
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'name=SimpleValue'],
            obj=mock_context
        )

        assert result.exit_code == 0

        call_args = mock_context.client.execute.call_args
        field_dict = call_args[0][2]
        assert field_dict['name'] == 'SimpleValue'

    def test_create_with_list_field(self, runner, mock_context):
        """Test list/array field values"""
        mock_context.client.execute.return_value = 444
        mock_context.client.fields_get.return_value = {
            'category_ids': {'type': 'many2many', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'category_ids=[1,2,3]'],
            obj=mock_context
        )

        assert result.exit_code == 0

        call_args = mock_context.client.execute.call_args
        field_dict = call_args[0][2]
        assert field_dict['category_ids'] == [1, 2, 3]

    def test_create_with_boolean_false(self, runner, mock_context):
        """Test boolean false value"""
        mock_context.client.execute.return_value = 555
        mock_context.client.fields_get.return_value = {
            'active': {'type': 'boolean', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'active=false'],
            obj=mock_context
        )

        assert result.exit_code == 0

        call_args = mock_context.client.execute.call_args
        field_dict = call_args[0][2]
        assert field_dict['active'] is False


class TestCreateCommandErrors:
    """Test error handling scenarios"""

    def test_create_invalid_field_format(self, runner, mock_context):
        """Test error on invalid field format (missing =)"""
        result = runner.invoke(
            create,
            ['res.partner', '-f', 'invalid_field'],
            obj=mock_context
        )

        assert result.exit_code == 1

    def test_create_field_not_exists(self, runner, mock_context):
        """Test error when field doesn't exist"""
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'invalid_field=value'],
            obj=mock_context
        )

        assert result.exit_code == 1

    def test_create_readonly_computed_field(self, runner, mock_context):
        """Test error on readonly computed field"""
        mock_context.client.fields_get.return_value = {
            'computed_field': {'type': 'char', 'readonly': True, 'store': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'computed_field=value'],
            obj=mock_context
        )

        assert result.exit_code == 1

    def test_create_type_mismatch(self, runner, mock_context):
        """Test error on field type mismatch"""
        mock_context.client.fields_get.return_value = {
            'active': {'type': 'boolean', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'active="not_a_boolean"'],
            obj=mock_context
        )

        assert result.exit_code == 1

    def test_create_odoo_error(self, runner, mock_context):
        """Test handling of Odoo server errors"""
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False}
        }
        mock_context.client.execute.side_effect = Exception("Odoo server error: Access denied")

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'name=Test'],
            obj=mock_context
        )

        assert result.exit_code == 1

    def test_create_invalid_field_format_json_mode(self, runner, mock_context):
        """Test JSON error output on parsing error"""
        result = runner.invoke(
            create,
            ['res.partner', '-f', 'invalid', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 1

        # Parse JSON error response
        output_data = json.loads(result.output)
        assert output_data['success'] is False
        assert output_data['error_type'] == 'field_parsing'
        assert 'suggestion' in output_data

    def test_create_validation_error_json_mode(self, runner, mock_context):
        """Test JSON error output on validation error"""
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'invalid_field=value', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 1

        output_data = json.loads(result.output)
        assert output_data['success'] is False
        assert output_data['error_type'] == 'field_validation'
        assert 'odoo get-fields' in output_data['suggestion']

    def test_create_odoo_error_json_mode(self, runner, mock_context):
        """Test JSON error output on Odoo error"""
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False}
        }
        mock_context.client.execute.side_effect = Exception("Server error")

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'name=Test', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 1

        output_data = json.loads(result.output)
        assert output_data['success'] is False
        assert output_data['error_type'] == 'odoo_error'


class TestCreateCommandValidation:
    """Test field validation logic"""

    def test_create_validation_called_by_default(self, runner, mock_context):
        """Test that validation is called by default"""
        mock_context.client.execute.return_value = 123
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'name=Test'],
            obj=mock_context
        )

        assert result.exit_code == 0

        # Verify fields_get was called (validation enabled)
        mock_context.client.fields_get.assert_called_once_with('res.partner')

    def test_create_validation_skipped_with_flag(self, runner, mock_context):
        """Test that --no-validate skips validation"""
        mock_context.client.execute.return_value = 123

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'name=Test', '--no-validate'],
            obj=mock_context
        )

        assert result.exit_code == 0

        # Verify fields_get was NOT called
        mock_context.client.fields_get.assert_not_called()

    def test_create_with_field_suggestion(self, runner, mock_context):
        """Test helpful field suggestions on typos"""
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False},
            'email': {'type': 'char', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'nam=Test'],  # Typo: 'nam' instead of 'name'
            obj=mock_context
        )

        assert result.exit_code == 1


class TestCreateCommandEdgeCases:
    """Test edge cases and special scenarios"""

    def test_create_with_empty_string_value(self, runner, mock_context):
        """Test creating with empty string value"""
        mock_context.client.execute.return_value = 123
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'name=""'],
            obj=mock_context
        )

        assert result.exit_code == 0

        call_args = mock_context.client.execute.call_args
        field_dict = call_args[0][2]
        assert field_dict['name'] == ''

    def test_create_with_null_value(self, runner, mock_context):
        """Test creating with null/false value"""
        mock_context.client.execute.return_value = 123
        mock_context.client.fields_get.return_value = {
            'parent_id': {'type': 'many2one', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'parent_id=null'],
            obj=mock_context
        )

        assert result.exit_code == 0

        call_args = mock_context.client.execute.call_args
        field_dict = call_args[0][2]
        assert field_dict['parent_id'] is False

    def test_create_with_negative_number(self, runner, mock_context):
        """Test creating with negative number"""
        mock_context.client.execute.return_value = 123
        mock_context.client.fields_get.return_value = {
            'value': {'type': 'integer', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'value=-100'],
            obj=mock_context
        )

        assert result.exit_code == 0

        call_args = mock_context.client.execute.call_args
        field_dict = call_args[0][2]
        assert field_dict['value'] == -100

    def test_create_with_value_containing_equals(self, runner, mock_context):
        """Test field value containing '=' character"""
        mock_context.client.execute.return_value = 123
        mock_context.client.fields_get.return_value = {
            'note': {'type': 'text', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'note="Formula: x=y+z"'],
            obj=mock_context
        )

        assert result.exit_code == 0

        call_args = mock_context.client.execute.call_args
        field_dict = call_args[0][2]
        assert field_dict['note'] == 'Formula: x=y+z'

    def test_create_with_many_fields(self, runner, mock_context):
        """Test creating with many fields at once"""
        mock_context.client.execute.return_value = 123
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False},
            'email': {'type': 'char', 'readonly': False},
            'phone': {'type': 'char', 'readonly': False},
            'street': {'type': 'char', 'readonly': False},
            'city': {'type': 'char', 'readonly': False},
            'zip': {'type': 'char', 'readonly': False}
        }

        result = runner.invoke(
            create,
            [
                'res.partner',
                '-f', 'name=Test',
                '-f', 'email=test@test.com',
                '-f', 'phone="+49123"',  # Quote phone to avoid parsing issues
                '-f', 'street="Main St"',
                '-f', 'city=Berlin',
                '-f', 'zip="10115"'  # Quote zip to keep as string
            ],
            obj=mock_context
        )

        assert result.exit_code == 0

        call_args = mock_context.client.execute.call_args
        field_dict = call_args[0][2]
        assert len(field_dict) == 6
        assert field_dict['name'] == 'Test'
        assert field_dict['city'] == 'Berlin'

    def test_create_keyboard_interrupt(self, runner, mock_context):
        """Test handling of keyboard interrupt (Ctrl+C)"""
        mock_context.client.fields_get.side_effect = KeyboardInterrupt()

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'name=Test'],
            obj=mock_context
        )

        assert result.exit_code == 130  # Standard exit code for SIGINT
        assert 'Cancelled' in result.output or result.output == ''


class TestCreateCommandOutput:
    """Test output formatting and messages"""

    def test_create_success_message_format(self, runner, mock_context):
        """Test success message contains expected information"""
        mock_context.client.execute.return_value = 999
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'name=Test'],
            obj=mock_context
        )

        assert result.exit_code == 0

    def test_create_json_output_structure(self, runner, mock_context):
        """Test JSON output has correct structure"""
        mock_context.client.execute.return_value = 777
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False},
            'email': {'type': 'char', 'readonly': False}
        }

        result = runner.invoke(
            create,
            ['res.partner', '-f', 'name=Test', '-f', 'email=test@test.com', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0

        output_data = json.loads(result.output)
        assert 'success' in output_data
        assert 'id' in output_data
        assert 'model' in output_data
        assert 'fields' in output_data
        assert output_data['success'] is True
        assert output_data['id'] == 777
        assert output_data['model'] == 'res.partner'
        assert 'name' in output_data['fields']
        assert 'email' in output_data['fields']


class TestCreateCommandIntegration:
    """Integration tests combining multiple features"""

    def test_create_full_workflow(self, runner, mock_context):
        """Test complete create workflow with validation and execution"""
        mock_context.client.execute.return_value = 12345
        mock_context.client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False},
            'email': {'type': 'char', 'readonly': False},
            'active': {'type': 'boolean', 'readonly': False}
        }

        result = runner.invoke(
            create,
            [
                'res.partner',
                '-f', 'name="Integration Test"',
                '-f', 'email="integration@test.com"',
                '-f', 'active=true'
            ],
            obj=mock_context
        )

        # Verify success
        assert result.exit_code == 0

        # Verify validation was called
        mock_context.client.fields_get.assert_called_once_with('res.partner')

        # Verify execution was called correctly
        mock_context.client.execute.assert_called_once()
        call_args = mock_context.client.execute.call_args
        assert call_args[0][0] == 'res.partner'
        assert call_args[0][1] == 'create'
        field_dict = call_args[0][2]
        assert field_dict['name'] == 'Integration Test'
        assert field_dict['email'] == 'integration@test.com'
        assert field_dict['active'] is True
