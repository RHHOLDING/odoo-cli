"""
Execute Python code with pre-authenticated Odoo client.

This is the PRIMARY way for LLM agents to interact with Odoo.
The agent writes Python code, this command executes it.
"""

import click
import sys
import json as json_lib
import io
import re
from contextlib import redirect_stdout, redirect_stderr
from typing import Optional, Tuple, List
from datetime import datetime, date, timedelta
from pprint import pprint

from odoo_cli.models.context import CliContext
from odoo_cli.utils.output import output_json, output_error


# Patterns that indicate Odoo server-side `env` usage (not available in JSON-RPC)
ENV_PATTERNS = [
    (r'\benv\s*\[', "env['model']", "client.search_read('model', ...)"),
    (r'\benv\.ref\s*\(', "env.ref('xml_id')", "client.execute('ir.model.data', 'xmlid_to_res_id', 'module.xml_id')"),
    (r'\bself\.env\b', "self.env", "client (no self in JSON-RPC context)"),
    (r'\benv\.\w+\s*\(', "env.method()", "client.method() or client.execute()"),
    (r'\benv\.user\b', "env.user", "client.search_read('res.users', [['id', '=', uid]], ...)"),
    (r'\benv\.company\b', "env.company", "client.search_read('res.company', ...) with context"),
    (r'\benv\.context\b', "env.context", "Pass context via client methods"),
]


def _detect_env_usage(code: str) -> Tuple[bool, List[dict]]:
    """
    Detect if code uses Odoo server-side `env` patterns.

    Returns:
        Tuple of (has_env_usage, list of detected patterns with suggestions)
    """
    detected = []

    for pattern, example, replacement in ENV_PATTERNS:
        if re.search(pattern, code):
            detected.append({
                "pattern": example,
                "replacement": replacement,
            })

    return len(detected) > 0, detected


def _summarize_result(result) -> str:
    """Generate a brief human-readable summary of the result."""
    if result is None:
        return "executed (no result)"

    if isinstance(result, dict):
        # Try to create a meaningful summary from dict
        parts = []
        for key, value in list(result.items())[:4]:  # Max 4 items
            if isinstance(value, (int, float)):
                # Format numbers nicely
                if isinstance(value, float):
                    parts.append(f"{key}={value:,.2f}")
                else:
                    parts.append(f"{key}={value:,}")
            elif isinstance(value, list):
                parts.append(f"{key}=[{len(value)} items]")
            elif isinstance(value, str) and len(value) < 30:
                parts.append(f"{key}={value!r}")
        if len(result) > 4:
            parts.append(f"...+{len(result)-4} more")
        return ", ".join(parts) if parts else f"dict with {len(result)} keys"

    if isinstance(result, list):
        return f"{len(result)} records"

    if isinstance(result, (int, float)):
        if isinstance(result, float):
            return f"{result:,.2f}"
        return f"{result:,}"

    if isinstance(result, str):
        if len(result) > 50:
            return f"{result[:50]}..."
        return result

    return str(type(result).__name__)


