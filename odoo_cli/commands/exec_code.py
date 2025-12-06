"""
Execute Python code with pre-authenticated Odoo client.

This is the PRIMARY way for LLM agents to interact with Odoo.
The agent writes Python code, this command executes it.
"""

import click
import sys
import json as json_lib
import io
from contextlib import redirect_stdout, redirect_stderr
from typing import Optional
from datetime import datetime, date, timedelta
from pprint import pprint

from odoo_cli.models.context import CliContext
from odoo_cli.utils.output import output_json, output_error


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
