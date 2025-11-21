"""
Unit tests for ContextManager class
"""

import json
import pytest
from pathlib import Path
from odoo_cli.context import ContextManager


@pytest.fixture
def temp_context_file(tmp_path):
    """Fixture providing a temporary context file path"""
    return tmp_path / ".odoo-context.json"


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
            {
                "id": 1,
                "name": "Company A",
                "role": "Main company",
                "context": "Test company"
            }
        ],
        "warehouses": [
            {
                "id": 1,
                "name": "Warehouse A",
                "company_id": 1,
                "role": "Main warehouse",
                "context": "Test warehouse"
            }
        ],
        "workflows": [
            {
                "name": "Test Workflow",
                "critical": True,
                "context": "Test workflow context"
            }
        ],
        "modules": [
            {
                "name": "custom_test",
                "purpose": "Test module",
                "context": "Test module context"
            }
        ],
        "notes": {
            "common_tasks": ["Task 1", "Task 2"],
            "pitfalls": ["Pitfall 1"]
        }
    }


class TestContextManagerLoad:
    """Tests for ContextManager.load()"""

    def test_load_missing_file_returns_empty_dict(self, temp_context_file):
        """Test that missing context file returns empty dict"""
        manager = ContextManager(temp_context_file)
        result = manager.load()
        assert result == {}
        assert manager.context == {}

    def test_load_valid_file(self, temp_context_file, valid_context_data):
        """Test loading valid context file"""
        # Write valid JSON
        with open(temp_context_file, 'w') as f:
            json.dump(valid_context_data, f)

        manager = ContextManager(temp_context_file)
        result = manager.load()

        assert result == valid_context_data
        assert manager.context == valid_context_data

    def test_load_invalid_json_raises_error(self, temp_context_file):
        """Test that invalid JSON raises JSONDecodeError"""
        # Write invalid JSON
        temp_context_file.write_text("{ invalid json }")

        manager = ContextManager(temp_context_file)
        with pytest.raises(json.JSONDecodeError):
            manager.load()

    def test_load_caches_context(self, temp_context_file, valid_context_data):
        """Test that load caches context"""
        with open(temp_context_file, 'w') as f:
            json.dump(valid_context_data, f)

        manager = ContextManager(temp_context_file)
        result1 = manager.load()
        result2 = manager.load()

        assert result1 is result2  # Same object reference

    def test_load_empty_json_object(self, temp_context_file):
        """Test loading empty JSON object"""
        temp_context_file.write_text("{}")

        manager = ContextManager(temp_context_file)
        result = manager.load()

        assert result == {}


class TestContextManagerGetSection:
    """Tests for ContextManager.get_section()"""

    def test_get_section_existing_array(self, temp_context_file, valid_context_data):
        """Test getting existing section with array"""
        with open(temp_context_file, 'w') as f:
            json.dump(valid_context_data, f)

        manager = ContextManager(temp_context_file)
        manager.load()

        companies = manager.get_section('companies')
        assert len(companies) == 1
        assert companies[0]['name'] == 'Company A'

    def test_get_section_existing_object(self, temp_context_file, valid_context_data):
        """Test getting existing section with object"""
        with open(temp_context_file, 'w') as f:
            json.dump(valid_context_data, f)

        manager = ContextManager(temp_context_file)
        manager.load()

        notes = manager.get_section('notes')
        assert notes['common_tasks'] == ["Task 1", "Task 2"]

    def test_get_section_missing_array_section(self, temp_context_file):
        """Test getting missing array section returns empty list"""
        temp_context_file.write_text("{}")

        manager = ContextManager(temp_context_file)
        manager.load()

        companies = manager.get_section('companies')
        assert companies == []

    def test_get_section_missing_notes_section(self, temp_context_file):
        """Test getting missing notes section returns empty dict"""
        temp_context_file.write_text("{}")

        manager = ContextManager(temp_context_file)
        manager.load()

        notes = manager.get_section('notes')
        assert notes == {}

    def test_get_section_loads_context_if_needed(self, temp_context_file, valid_context_data):
        """Test that get_section loads context if not already loaded"""
        with open(temp_context_file, 'w') as f:
            json.dump(valid_context_data, f)

        manager = ContextManager(temp_context_file)
        # Don't call load() - let get_section do it
        companies = manager.get_section('companies')

        assert len(companies) == 1


