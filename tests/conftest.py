"""
Pytest configuration and shared fixtures
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from click.testing import CliRunner
import json


@pytest.fixture
def cli_runner():
    """Provide a Click CLI test runner"""
    return CliRunner()


@pytest.fixture
def mock_odoo_client():
    """Mock OdooClient for testing"""
    client = MagicMock()
    client.url = "https://test.odoo.com"
    client.db = "test_db"
    client.username = "test@example.com"
    client.uid = 1
    client.connect.return_value = None
    return client


@pytest.fixture
def mock_config():
    """Mock configuration values"""
    return {
        'url': 'https://test.odoo.com',
        'db': 'test_db',
        'username': 'test@example.com',
        'password': 'test_password',
        'timeout': 30,
        'verify_ssl': True
    }


@pytest.fixture
def sample_partners():
    """Sample partner records for testing"""
    return [
        {
            'id': 1,
            'name': 'Test Company',
            'email': 'company@test.com',
            'is_company': True,
            'phone': '+1234567890'
        },
        {
            'id': 2,
            'name': 'John Doe',
            'email': 'john@test.com',
            'is_company': False,
            'phone': '+0987654321'
        }
    ]


@pytest.fixture
def sample_employees():
    """Sample employee records for testing"""
    return [
        {
            'id': 1,
            'name': 'John Smith',
            'work_email': 'john.smith@company.com',
            'department_id': [1, 'Sales'],
            'job_id': [1, 'Sales Manager'],
            'user_id': [10, 'john.smith']
        },
        {
            'id': 2,
            'name': 'Jane Doe',
            'work_email': 'jane.doe@company.com',
            'department_id': [2, 'HR'],
            'job_id': [2, 'HR Manager'],
            'user_id': [11, 'jane.doe']
        }
    ]


@pytest.fixture
def sample_holidays():
    """Sample holiday/leave records for testing"""
    return [
        {
            'id': 1,
            'employee_id': [1, 'John Smith'],
            'holiday_status_id': [1, 'Annual Leave'],
            'date_from': '2024-01-01 08:00:00',
            'date_to': '2024-01-05 17:00:00',
            'state': 'validate',
            'number_of_days': 5
        },
        {
            'id': 2,
            'employee_id': [2, 'Jane Doe'],
            'holiday_status_id': [2, 'Sick Leave'],
            'date_from': '2024-02-01 08:00:00',
            'date_to': '2024-02-02 17:00:00',
            'state': 'draft',
            'number_of_days': 2
        }
    ]


@pytest.fixture
def sample_models():
    """Sample model list for testing"""
    return [
        'account.move',
        'account.move.line',
        'hr.employee',
        'hr.leave',
        'res.company',
        'res.partner',
        'res.users',
        'sale.order',
        'sale.order.line'
    ]


@pytest.fixture
def sample_fields():
    """Sample field definitions for testing"""
    return {
        'name': {
            'type': 'char',
            'string': 'Name',
            'required': True,
            'help': 'The name of the partner'
        },
        'email': {
            'type': 'char',
            'string': 'Email',
            'required': False,
            'help': 'Email address'
        },
        'is_company': {
            'type': 'boolean',
            'string': 'Is a Company',
            'required': False,
            'help': 'Check if the contact is a company'
        },
        'partner_id': {
            'type': 'many2one',
            'string': 'Partner',
            'relation': 'res.partner',
            'required': False
        }
    }


@pytest.fixture
def json_success_response():
    """Standard JSON success response structure"""
    def _response(data, count=None, truncated=False):
        response = {
            'success': True,
            'data': data
        }
        if count is not None:
            response['count'] = count
        if truncated:
            response['truncated'] = truncated
        return response
    return _response


@pytest.fixture
def json_error_response():
    """Standard JSON error response structure"""
    def _response(error, error_type, details=None, suggestion=None):
        response = {
            'success': False,
            'error': error,
            'error_type': error_type
        }
        if details:
            response['details'] = details
        if suggestion:
            response['suggestion'] = suggestion
        return response
    return _response