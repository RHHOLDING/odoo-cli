"""
Unit tests for context CLI commands
"""

import json
import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch, MagicMock
from odoo_cli.commands.context import context, show, guide, validate


@pytest.fixture
def cli_runner():
    """Fixture providing a Click CLI runner"""
    return CliRunner()


@pytest.fixture
def mock_context(tmp_path):
    """Fixture providing a mock CliContext"""
    mock_ctx = MagicMock()
    mock_ctx.json_mode = False
    mock_ctx.console = MagicMock()
    mock_ctx.obj = MagicMock()
    mock_ctx.obj.exit_code = 0
    return mock_ctx


@pytest.fixture
def valid_context_data():
    """Fixture with valid context data"""
    return {
        "schema_version": "1.0.0",
        "project": {
            "name": "Test Project",
            "description": "Test project description",
            "odoo_version": "17.0"
        },
        "companies": [
            {"id": 1, "name": "Company A", "role": "Main", "context": "Test"}
        ],
        "warehouses": [
            {"id": 1, "name": "Warehouse A", "company_id": 1, "role": "Main", "context": "Test"}
        ],
        "workflows": [
            {"name": "Workflow A", "critical": True, "context": "Test"}
        ],
        "modules": [
            {"name": "custom_test", "purpose": "Test", "context": "Test"}
        ],
        "notes": {
            "common_tasks": ["Task 1"],
            "pitfalls": ["Pitfall 1"]
        }
    }


class TestContextShowCommand:
    """Tests for context show command"""

    def test_show_no_context_file(self, cli_runner, tmp_path):
        """Test show command when no context file exists"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(show)
            assert result.exit_code == 0
            assert 'No .odoo-context.json' in result.output or 'No context' in result.output

    def test_show_with_valid_context_file(self, cli_runner, tmp_path, valid_context_data):
        """Test show command with valid context file"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            # Create context file
            context_file = Path('.odoo-context.json')
            context_file.write_text(json.dumps(valid_context_data))

            result = cli_runner.invoke(show, obj=MagicMock(json_mode=False))
            assert result.exit_code == 0
            assert 'companies' in result.output.lower() or 'Company A' in result.output

    def test_show_json_output(self, cli_runner, tmp_path, valid_context_data):
        """Test show command with JSON output"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            context_file = Path('.odoo-context.json')
            context_file.write_text(json.dumps(valid_context_data))

            result = cli_runner.invoke(show, ['--json'], obj=MagicMock(json_mode=False))
            assert result.exit_code == 0
            # Should be valid JSON
            output = json.loads(result.output)
            assert 'context' in output

    def test_show_section_filter(self, cli_runner, tmp_path, valid_context_data):
        """Test show command with section filter"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            context_file = Path('.odoo-context.json')
            context_file.write_text(json.dumps(valid_context_data))

            result = cli_runner.invoke(
                show,
                ['--section', 'companies'],
                obj=MagicMock(json_mode=False)
            )
            assert result.exit_code == 0
            output = json.loads(result.output) if '--json' not in result.output else None
            if output:
                assert 'companies' in output['context']

    def test_show_missing_section(self, cli_runner, tmp_path, valid_context_data):
        """Test show command with non-existent section"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            context_file = Path('.odoo-context.json')
            context_file.write_text(json.dumps(valid_context_data))

            result = cli_runner.invoke(
                show,
                ['--section', 'nonexistent'],
                obj=MagicMock(json_mode=False)
            )
            assert result.exit_code == 0


class TestContextGuideCommand:
    """Tests for context guide command"""

    def test_guide_no_context_file(self, cli_runner, tmp_path):
        """Test guide command when no context file exists"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(
                guide,
                ['--task', 'create-sales-order'],
                obj=MagicMock(json_mode=False)
            )
            assert result.exit_code == 0
            assert 'No context' in result.output or 'not found' in result.output.lower()

    def test_guide_with_valid_context(self, cli_runner, tmp_path, valid_context_data):
        """Test guide command with valid context"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            context_file = Path('.odoo-context.json')
            context_file.write_text(json.dumps(valid_context_data))

            result = cli_runner.invoke(
                guide,
                ['--task', 'create-sales-order'],
                obj=MagicMock(json_mode=False)
            )
            assert result.exit_code == 0

    def test_guide_create_sales_order_task(self, cli_runner, tmp_path, valid_context_data):
        """Test guide for create-sales-order task"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            context_file = Path('.odoo-context.json')
            context_file.write_text(json.dumps(valid_context_data))

            result = cli_runner.invoke(
                guide,
                ['--task', 'create-sales-order', '--json'],
                obj=MagicMock(json_mode=False)
            )
            assert result.exit_code == 0
            # Should return companies and warehouses for this task
            output = json.loads(result.output)
            assert 'guide' in output
            assert 'create-sales-order' in output['task']

    def test_guide_manage_inventory_task(self, cli_runner, tmp_path, valid_context_data):
        """Test guide for manage-inventory task"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            context_file = Path('.odoo-context.json')
            context_file.write_text(json.dumps(valid_context_data))

            result = cli_runner.invoke(
                guide,
                ['--task', 'manage-inventory', '--json'],
                obj=MagicMock(json_mode=False)
            )
            assert result.exit_code == 0

    def test_guide_purchase_approval_task(self, cli_runner, tmp_path, valid_context_data):
        """Test guide for purchase-approval task"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            context_file = Path('.odoo-context.json')
            context_file.write_text(json.dumps(valid_context_data))

            result = cli_runner.invoke(
                guide,
                ['--task', 'purchase-approval', '--json'],
                obj=MagicMock(json_mode=False)
            )
            assert result.exit_code == 0

    def test_guide_production_workflow_task(self, cli_runner, tmp_path, valid_context_data):
        """Test guide for production-workflow task"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            context_file = Path('.odoo-context.json')
            context_file.write_text(json.dumps(valid_context_data))

            result = cli_runner.invoke(
                guide,
                ['--task', 'production-workflow', '--json'],
                obj=MagicMock(json_mode=False)
            )
            assert result.exit_code == 0

    def test_guide_json_output(self, cli_runner, tmp_path, valid_context_data):
        """Test guide command with JSON output"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            context_file = Path('.odoo-context.json')
            context_file.write_text(json.dumps(valid_context_data))

            result = cli_runner.invoke(
                guide,
                ['--task', 'create-sales-order', '--json'],
                obj=MagicMock(json_mode=False)
            )
            assert result.exit_code == 0
            # Should return valid JSON
            try:
                output = json.loads(result.output)
                assert 'task' in output
                assert 'guide' in output
            except json.JSONDecodeError:
                pytest.fail("Output is not valid JSON")


