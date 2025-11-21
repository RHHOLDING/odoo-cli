"""
Unit tests for field parsing and validation utilities.
"""

import pytest
from unittest.mock import Mock
from odoo_cli.field_utils.field_parser import (
    parse_field_values,
    validate_fields,
    is_float,
    format_field_validation_error
)


class TestIsFloat:
    """Test is_float helper function"""

    def test_valid_float(self):
        assert is_float("123.45") is True
        assert is_float("0.001") is True
        assert is_float("-19.99") is True

    def test_valid_integer(self):
        # Integers are also valid floats
        assert is_float("123") is True
        assert is_float("-456") is True
        assert is_float("0") is True

    def test_invalid_float(self):
        assert is_float("abc") is False
        assert is_float("12.34.56") is False
        assert is_float("") is False
        assert is_float("12a34") is False


class TestParseFieldValues:
    """Test parse_field_values function"""

    def test_parse_string_with_double_quotes(self):
        result = parse_field_values(('name="Test Partner"',))
        assert result == {'name': 'Test Partner'}

    def test_parse_string_with_single_quotes(self):
        result = parse_field_values(("name='Test Partner'",))
        assert result == {'name': 'Test Partner'}

    def test_parse_string_without_quotes(self):
        result = parse_field_values(('description=No quotes needed',))
        assert result == {'description': 'No quotes needed'}

    def test_parse_integer(self):
        result = parse_field_values(('partner_id=123',))
        assert result == {'partner_id': 123}
        assert isinstance(result['partner_id'], int)

    def test_parse_negative_integer(self):
        result = parse_field_values(('value=-456',))
        assert result == {'value': -456}
        assert isinstance(result['value'], int)

    def test_parse_float(self):
        result = parse_field_values(('price=19.99',))
        assert result == {'price': 19.99}
        assert isinstance(result['price'], float)

    def test_parse_boolean_true(self):
        result = parse_field_values(('active=true',))
        assert result == {'active': True}
        assert isinstance(result['active'], bool)

    def test_parse_boolean_false(self):
        result = parse_field_values(('active=false',))
        assert result == {'active': False}
        assert isinstance(result['active'], bool)

    def test_parse_boolean_case_insensitive(self):
        result = parse_field_values(('active=True', 'inactive=FALSE'))
        assert result == {'active': True, 'inactive': False}

    def test_parse_null(self):
        result = parse_field_values(('parent_id=null',))
        assert result == {'parent_id': False}

    def test_parse_none(self):
        result = parse_field_values(('parent_id=none',))
        assert result == {'parent_id': False}

    def test_parse_list_of_integers(self):
        result = parse_field_values(('category_ids=[1,2,3]',))
        assert result == {'category_ids': [1, 2, 3]}

    def test_parse_list_of_strings(self):
        result = parse_field_values(('tags=["tag1","tag2"]',))
        assert result == {'tags': ['tag1', 'tag2']}

    def test_parse_empty_list(self):
        result = parse_field_values(('category_ids=[]',))
        assert result == {'category_ids': []}

    def test_parse_multiple_fields(self):
        result = parse_field_values((
            'name="Test"',
            'partner_id=123',
            'active=true',
            'price=19.99'
        ))
        assert result == {
            'name': 'Test',
            'partner_id': 123,
            'active': True,
            'price': 19.99
        }

    def test_parse_field_with_equals_in_value(self):
        # Value contains '=' - should split only on first '='
        result = parse_field_values(('note="Formula: x=y+z"',))
        assert result == {'note': 'Formula: x=y+z'}

    def test_parse_empty_string_value(self):
        result = parse_field_values(('name=""',))
        assert result == {'name': ''}

    def test_invalid_format_no_equals(self):
        with pytest.raises(ValueError, match="Invalid field format"):
            parse_field_values(('invalid_field',))

    def test_invalid_format_empty_key(self):
        with pytest.raises(ValueError, match="Field name cannot be empty"):
            parse_field_values(('=value',))

    def test_whitespace_handling(self):
        result = parse_field_values(('  name  =  "Test"  ',))
        assert result == {'name': 'Test'}


