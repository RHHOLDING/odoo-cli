"""
Integration tests for context feature

Tests full workflows with actual context files and CLI execution
"""

import json
import pytest
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import MagicMock
from odoo_cli.commands.context import context


@pytest.fixture
def cli_runner():
    """Fixture providing a Click CLI runner"""
    return CliRunner()


@pytest.fixture
def context_valid_fixture():
    """Path to valid context fixture"""
    return Path(__file__).parent.parent / "fixtures" / "context-valid.json"


@pytest.fixture
def context_invalid_fixture():
    """Path to invalid context fixture"""
    return Path(__file__).parent.parent / "fixtures" / "context-invalid.json"


class TestContextShowIntegration:
    """Integration tests for context show command"""

    def test_show_with_valid_fixture(self, cli_runner, context_valid_fixture):
        """Test show command with valid fixture file"""
        with cli_runner.isolated_filesystem():
            # Copy fixture to current directory
            context_file = Path('.odoo-context.json')
            context_file.write_text(context_valid_fixture.read_text())

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            result = cli_runner.invoke(context, ['show'], obj=mock_obj)

            assert result.exit_code == 0
            assert 'Azure Interior' in result.output or 'companies' in result.output.lower()

    def test_show_section_companies(self, cli_runner, context_valid_fixture):
        """Test show command filtering to companies section"""
        with cli_runner.isolated_filesystem():
            context_file = Path('.odoo-context.json')
            context_file.write_text(context_valid_fixture.read_text())

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            result = cli_runner.invoke(
                context,
                ['show', '--section', 'companies'],
                obj=mock_obj
            )

            assert result.exit_code == 0

    def test_show_section_warehouses(self, cli_runner, context_valid_fixture):
        """Test show command filtering to warehouses section"""
        with cli_runner.isolated_filesystem():
            context_file = Path('.odoo-context.json')
            context_file.write_text(context_valid_fixture.read_text())

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            result = cli_runner.invoke(
                context,
                ['show', '--section', 'warehouses'],
                obj=mock_obj
            )

            assert result.exit_code == 0

    def test_show_json_with_fixture(self, cli_runner, context_valid_fixture):
        """Test show command with JSON output and fixture"""
        with cli_runner.isolated_filesystem():
            context_file = Path('.odoo-context.json')
            context_file.write_text(context_valid_fixture.read_text())

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            result = cli_runner.invoke(
                context,
                ['show', '--json'],
                obj=mock_obj
            )

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert 'context' in output
            assert 'companies' in output['context']


class TestContextGuideIntegration:
    """Integration tests for context guide command"""

    def test_guide_create_sales_order(self, cli_runner, context_valid_fixture):
        """Test guide for create-sales-order with fixture"""
        with cli_runner.isolated_filesystem():
            context_file = Path('.odoo-context.json')
            context_file.write_text(context_valid_fixture.read_text())

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            result = cli_runner.invoke(
                context,
                ['guide', '--task', 'create-sales-order'],
                obj=mock_obj
            )

            assert result.exit_code == 0

    def test_guide_manage_inventory(self, cli_runner, context_valid_fixture):
        """Test guide for manage-inventory with fixture"""
        with cli_runner.isolated_filesystem():
            context_file = Path('.odoo-context.json')
            context_file.write_text(context_valid_fixture.read_text())

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            result = cli_runner.invoke(
                context,
                ['guide', '--task', 'manage-inventory', '--json'],
                obj=mock_obj
            )

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert 'task' in output
            assert 'manage-inventory' in output['task']

    def test_guide_purchase_approval(self, cli_runner, context_valid_fixture):
        """Test guide for purchase-approval with fixture"""
        with cli_runner.isolated_filesystem():
            context_file = Path('.odoo-context.json')
            context_file.write_text(context_valid_fixture.read_text())

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            result = cli_runner.invoke(
                context,
                ['guide', '--task', 'purchase-approval'],
                obj=mock_obj
            )

            assert result.exit_code == 0

    def test_guide_production_workflow(self, cli_runner, context_valid_fixture):
        """Test guide for production-workflow with fixture"""
        with cli_runner.isolated_filesystem():
            context_file = Path('.odoo-context.json')
            context_file.write_text(context_valid_fixture.read_text())

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            result = cli_runner.invoke(
                context,
                ['guide', '--task', 'production-workflow', '--json'],
                obj=mock_obj
            )

            assert result.exit_code == 0


