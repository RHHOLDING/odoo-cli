#!/usr/bin/env python3
"""
Script to add --json option to all commands for LLM-friendly usage.

This makes both patterns work:
- Global: odoo-cli --json search ...
- Command: odoo-cli search ... --json (NEW, LLM-friendly!)

The command-level flag takes precedence if both are specified.
"""

import re
from pathlib import Path


def add_json_option_to_command(file_path: Path) -> bool:
    """Add --json option to a command file."""
    content = file_path.read_text()

    # Skip if already has json_output_option decorator
    if 'json_output_option' in content:
        print(f"✓ {file_path.name} - Already has json_output_option")
        return False

    # Skip shell.py (doesn't need JSON output)
    if file_path.name == 'shell.py':
        print(f"⊘ {file_path.name} - Skipped (shell doesn't need JSON)")
        return False

    # Add import for decorator
    if 'from odoo_cli.decorators import json_output_option' not in content:
        # Find last import line
        import_pattern = r'(from odoo_cli\.[\w.]+ import .+)'
        imports = list(re.finditer(import_pattern, content))

        if imports:
            last_import = imports[-1]
            insert_pos = last_import.end()
            content = (
                content[:insert_pos] +
                '\nfrom odoo_cli.decorators import json_output_option' +
                content[insert_pos:]
            )

    # Add decorator before @click.pass_obj or @click.pass_context
    decorator_pattern = r'(@click\.(?:pass_obj|pass_context))'
    match = re.search(decorator_pattern, content)

    if match:
        insert_pos = match.start()
        content = (
            content[:insert_pos] +
            '@json_output_option\n' +
            content[insert_pos:]
        )

    # Add output_json parameter to function signature
    # Find function definition after the decorator
    func_pattern = r'(def \w+\([^)]+)((?:,\s*)?)\):'

    def add_param(match):
        params = match.group(1)
        trailing = match.group(2)

        # Don't add if already has output_json
        if 'output_json' in params:
            return match.group(0)

        # Add output_json parameter
        if trailing or params.endswith(','):
            return f"{params} output_json: bool):"
        else:
            return f"{params}, output_json: bool):"

    content = re.sub(func_pattern, add_param, content)

    # Add json_mode determination at start of function
    # Find first triple-quoted docstring end
    docstring_pattern = r'(""".*?"""\s+)'
    match = re.search(docstring_pattern, content, re.DOTALL)

    if match:
        insert_pos = match.end()
        json_mode_code = "    # Determine JSON mode (command flag takes precedence over global)\n    json_mode = output_json if output_json is not None else ctx.json_mode\n\n"

        # Only add if not already present
        if 'json_mode = output_json' not in content:
            content = (
                content[:insert_pos] +
                json_mode_code +
                content[insert_pos:]
            )

    # Replace all ctx.json_mode with json_mode
    content = re.sub(r'\bctx\.json_mode\b', 'json_mode', content)

    # Write back
    file_path.write_text(content)
    print(f"✓ {file_path.name} - Updated with json_output_option")
    return True


def main():
    """Update all command files."""
    commands_dir = Path(__file__).parent.parent / 'odoo_cli' / 'commands'

    print("Adding --json option to all commands...\n")

    updated = 0
    skipped = 0

    for file_path in sorted(commands_dir.glob('*.py')):
        if file_path.name == '__init__.py':
            continue

        if add_json_option_to_command(file_path):
            updated += 1
        else:
            skipped += 1

    print(f"\n✓ Done! Updated {updated} commands, skipped {skipped}")
    print("\nBoth patterns now work:")
    print("  odoo-cli --json search res.partner '[]'")
    print("  odoo-cli search res.partner '[]' --json  ← LLM-friendly!")


if __name__ == '__main__':
    main()
