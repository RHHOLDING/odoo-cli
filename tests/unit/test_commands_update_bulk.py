"""
Unit tests for UPDATE-BULK command.
"""

import pytest
import json
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import Mock, patch
import tempfile

from odoo_cli.commands.update_bulk import update_bulk, group_by_fields
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


class TestGroupByFields:
    """Test field grouping utility"""

    def test_group_identical_updates(self):
        """Test grouping records with identical field updates"""
        updates = {
            '1': {'name': 'Test', 'active': True},
            '2': {'name': 'Test', 'active': True},
            '3': {'name': 'Other', 'active': False},
        }

        groups = group_by_fields(updates)
        assert len(groups) == 2

    def test_group_single_record(self):
        """Test single record"""
        updates = {'1': {'name': 'Test'}}
        groups = group_by_fields(updates)
        assert len(groups) == 1

    def test_group_all_identical(self):
        """Test all records have identical updates"""
        updates = {
            '1': {'name': 'Same'},
            '2': {'name': 'Same'},
            '3': {'name': 'Same'},
        }

        groups = group_by_fields(updates)
        assert len(groups) == 1


class TestUpdateBulkSuccess:
    """Test successful UPDATE-BULK scenarios"""

    def test_update_bulk_simple(self, runner, mock_context):
        """Test updating records with simple updates"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            updates = {
                '123': {'name': 'Updated 1'},
                '124': {'name': 'Updated 2'},
            }
            json.dump(updates, f)
            temp_file = f.name

        result = runner.invoke(
            update_bulk,
            ['res.partner', '--file', temp_file],
            obj=mock_context
        )

        assert result.exit_code == 0
        assert mock_context.client.execute.called

    def test_update_bulk_with_grouping(self, runner, mock_context):
        """Test field grouping optimization"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            updates = {
                '1': {'name': 'Test', 'active': True},
                '2': {'name': 'Test', 'active': True},
                '3': {'name': 'Other', 'active': False},
            }
            json.dump(updates, f)
            temp_file = f.name

        result = runner.invoke(
            update_bulk,
            ['res.partner', '--file', temp_file],
            obj=mock_context
        )

        assert result.exit_code == 0
        # Should have 2 execute calls (2 groups)
        assert mock_context.client.execute.call_count == 2

    def test_update_bulk_json_output(self, runner, mock_context):
        """Test JSON output format"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            updates = {
                '123': {'name': 'Test'},
                '124': {'email': 'test@test.com'},
            }
            json.dump(updates, f)
            temp_file = f.name

        result = runner.invoke(
            update_bulk,
            ['res.partner', '--file', temp_file, '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['success'] is True
        assert output['updated'] == 2
        assert output['model'] == 'res.partner'

    def test_update_bulk_custom_batch_size(self, runner, mock_context):
        """Test custom batch size"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            updates = {
                '1': {'name': 'Test'},
                '2': {'name': 'Test'},
                '3': {'name': 'Test'},
                '4': {'name': 'Test'},
                '5': {'name': 'Test'},
            }
            json.dump(updates, f)
            temp_file = f.name

        result = runner.invoke(
            update_bulk,
            ['res.partner', '--file', temp_file, '--batch-size', '2'],
            obj=mock_context
        )

        assert result.exit_code == 0


class TestUpdateBulkErrors:
    """Test error handling"""

    def test_file_not_found(self, runner, mock_context):
        """Test error when file doesn't exist"""
        result = runner.invoke(
            update_bulk,
            ['res.partner', '--file', '/nonexistent/file.json'],
            obj=mock_context
        )

        assert result.exit_code == 2

    def test_invalid_json(self, runner, mock_context):
        """Test error with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            temp_file = f.name

        result = runner.invoke(
            update_bulk,
            ['res.partner', '--file', temp_file],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_json_not_object(self, runner, mock_context):
        """Test error when JSON is not an object"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{'id': 1, 'name': 'Test'}], f)
            temp_file = f.name

        result = runner.invoke(
            update_bulk,
            ['res.partner', '--file', temp_file],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_empty_object(self, runner, mock_context):
        """Test error with empty JSON object"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            temp_file = f.name

        result = runner.invoke(
            update_bulk,
            ['res.partner', '--file', temp_file],
            obj=mock_context
        )

        assert result.exit_code == 3

    def test_odoo_error_during_update(self, runner, mock_context):
        """Test error during Odoo execution"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            updates = {'123': {'name': 'Test'}}
            json.dump(updates, f)
            temp_file = f.name

        mock_context.client.execute.side_effect = Exception("Odoo error")

        result = runner.invoke(
            update_bulk,
            ['res.partner', '--file', temp_file],
            obj=mock_context
        )

        assert result.exit_code == 3


class TestUpdateBulkGrouping:
    """Test field grouping logic"""

    def test_single_group(self, runner, mock_context):
        """Test all records in single group"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            updates = {
                '1': {'name': 'Test'},
                '2': {'name': 'Test'},
                '3': {'name': 'Test'},
            }
            json.dump(updates, f)
            temp_file = f.name

        result = runner.invoke(
            update_bulk,
            ['res.partner', '--file', temp_file, '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['groups'] == 1

    def test_multiple_groups(self, runner, mock_context):
        """Test records split into multiple groups"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            updates = {
                '1': {'name': 'A'},
                '2': {'name': 'A'},
                '3': {'name': 'B'},
                '4': {'name': 'B'},
                '5': {'email': 'test@test.com'},
            }
            json.dump(updates, f)
            temp_file = f.name

        result = runner.invoke(
            update_bulk,
            ['res.partner', '--file', temp_file, '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['groups'] >= 2


class TestUpdateBulkOutputFormats:
    """Test output formatting"""

    def test_json_output_structure(self, runner, mock_context):
        """Test JSON output structure"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            updates = {
                '123': {'name': 'Test'},
                '124': {'active': False},
            }
            json.dump(updates, f)
            temp_file = f.name

        result = runner.invoke(
            update_bulk,
            ['res.partner', '--file', temp_file, '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert 'success' in output
        assert 'updated' in output
        assert 'ids' in output
        assert 'model' in output
        assert 'groups' in output


class TestUpdateBulkIntegration:
    """Integration tests"""

    def test_full_workflow(self, runner, mock_context):
        """Test complete workflow"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            updates = {
                '1': {'name': 'Updated 1'},
                '2': {'name': 'Updated 2'},
                '3': {'name': 'Updated 3'},
            }
            json.dump(updates, f)
            temp_file = f.name

        result = runner.invoke(
            update_bulk,
            ['res.partner', '--file', temp_file],
            obj=mock_context
        )

        assert result.exit_code == 0
        assert mock_context.client.execute.called

    def test_large_update_simulation(self, runner, mock_context):
        """Test simulating large bulk update"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            updates = {}
            for i in range(1, 51):
                if i % 2 == 0:
                    updates[str(i)] = {'name': 'Even', 'active': True}
                else:
                    updates[str(i)] = {'name': 'Odd', 'active': False}
            json.dump(updates, f)
            temp_file = f.name

        result = runner.invoke(
            update_bulk,
            ['res.partner', '--file', temp_file, '--batch-size', '10', '--json'],
            obj=mock_context
        )

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output['updated'] == 50