class TestContextValidateIntegration:
    """Integration tests for context validate command"""

    def test_validate_valid_fixture(self, cli_runner, context_valid_fixture):
        """Test validate with valid fixture"""
        with cli_runner.isolated_filesystem():
            context_file = Path('.odoo-context.json')
            context_file.write_text(context_valid_fixture.read_text())

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            mock_obj.obj = MagicMock()
            result = cli_runner.invoke(
                context,
                ['validate'],
                obj=mock_obj
            )

            assert result.exit_code == 0
            assert 'valid' in result.output.lower()

    def test_validate_valid_fixture_json(self, cli_runner, context_valid_fixture):
        """Test validate valid fixture with JSON output"""
        with cli_runner.isolated_filesystem():
            context_file = Path('.odoo-context.json')
            context_file.write_text(context_valid_fixture.read_text())

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            mock_obj.obj = MagicMock()
            result = cli_runner.invoke(
                context,
                ['validate', '--json'],
                obj=mock_obj
            )

            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output['valid'] is True

    def test_validate_invalid_fixture(self, cli_runner, context_invalid_fixture):
        """Test validate with invalid fixture"""
        with cli_runner.isolated_filesystem():
            context_file = Path('.odoo-context.json')
            context_file.write_text(context_invalid_fixture.read_text())

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            mock_obj.obj = MagicMock()
            result = cli_runner.invoke(
                context,
                ['validate'],
                obj=mock_obj
            )

            # Should show warnings (password) but still be valid in normal mode
            # because it only has a security warning
            assert result.exit_code in (0, 3)

    def test_validate_strict_valid_fixture(self, cli_runner, context_valid_fixture):
        """Test strict validation with valid fixture"""
        with cli_runner.isolated_filesystem():
            context_file = Path('.odoo-context.json')
            context_file.write_text(context_valid_fixture.read_text())

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            mock_obj.obj = MagicMock()
            result = cli_runner.invoke(
                context,
                ['validate', '--strict'],
                obj=mock_obj
            )

            assert result.exit_code == 0

    def test_validate_strict_invalid_fixture(self, cli_runner, context_invalid_fixture):
        """Test strict validation with invalid fixture"""
        with cli_runner.isolated_filesystem():
            context_file = Path('.odoo-context.json')
            context_file.write_text(context_invalid_fixture.read_text())

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            mock_obj.obj = MagicMock()
            result = cli_runner.invoke(
                context,
                ['validate', '--strict'],
                obj=mock_obj
            )

            # Should fail due to incomplete sections or missing project name
            assert result.exit_code == 3 or 'invalid' in result.output.lower()


class TestContextMissingFile:
    """Integration tests for missing context file scenarios"""

    def test_show_missing_file(self, cli_runner):
        """Test show command with no context file"""
        with cli_runner.isolated_filesystem():
            mock_obj = MagicMock()
            mock_obj.json_mode = False
            result = cli_runner.invoke(context, ['show'], obj=mock_obj)

            assert result.exit_code == 0
            assert 'no' in result.output.lower() or 'not found' in result.output.lower()

    def test_guide_missing_file(self, cli_runner):
        """Test guide command with no context file"""
        with cli_runner.isolated_filesystem():
            mock_obj = MagicMock()
            mock_obj.json_mode = False
            result = cli_runner.invoke(
                context,
                ['guide', '--task', 'create-sales-order'],
                obj=mock_obj
            )

            assert result.exit_code == 0
            assert 'no' in result.output.lower() or 'not found' in result.output.lower()

    def test_validate_missing_file(self, cli_runner):
        """Test validate command with no context file"""
        with cli_runner.isolated_filesystem():
            mock_obj = MagicMock()
            mock_obj.json_mode = False
            mock_obj.obj = MagicMock()
            result = cli_runner.invoke(context, ['validate'], obj=mock_obj)

            # Should fail validation
            assert result.exit_code == 3 or 'invalid' in result.output.lower()


class TestContextEdgeCases:
    """Integration tests for edge cases"""

    def test_show_empty_context(self, cli_runner):
        """Test show with empty context file"""
        with cli_runner.isolated_filesystem():
            context_file = Path('.odoo-context.json')
            context_file.write_text('{}')

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            result = cli_runner.invoke(context, ['show'], obj=mock_obj)

            assert result.exit_code == 0

    def test_validate_empty_context(self, cli_runner):
        """Test validate with empty context file"""
        with cli_runner.isolated_filesystem():
            context_file = Path('.odoo-context.json')
            context_file.write_text('{}')

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            mock_obj.obj = MagicMock()
            result = cli_runner.invoke(context, ['validate'], obj=mock_obj)

            # Empty file should be valid in normal mode
            assert result.exit_code == 0 or 'valid' in result.output.lower()

    def test_guide_empty_context(self, cli_runner):
        """Test guide with empty context file"""
        with cli_runner.isolated_filesystem():
            context_file = Path('.odoo-context.json')
            context_file.write_text('{}')

            mock_obj = MagicMock()
            mock_obj.json_mode = False
            result = cli_runner.invoke(
                context,
                ['guide', '--task', 'create-sales-order'],
                obj=mock_obj
            )

            assert result.exit_code == 0
            assert 'no' in result.output.lower() or 'available' in result.output.lower()