class TestContextValidateCommand:
    """Tests for context validate command"""

    def test_validate_no_context_file(self, cli_runner, tmp_path):
        """Test validate command when no context file exists"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            result = cli_runner.invoke(validate, obj=MagicMock(json_mode=False, obj=MagicMock()))
            # Should fail validation
            assert 'invalid' in result.output.lower() or result.exit_code == 3

    def test_validate_valid_context_file(self, cli_runner, tmp_path, valid_context_data):
        """Test validate command with valid context file"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            context_file = Path('.odoo-context.json')
            context_file.write_text(json.dumps(valid_context_data))

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            mock_obj.obj = MagicMock()
            result = cli_runner.invoke(validate, obj=mock_obj)
            assert result.exit_code == 0
            assert 'valid' in result.output.lower()

    def test_validate_invalid_json(self, cli_runner, tmp_path):
        """Test validate command with invalid JSON"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            context_file = Path('.odoo-context.json')
            context_file.write_text('{ invalid }')

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            mock_obj.obj = MagicMock()
            result = cli_runner.invoke(validate, obj=mock_obj)
            # Should fail validation
            assert 'invalid' in result.output.lower() or result.exit_code == 3

    def test_validate_json_output(self, cli_runner, tmp_path, valid_context_data):
        """Test validate command with JSON output"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            context_file = Path('.odoo-context.json')
            context_file.write_text(json.dumps(valid_context_data))

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            mock_obj.obj = MagicMock()
            result = cli_runner.invoke(validate, ['--json'], obj=mock_obj)
            assert result.exit_code == 0
            # Should be valid JSON with validation result
            try:
                output = json.loads(result.output)
                assert 'valid' in output
                assert 'errors' in output
                assert 'warnings' in output
            except json.JSONDecodeError:
                pytest.fail("Output is not valid JSON")

    def test_validate_normal_mode(self, cli_runner, tmp_path, valid_context_data):
        """Test validate in normal mode"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            context_file = Path('.odoo-context.json')
            context_file.write_text(json.dumps(valid_context_data))

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            mock_obj.obj = MagicMock()
            result = cli_runner.invoke(validate, obj=mock_obj)
            assert result.exit_code == 0

    def test_validate_strict_mode(self, cli_runner, tmp_path, valid_context_data):
        """Test validate in strict mode"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            context_file = Path('.odoo-context.json')
            context_file.write_text(json.dumps(valid_context_data))

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            mock_obj.obj = MagicMock()
            result = cli_runner.invoke(validate, ['--strict'], obj=mock_obj)
            assert result.exit_code == 0

    def test_validate_strict_missing_sections(self, cli_runner, tmp_path):
        """Test strict mode fails with missing sections"""
        with cli_runner.isolated_filesystem(temp_dir=tmp_path):
            incomplete_data = {"schema_version": "1.0.0"}
            context_file = Path('.odoo-context.json')
            context_file.write_text(json.dumps(incomplete_data))

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            mock_obj.obj = MagicMock()
            result = cli_runner.invoke(validate, ['--strict'], obj=mock_obj)
            # Should fail validation
            assert 'invalid' in result.output.lower() or result.exit_code == 3


class TestContextCommandGroup:
    """Tests for context command group"""

    def test_context_command_help(self, cli_runner):
        """Test context command help"""
        result = cli_runner.invoke(context, ['--help'])
        assert result.exit_code == 0
        assert 'show' in result.output
        assert 'guide' in result.output
        assert 'validate' in result.output

    def test_context_show_help(self, cli_runner):
        """Test context show help"""
        result = cli_runner.invoke(context, ['show', '--help'])
        assert result.exit_code == 0
        assert '--section' in result.output

    def test_context_guide_help(self, cli_runner):
        """Test context guide help"""
        result = cli_runner.invoke(context, ['guide', '--help'])
        assert result.exit_code == 0
        assert '--task' in result.output

    def test_context_validate_help(self, cli_runner):
        """Test context validate help"""
        result = cli_runner.invoke(context, ['validate', '--help'])
        assert result.exit_code == 0
        assert '--strict' in result.output