class TestValidateFields:
    """Test validate_fields function"""

    @pytest.fixture
    def mock_client(self):
        """Create mock OdooClient with fields_get method"""
        client = Mock()
        client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False, 'store': True},
            'email': {'type': 'char', 'readonly': False, 'store': True},
            'partner_id': {'type': 'many2one', 'readonly': False, 'store': True},
            'active': {'type': 'boolean', 'readonly': False, 'store': True},
            'amount_total': {'type': 'float', 'readonly': False, 'store': True},
            'create_date': {'type': 'datetime', 'readonly': True, 'store': True},
            'computed_field': {'type': 'char', 'readonly': True, 'store': False},
            'category_ids': {'type': 'many2many', 'readonly': False, 'store': True},
        }
        return client

    def test_valid_fields_pass(self, mock_client):
        fields = {'name': 'Test', 'email': 'test@test.com'}
        # Should not raise
        validate_fields(mock_client, 'res.partner', fields)

    def test_valid_integer_field(self, mock_client):
        fields = {'partner_id': 123}
        # Should not raise
        validate_fields(mock_client, 'res.partner', fields)

    def test_valid_boolean_field(self, mock_client):
        fields = {'active': True}
        # Should not raise
        validate_fields(mock_client, 'res.partner', fields)

    def test_valid_float_field(self, mock_client):
        fields = {'amount_total': 19.99}
        # Should not raise
        validate_fields(mock_client, 'res.partner', fields)

    def test_valid_many2one_clear(self, mock_client):
        # False is valid for many2one (clears the relation)
        fields = {'partner_id': False}
        # Should not raise
        validate_fields(mock_client, 'res.partner', fields)

    def test_valid_many2many_list(self, mock_client):
        fields = {'category_ids': [1, 2, 3]}
        # Should not raise
        validate_fields(mock_client, 'res.partner', fields)

    def test_invalid_field_name(self, mock_client):
        fields = {'invalid_field': 'value'}
        with pytest.raises(ValueError, match="does not exist"):
            validate_fields(mock_client, 'res.partner', fields)

    def test_invalid_field_suggestion(self, mock_client):
        # Field name similar to existing field
        fields = {'nam': 'Test'}  # Similar to 'name'
        with pytest.raises(ValueError, match="Did you mean"):
            validate_fields(mock_client, 'res.partner', fields)

    def test_readonly_stored_field_allowed(self, mock_client):
        # Readonly fields with store=True are allowed (e.g., system fields)
        # Only computed fields (readonly + store=False) are rejected
        fields = {'create_date': '2025-11-21'}
        # Should not raise - stored readonly fields can be set in some contexts
        validate_fields(mock_client, 'res.partner', fields)

    def test_readonly_field_skip(self, mock_client):
        fields = {'create_date': '2025-11-21'}
        # With skip_readonly=False, should not raise
        validate_fields(mock_client, 'res.partner', fields, skip_readonly=False)

    def test_computed_field_error(self, mock_client):
        fields = {'computed_field': 'value'}
        with pytest.raises(ValueError, match="readonly"):
            validate_fields(mock_client, 'res.partner', fields)

    def test_type_mismatch_integer(self, mock_client):
        fields = {'partner_id': 'not_an_integer'}
        with pytest.raises(ValueError, match="expects many2one"):
            validate_fields(mock_client, 'res.partner', fields)

    def test_type_mismatch_boolean(self, mock_client):
        fields = {'active': 'yes'}  # Should be bool
        with pytest.raises(ValueError, match="expects boolean"):
            validate_fields(mock_client, 'res.partner', fields)

    def test_integer_for_float_allowed(self, mock_client):
        # Integer should be allowed for float fields
        fields = {'amount_total': 100}  # int instead of float
        # Should not raise
        validate_fields(mock_client, 'res.partner', fields)

    def test_model_not_found(self, mock_client):
        mock_client.fields_get.side_effect = Exception("Model not found")
        fields = {'name': 'Test'}
        with pytest.raises(ValueError, match="Could not fetch field definitions"):
            validate_fields(mock_client, 'invalid.model', fields)


class TestFormatFieldValidationError:
    """Test error formatting function"""

    def test_format_error_message(self):
        error = ValueError("Field 'test' does not exist")
        result = format_field_validation_error(error, 'res.partner', 'test')

        assert "Validation Error" in result
        assert "res.partner.test" in result
        assert "Field 'test' does not exist" in result
        assert "odoo get-fields res.partner" in result
        assert "--no-validate" in result


class TestIntegration:
    """Integration tests combining parsing and validation"""

    @pytest.fixture
    def mock_client(self):
        """Create mock OdooClient"""
        client = Mock()
        client.fields_get.return_value = {
            'name': {'type': 'char', 'readonly': False, 'store': True},
            'email': {'type': 'char', 'readonly': False, 'store': True},
            'partner_id': {'type': 'many2one', 'readonly': False, 'store': True},
            'active': {'type': 'boolean', 'readonly': False, 'store': True},
        }
        return client

    def test_parse_and_validate_success(self, mock_client):
        # Parse fields
        fields = parse_field_values((
            'name="Test Partner"',
            'email="test@test.com"',
            'partner_id=123',
            'active=true'
        ))

        # Validate
        validate_fields(mock_client, 'res.partner', fields)

        # Should not raise, fields should be parsed correctly
        assert fields == {
            'name': 'Test Partner',
            'email': 'test@test.com',
            'partner_id': 123,
            'active': True
        }

    def test_parse_and_validate_type_error(self, mock_client):
        # Parse with wrong type
        fields = parse_field_values(('active="yes"',))  # Should be bool, got str

        # Validate should catch type error
        with pytest.raises(ValueError, match="expects boolean"):
            validate_fields(mock_client, 'res.partner', fields)