class TestContextManagerValidate:
    """Tests for ContextManager.validate()"""

    def test_validate_missing_file(self, temp_context_file):
        """Test validation of missing file"""
        manager = ContextManager(temp_context_file)
        result = manager.validate()

        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert 'not found' in result['errors'][0].lower()

    def test_validate_valid_file(self, temp_context_file, valid_context_data):
        """Test validation of valid file (normal mode)"""
        with open(temp_context_file, 'w') as f:
            json.dump(valid_context_data, f)

        manager = ContextManager(temp_context_file)
        result = manager.validate(strict=False)

        assert result['valid'] is True
        assert result['errors'] == []

    def test_validate_invalid_json(self, temp_context_file):
        """Test validation of invalid JSON"""
        temp_context_file.write_text("{ invalid }")

        manager = ContextManager(temp_context_file)
        result = manager.validate()

        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert 'Invalid JSON' in result['errors'][0]

    def test_validate_detects_password(self, temp_context_file):
        """Test that validation detects literal 'password'"""
        data = {
            "schema_version": "1.0.0",
            "notes": {
                "password": "secret"
            }
        }
        with open(temp_context_file, 'w') as f:
            json.dump(data, f)

        manager = ContextManager(temp_context_file)
        result = manager.validate(strict=False)

        assert result['valid'] is True
        assert len(result['warnings']) > 0
        assert any('password' in w.lower() for w in result['warnings'])

    def test_validate_detects_token(self, temp_context_file):
        """Test that validation detects literal 'token'"""
        data = {
            "schema_version": "1.0.0",
            "notes": {
                "api_token": "secret"
            }
        }
        with open(temp_context_file, 'w') as f:
            json.dump(data, f)

        manager = ContextManager(temp_context_file)
        result = manager.validate(strict=False)

        assert result['valid'] is True
        assert len(result['warnings']) > 0
        assert any('token' in w.lower() for w in result['warnings'])

    def test_validate_strict_requires_all_sections(self, temp_context_file):
        """Test that strict mode requires all sections"""
        data = {
            "schema_version": "1.0.0",
            "project": {"name": "Test"}
        }
        with open(temp_context_file, 'w') as f:
            json.dump(data, f)

        manager = ContextManager(temp_context_file)
        result = manager.validate(strict=True)

        assert result['valid'] is False
        # Should have errors about missing sections
        assert any('companies' in e for e in result['errors'])

    def test_validate_strict_requires_project_name(self, temp_context_file, valid_context_data):
        """Test that strict mode requires project name"""
        valid_context_data['project'] = {}
        with open(temp_context_file, 'w') as f:
            json.dump(valid_context_data, f)

        manager = ContextManager(temp_context_file)
        result = manager.validate(strict=True)

        assert result['valid'] is False
        assert any('name' in e.lower() for e in result['errors'])

    def test_validate_strict_mode_warnings_become_errors(self, temp_context_file, valid_context_data):
        """Test that in strict mode, warnings become errors"""
        valid_context_data['notes']['secret_password'] = 'exposed'
        with open(temp_context_file, 'w') as f:
            json.dump(valid_context_data, f)

        # Normal mode should have warnings
        manager = ContextManager(temp_context_file)
        normal_result = manager.validate(strict=False)
        assert len(normal_result['warnings']) > 0

        # Strict mode should have errors
        strict_result = manager.validate(strict=True)
        assert strict_result['valid'] is False

    def test_validate_empty_context(self, temp_context_file):
        """Test validation of empty context"""
        temp_context_file.write_text('{}')

        manager = ContextManager(temp_context_file)
        result = manager.validate(strict=False)

        # Empty file is valid in normal mode
        assert result['valid'] is True

    def test_validate_large_file_warning(self, temp_context_file, valid_context_data):
        """Test that validation warns about large files"""
        # Create a large file (>1MB)
        large_data = valid_context_data.copy()
        large_data['notes']['large_text'] = 'x' * (2 * 1_000_000)  # 2MB of text

        with open(temp_context_file, 'w') as f:
            json.dump(large_data, f)

        manager = ContextManager(temp_context_file)
        result = manager.validate(strict=False)

        # Should have warning about file size
        assert any('MB' in w or 'size' in w.lower() for w in result['warnings'])


class TestContextManagerDefaults:
    """Tests for ContextManager default behavior"""

    def test_default_context_file_path(self, tmp_path, monkeypatch):
        """Test that default context file is .odoo-context.json in CWD"""
        monkeypatch.chdir(tmp_path)

        manager = ContextManager()
        # Create the default file
        (tmp_path / ".odoo-context.json").write_text("{}")

        result = manager.load()
        assert result == {}

    def test_context_file_only_in_current_dir(self, tmp_path, monkeypatch):
        """Test that context file is only searched in current directory"""
        # Create parent and child directories
        parent = tmp_path
        child = tmp_path / "subdir"
        child.mkdir()

        # Create context file in parent only
        (parent / ".odoo-context.json").write_text(json.dumps({"schema_version": "1.0.0"}))

        # Change to child directory
        monkeypatch.chdir(child)

        manager = ContextManager()
        result = manager.load()

        # Should not find the parent's file
        assert result == {}
