#!/usr/bin/env python3
"""
Script to add --json option to all commands for LLM-friendly usage.

Improved version with proper code injection placement.
"""

import re
from pathlib import Path


def add_json_option_to_command(file_path: Path) -> bool:
    """Add --json option to a command file."""
    content = file_path.read_text()

    # Skip if already has output_json parameter
    if 'output_json: bool' in content or 'output_json,' in content:
        print(f"✓ {file_path.name} - Already has output_json parameter")
        return False

    # Skip shell.py (doesn't need JSON output)
    if file_path.name == 'shell.py':
        print(f"⊘ {file_path.name} - Skipped (shell doesn't need JSON)")
        return False

    lines = content.split('\n')
    new_lines = []
    decorator_added = False
    import_added = False
    json_mode_added = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Add import after other imports
        if not import_added and line.startswith('from odoo_cli.utils') and 'import' in line:
            new_lines.append(line)
            new_lines.append('from odoo_cli.decorators import json_output_option')
            import_added = True
            i += 1
            continue

        # Add decorator before @click.pass_obj or @click.pass_context
        if not decorator_added and line.strip() in ['@click.pass_obj', '@click.pass_context']:
            new_lines.append('@json_output_option')
            decorator_added = True

        # Add parameter to function signature
        if 'def ' in line and '(ctx: CliContext' in line:
            # Find closing parenthesis
            func_line = line
            if '):'  in line:
                # Single line function signature
                func_line = line.replace('):', ', output_json: bool):')
            else:
                # Multi-line signature - just add before last param
                func_line = line.replace(', context: tuple', ', context: tuple, output_json: bool')

            new_lines.append(func_line)
            i += 1
            continue

        # Add json_mode logic after docstring
        if not json_mode_added and line.strip() == '"""':
            # This is end of docstring
            new_lines.append(line)
            # Add json_mode logic
            new_lines.append('    # Determine JSON mode (command flag takes precedence over global)')
            new_lines.append('    json_mode = output_json if output_json is not None else ctx.json_mode')
            new_lines.append('')
            json_mode_added = True
            i += 1

            # Now replace all ctx.json_mode with json_mode in remaining code
            while i < len(lines):
                remaining_line = lines[i]
                remaining_line = remaining_line.replace('ctx.json_mode', 'json_mode')
                new_lines.append(remaining_line)
                i += 1
            break

        new_lines.append(line)
        i += 1

    # Write back
    new_content = '\n'.join(new_lines)
    file_path.write_text(new_content)
    print(f"✓ {file_path.name} - Updated with json_output_option")
    return True


def main():
    """Update all command files."""
    commands_dir = Path(__file__).parent.parent / 'odoo_cli' / 'commands'

    print("Adding --json option to all commands (v2 - improved)...\n")

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