@click.command('exec')
@click.argument('script', required=False, type=click.Path(exists=True))
@click.option('-c', '--code', 'inline_code', help='Execute inline Python code')
@click.option('--json', 'json_mode', is_flag=True, help='Output result as JSON')
@click.pass_obj
def exec_code(ctx: CliContext, script: Optional[str], inline_code: Optional[str], json_mode: bool):
    """
    Execute Python code with pre-authenticated Odoo client.

    The executed code has access to:
      - client: Authenticated OdooClient instance
      - json: JSON module
      - datetime, date, timedelta: Date utilities
      - pprint: Pretty printer

    Set 'result' variable to return structured data.

    \b
    Examples:
        # Run a script file
        odoo-cli exec script.py --json

        # Inline code
        odoo-cli exec -c "print(client.search_count('res.partner', []))"

        # Return structured result
        odoo-cli exec -c "result = client.search_read('res.partner', [], limit=5)" --json

        # Complex calculation
        odoo-cli exec avg_price.py --json

    \b
    Example script (avg_price.py):
        products = client.search_read('product.product', [['sale_ok', '=', True]], ['list_price'])
        avg = sum(p['list_price'] for p in products) / len(products) if products else 0
        result = {"average_price": round(avg, 2), "count": len(products)}
    """
    if ctx:
        json_mode = json_mode or ctx.json_mode

    # Need either script or inline code
    if not script and not inline_code:
        if json_mode:
            output_json({
                "success": False,
                "error": "No code provided. Use SCRIPT argument or -c flag.",
                "error_type": "usage",
            })
        else:
            click.echo("Error: Provide a script file or use -c for inline code")
            click.echo("  odoo-cli exec script.py")
            click.echo("  odoo-cli exec -c \"print(client.search_count('res.partner', []))\"")
        sys.exit(1)

    # Get the code to execute
    if script:
        with open(script, 'r') as f:
            code_to_run = f.read()
    else:
        code_to_run = inline_code

    # Get authenticated client
    try:
        client = ctx.client
    except Exception as e:
        if json_mode:
            output_json({
                "success": False,
                "error": str(e),
                "error_type": "connection",
            })
        else:
            click.echo(f"Connection error: {e}")
        sys.exit(1)

    # Check for common Odoo server-side patterns that won't work via JSON-RPC
    has_env_usage, env_patterns = _detect_env_usage(code_to_run)
    if has_env_usage:
        error_msg = (
            "'env' is not available in odoo-cli. "
            "This tool uses JSON-RPC, not server-side Python. Use 'client' instead."
        )
        if json_mode:
            output_json({
                "success": False,
                "error": error_msg,
                "error_type": "env_not_available",
                "detected_patterns": env_patterns,
                "hint": "Replace env.* calls with equivalent client.* methods. "
                        "Available: client.search(), client.read(), client.search_read(), "
                        "client.create(), client.write(), client.unlink(), client.execute()",
                "documentation": "Run: odoo-cli exec --help",
            })
        else:
            click.echo(f"Error: {error_msg}", err=True)
            click.echo("\nDetected patterns and replacements:", err=True)
            for p in env_patterns:
                click.echo(f"  {p['pattern']}  →  {p['replacement']}", err=True)
            click.echo("\nAvailable client methods:", err=True)
            click.echo("  client.search(), client.read(), client.search_read()", err=True)
            click.echo("  client.create(), client.write(), client.unlink()", err=True)
            click.echo("  client.execute(), client.search_count()", err=True)
        sys.exit(3)  # Operation error

    # Setup execution namespace
    namespace = {
        'client': client,
        'json': json_lib,
        'pprint': pprint,
        'datetime': datetime,
        'date': date,
        'timedelta': timedelta,
        'result': None,  # User can set this for structured output
    }

    # Capture stdout/stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Execute the code
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code_to_run, namespace)

        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()

        # Get result (either from 'result' variable or stdout)
        exec_result = namespace.get('result')

        if json_mode:
            response = {"success": True}

            if exec_result is not None:
                response["result"] = exec_result

            if stdout_output.strip():
                # Try to parse stdout as JSON if result not set
                if exec_result is None:
                    try:
                        response["result"] = json_lib.loads(stdout_output.strip())
                    except json_lib.JSONDecodeError:
                        response["output"] = stdout_output.strip()
                else:
                    response["output"] = stdout_output.strip()

            if stderr_output.strip():
                response["stderr"] = stderr_output.strip()

            # Print human-readable summary FIRST (before JSON)
            summary_result = response.get("result") or response.get("output")
            summary = _summarize_result(summary_result)
            click.echo(f"✓ {summary}")

            # JSON output comes after summary
            output_json(response)
        else:
            # Plain output mode
            if stdout_output:
                click.echo(stdout_output, nl=False)
            if stderr_output:
                click.echo(stderr_output, nl=False, err=True)
            if exec_result is not None and not stdout_output:
                # Pretty print result if nothing was printed
                pprint(exec_result)

    except Exception as e:
        stderr_output = stderr_capture.getvalue()

        if json_mode:
            output_json({
                "success": False,
                "error": str(e),
                "error_type": "execution",
                "stderr": stderr_output if stderr_output else None,
            })
        else:
            click.echo(f"Execution error: {e}", err=True)
            if stderr_output:
                click.echo(stderr_output, err=True)
        sys.exit(1)
