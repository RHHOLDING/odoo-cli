"""
Unit tests for CREATE-BULK command.
"""

import pytest
import json
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import Mock, patch, mock_open
import tempfile

from odoo_cli.commands.create_bulk import create_bulk
from odoo_cli.models.context import CliContext


@pytest.fixture
def mock_context():
    """Create mock CLI context"""
    context = Mock(spec=CliContext)
    context.client = Mock()
    context.console = Mock()
    return context


@pytest.fixture
def runner():
    """Create Click test runner"""
    return CliRunner()


@pytest.fixture
def temp_json_file():
    """Create a temporary JSON file with test data"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_data = [
            {'name': 'Partner 1', 'email': 'p1@test.com'},
            {'name': 'Partner 2', 'email': 'p2@test.com'},
            {'name': 'Partner 3', 'email': 'p3@test.com'},
        ]
        json.dump(test_data, f)
        return f.name


class TestCreateBulkSuccess:
    """Test successful CREATE-BULK scenarios"""

    def test_create_bulk_small_batch(self, runner, mock_context, temp_json_file):
        """Test creating small batch of records"""
        mock_context.client.execute.return_value = [101, 102, 103]

        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', temp_json_file, '--batch-size', '100'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.execute.assert_called_once_with(
            'res.partner', 'create', [
                {'name': 'Partner 1', 'email': 'p1@test.com'},
                {'name': 'Partner 2', 'email': 'p2@test.com'},
                {'name': 'Partner 3', 'email': 'p3@test.com'},
            ]
        )

    def test_create_bulk_with_batching(self, runner, mock_context):
        """Test that records are batched correctly"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = [{'name': f'Partner {i}'} for i in range(1, 6)]
            json.dump(test_data, f)
            temp_file = f.name

        # Mock execute to return IDs per batch
        mock_context.client.execute.side_effect = [
            [101, 102],  # First batch
            [103, 104],  # Second batch
            [105],       # Third batch
        ]

        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', temp_file, '--batch-size', '2'],
            obj=mock_context
        )

        assert result.exit_code == 0
        assert mock_context.client.execute.call_count == 3

    def test_create_bulk_json_output(self, runner, mock_context, temp_json_file):
        """Test JSON output format"""
        mock_context.client.execute.return_value = [101, 102, 103]

        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', temp_json_file, '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['success'] is True
        assert output['created'] == 3
        assert output['ids'] == [101, 102, 103]
        assert output['model'] == 'res.partner'

    def test_create_bulk_custom_batch_size(self, runner, mock_context):
        """Test custom batch size"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = [{'name': f'P{i}'} for i in range(1, 11)]
            json.dump(test_data, f)
            temp_file = f.name

        mock_context.client.execute.side_effect = [
            list(range(101, 106)),  # 5 records
            list(range(106, 111)),  # 5 records
        ]

        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', temp_file, '--batch-size', '5'],
            obj=mock_context
        )

        assert result.exit_code == 0
        assert mock_context.client.execute.call_count == 2


class TestCreateBulkErrors:
    """Test error handling"""

    def test_file_not_found(self, runner, mock_context):
        """Test error when file doesn't exist"""
        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', '/nonexistent/file.json'],
            obj=mock_context
        )

        # Click returns 2 for missing files
        assert result.exit_code == 2

    def test_invalid_json(self, runner, mock_context):
        """Test error with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            temp_file = f.name

        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', temp_file],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_json_not_array(self, runner, mock_context):
        """Test error when JSON is not an array"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'name': 'single record'}, f)
            temp_file = f.name

        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', temp_file],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_empty_array(self, runner, mock_context):
        """Test error with empty JSON array"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            temp_file = f.name

        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', temp_file],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_odoo_error_during_batch(self, runner, mock_context, temp_json_file):
        """Test error during Odoo execution"""
        mock_context.client.execute.side_effect = Exception("Odoo error")

        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', temp_json_file],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_error_json_mode(self, runner, mock_context):
        """Test error output in JSON mode"""
        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', '/nonexistent.json', '--json'],
            obj=mock_context
        )

        # Click returns 2 for missing file argument
        assert result.exit_code == 2


class TestCreateBulkBatching:
    """Test batching logic"""

    def test_single_batch(self, runner, mock_context, temp_json_file):
        """Test data within single batch"""
        mock_context.client.execute.return_value = [101, 102, 103]

        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', temp_json_file, '--batch-size', '100'],
            obj=mock_context
        )

        assert result.exit_code == 0
        assert mock_context.client.execute.call_count == 1

    def test_exact_multiple_batches(self, runner, mock_context):
        """Test data that divides evenly into batches"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = [{'name': f'P{i}'} for i in range(1, 11)]
            json.dump(test_data, f)
            temp_file = f.name

        mock_context.client.execute.side_effect = [
            [101, 102, 103, 104, 105],
            [106, 107, 108, 109, 110],
        ]

        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', temp_file, '--batch-size', '5'],
            obj=mock_context
        )

        assert result.exit_code == 0
        assert mock_context.client.execute.call_count == 2

    def test_uneven_batches(self, runner, mock_context):
        """Test data with uneven batch division"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = [{'name': f'P{i}'} for i in range(1, 8)]
            json.dump(test_data, f)
            temp_file = f.name

        mock_context.client.execute.side_effect = [
            [101, 102, 103],
            [104, 105, 106],
            [107],
        ]

        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', temp_file, '--batch-size', '3'],
            obj=mock_context
        )

        assert result.exit_code == 0
        assert mock_context.client.execute.call_count == 3


class TestCreateBulkOutputFormats:
    """Test output formatting"""

    def test_console_output_summary(self, runner, mock_context, temp_json_file):
        """Test console output summary"""
        mock_context.client.execute.return_value = [101, 102, 103]

        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', temp_json_file],
            obj=mock_context
        )

        assert result.exit_code == 0
        assert mock_context.console.print.called

    def test_json_output_structure(self, runner, mock_context, temp_json_file):
        """Test JSON output structure"""
        mock_context.client.execute.return_value = [101, 102, 103]

        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', temp_json_file, '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert 'success' in output
        assert 'created' in output
        assert 'ids' in output
        assert 'model' in output
        assert 'batches' in output
        assert 'batch_size' in output


class TestCreateBulkIntegration:
    """Integration tests"""

    def test_full_workflow(self, runner, mock_context, temp_json_file):
        """Test complete workflow"""
        mock_context.client.execute.return_value = [101, 102, 103]

        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', temp_json_file, '--batch-size', '100'],
            obj=mock_context
        )

        assert result.exit_code == 0
        mock_context.client.execute.assert_called_once()

    def test_large_batch_simulation(self, runner, mock_context):
        """Test simulating large batch"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = [{'name': f'Partner {i}', 'email': f'p{i}@test.com'}
                        for i in range(1, 251)]
            json.dump(test_data, f)
            temp_file = f.name

        # 250 records / 100 batch size = 3 batches
        mock_context.client.execute.side_effect = [
            list(range(101, 201)),   # 100 records
            list(range(201, 301)),   # 100 records
            list(range(301, 351)),   # 50 records
        ]

        result = runner.invoke(
            create_bulk,
            ['res.partner', '--file', temp_file, '--batch-size', '100', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        assert mock_context.client.execute.call_count == 3
        output = json.loads(result.output)
        assert output['created'] == 250
