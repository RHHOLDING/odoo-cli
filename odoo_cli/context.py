"""
Context Manager for project-specific business context

Manages loading and accessing .odoo-context.json files with validation.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class ContextManager:
    """Manages loading and accessing .odoo-context.json files"""

    def __init__(self, context_file: Optional[Path] = None) -> None:
        """
        Initialize ContextManager

        Args:
            context_file: Path to context file (defaults to CWD/.odoo-context.json)
        """
        self.context_file = context_file or Path.cwd() / ".odoo-context.json"
        self.context: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        """
        Load context from file

        Returns:
            - Full context dict if file exists and is valid JSON
            - Empty dict {} if file not found (no error)

        Raises:
            json.JSONDecodeError: If file exists but contains invalid JSON
        """
        if not self.context_file.exists():
            self.context = {}
            return self.context

        try:
            with open(self.context_file, 'r', encoding='utf-8') as f:
                self.context = json.load(f)
            return self.context
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in context file: {e.msg}",
                e.doc,
                e.pos
            )

    def get_section(self, section: str) -> Any:
        """
        Get specific section from loaded context

        Args:
            section: Section name (companies, warehouses, workflows, modules, notes)

        Returns:
            - Section data if exists (array or object)
            - Empty list [] if section doesn't exist
        """
        if self.context is None:
            self.load()

        # Return section if it exists, otherwise return empty list/dict
        if section in self.context:
            return self.context[section]
        elif section in ['companies', 'warehouses', 'workflows', 'modules']:
            return []
        elif section == 'notes':
            return {}
        else:
            return []

    def validate(self, strict: bool = False) -> Dict[str, Any]:
        """
        Validate context file

        Args:
            strict: Enforce strict validation (schema + completeness)

        Returns:
            {
                'valid': bool,
                'errors': List[str],    # Empty if valid
                'warnings': List[str]   # Empty if valid or strict mode
            }
        """
        warnings: List[str] = []
        errors: List[str] = []

        # Check if file exists
        if not self.context_file.exists():
            return {
                'valid': False,
                'errors': [f'Context file not found: {self.context_file}'],
                'warnings': []
            }

        # Try to load and parse JSON
        try:
            with open(self.context_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return {
                'valid': False,
                'errors': [f'Invalid JSON: {e.msg} (line {e.lineno}, column {e.colno})'],
                'warnings': []
            }

        # Check for security issues (minimal: literal "password" or "token")
        content_str = json.dumps(data, indent=2).lower()
        if 'password' in content_str:
            warnings.append(
                'Found literal "password" in context file - ensure no credentials are included'
            )
        if 'token' in content_str:
            warnings.append(
                'Found literal "token" in context file - ensure no credentials are included'
            )

        # Check file size (warn if >1MB)
        file_size = self.context_file.stat().st_size
        if file_size > 1_000_000:
            warnings.append(
                f'Context file is {file_size / 1_000_000:.1f}MB - consider simplifying'
            )

        # Strict mode validation
        if strict:
            # Import jsonschema only when needed
            try:
                from jsonschema import validate as schema_validate, ValidationError
            except ImportError:
                errors.append(
                    'jsonschema library required for strict validation. '
                    'Install with: pip install jsonschema'
                )
                return {
                    'valid': False,
                    'errors': errors,
                    'warnings': []
                }

            # Load and apply schema validation
            schema_path = Path(__file__).parent / 'schemas' / 'context_schema.json'
            if not schema_path.exists():
                errors.append(f'Schema file not found: {schema_path}')
                return {
                    'valid': False,
                    'errors': errors,
                    'warnings': []
                }

            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                schema_validate(instance=data, schema=schema)
            except ValidationError as e:
                errors.append(f'Schema validation failed: {e.message}')
            except Exception as e:
                errors.append(f'Error validating schema: {str(e)}')

            # Require all major sections to be present and non-empty
            required_sections = ['companies', 'warehouses', 'workflows', 'modules', 'notes']
            for section in required_sections:
                if section not in data:
                    errors.append(
                        f'Section "{section}" is missing (required in strict mode)'
                    )
                elif not data[section]:
                    errors.append(
                        f'Section "{section}" is empty (required in strict mode)'
                    )

            # Require project metadata
            if 'project' not in data:
                errors.append('Project metadata is missing (required in strict mode)')
            elif not data['project'].get('name'):
                errors.append('Project name is required in strict mode')

            # In strict mode, warnings become errors
            if warnings:
                errors.extend([f'Warning: {w}' for w in warnings])
                warnings = []

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
