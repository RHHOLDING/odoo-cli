#!/bin/bash
# Apply --json option to all commands for maximum LLM-friendliness

cd /Users/andre/Documents/dev/ODOO-CLI

echo "Applying --json option to all commands..."
echo

# List of commands to update (all except shell.py and search.py which is done)
commands=(
    "read" "create" "update" "delete"
    "create_bulk" "update_bulk" "aggregate"
    "execute" "get_models" "get_fields"
    "search_count" "name_get" "name_search"
    "search_employee" "search_holidays"
)

for cmd in "${commands[@]}"; do
    file="odoo_cli/commands/${cmd}.py"

    if [ ! -f "$file" ]; then
        echo "⊘ $cmd.py - File not found"
        continue
    fi

    # Check if already has output_json parameter
    if grep -q "output_json: bool" "$file"; then
        echo "✓ $cmd.py - Already has output_json"
        continue
    fi

    echo "→ Processing $cmd.py..."

    # 1. Add import if not present
    if ! grep -q "from odoo_cli.decorators import json_output_option" "$file"; then
        # Add after last import from odoo_cli
        sed -i '' '/from odoo_cli\.utils/a\
from odoo_cli.decorators import json_output_option
' "$file"
    fi

    # 2. Add decorator before @click.pass_obj
    sed -i '' '/@click\.pass_obj/i\
@json_output_option
' "$file"

    # 3. Add output_json parameter to function signature
    # This is tricky - we need to handle different parameter patterns
    sed -i '' 's/\(def [a-z_]*([^)]*\), context: tuple)/\1, context: tuple, output_json: bool)/g' "$file"
    sed -i '' 's/\(def [a-z_]*([^)]*\)): /\1, output_json: bool): /g' "$file"

    # 4. Add json_mode logic after first docstring
    # Find line number of first """ after def
    line=$(grep -n '"""' "$file" | head -2 | tail -1 | cut -d: -f1)

    if [ -n "$line" ]; then
        # Insert after docstring
        sed -i '' "${line}a\\
    # Determine JSON mode (command flag takes precedence over global)\\
    json_mode = output_json if output_json is not None else ctx.json_mode\\

" "$file"
    fi

    # 5. Replace all ctx.json_mode with json_mode
    sed -i '' 's/ctx\.json_mode/json_mode/g' "$file"

    echo "✓ $cmd.py - Updated"
done

echo
echo "✓ Done! All commands now support both patterns:"
echo "  odoo-cli --json search res.partner '[]'  (global)"
echo "  odoo-cli search res.partner '[]' --json  (command, LLM-friendly!)"
