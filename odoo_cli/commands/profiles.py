"""
Profile management commands for odoo-cli.

Allows listing, showing, and testing environment profiles.
"""

import click
import json as json_lib
from typing import Optional

from odoo_cli.models.context import CliContext
from odoo_cli.models.profile import ProfileManager
from odoo_cli.utils.output import output_json, output_error


@click.group()
@click.pass_context
def profiles(ctx):
    """Manage environment profiles.

    Profiles allow quick switching between different Odoo environments
    (production, staging, dev) without editing config files.

    Configure profiles in ~/.config/odoo-cli/config.yaml:

    \b
    profiles:
      production:
        url: "https://company.odoo.com"
        db: "company-prod"
        username: "admin@company.com"
        password: "secret"
        default: true
      staging:
        url: "https://company-staging.odoo.com"
        db: "company-staging"
        username: "admin@company.com"
        password: "secret"
    """
    pass


@profiles.command("list")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_obj
def list_profiles(ctx: Optional[CliContext], json_mode: bool):
    """List all available profiles."""
    # Determine JSON mode
    if ctx:
        json_mode = json_mode or ctx.json_mode

    pm = ProfileManager()

    if not pm.has_profiles():
        if json_mode:
            output_json({
                "success": True,
                "profiles": [],
                "message": "No profiles configured",
                "hint": "Create ~/.config/odoo-cli/config.yaml with profiles section"
            })
        else:
            click.echo("No profiles configured.")
            click.echo("\nCreate ~/.config/odoo-cli/config.yaml with:")
            click.echo("  profiles:")
            click.echo("    production:")
            click.echo("      url: https://your-instance.odoo.com")
            click.echo("      db: your-database")
            click.echo("      username: admin@example.com")
            click.echo("      password: your-password")
        return

    active = pm.get_active_profile_name()
    profile_list = []

    for name in pm.list_profiles():
        profile = pm.profiles[name]
        profile_list.append({
            "name": name,
            "url": profile.url,
            "db": profile.db,
            "default": profile.default,
            "readonly": profile.readonly,
            "protected": profile.protected,
            "active": name == active,
        })

    if json_mode:
        output_json({
            "success": True,
            "profiles": profile_list,
            "active_profile": active,
            "config_file": str(pm.config_path) if pm.config_path else None,
        })
    else:
        click.echo(f"Profiles from: {pm.config_path}\n")
        for p in profile_list:
            marker = " [active]" if p["active"] else ""
            default = " (default)" if p["default"] else ""
            readonly = " [readonly]" if p["readonly"] else ""
            protected = " [protected]" if p["protected"] else ""
            click.echo(f"  {p['name']}{default}{readonly}{protected}{marker}")
            click.echo(f"    URL: {p['url']}")
            click.echo(f"    DB:  {p['db']}")
            click.echo()


@profiles.command("show")
@click.argument("profile_name")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_obj
def show_profile(ctx: Optional[CliContext], profile_name: str, json_mode: bool):
    """Show details for a specific profile (password masked)."""
    if ctx:
        json_mode = json_mode or ctx.json_mode

    pm = ProfileManager()

    if profile_name not in pm.profiles:
        available = ", ".join(pm.list_profiles()) if pm.has_profiles() else "none"
        if json_mode:
            output_error(
                f"Profile '{profile_name}' not found",
                error_type="profile",
                details=f"Available profiles: {available}",
                suggestion="Use 'odoo-cli profiles list' to see all profiles",
                json_mode=True,
            )
        else:
            click.echo(f"Error: Profile '{profile_name}' not found")
            click.echo(f"Available profiles: {available}")
        return

    profile = pm.profiles[profile_name]

    if json_mode:
        output_json({
            "success": True,
            "profile": profile.to_dict(mask_password=True),
        })
    else:
        click.echo(f"Profile: {profile_name}")
        click.echo(f"  URL:        {profile.url}")
        click.echo(f"  Database:   {profile.db}")
        click.echo(f"  Username:   {profile.username}")
        click.echo(f"  Password:   ***")
        click.echo(f"  Timeout:    {profile.timeout}s")
        click.echo(f"  Verify SSL: {profile.verify_ssl}")
        click.echo(f"  Default:    {profile.default}")
        click.echo(f"  Readonly:   {profile.readonly}")
        click.echo(f"  Protected:  {profile.protected}")


@profiles.command("test")
@click.argument("profile_name")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_obj
def test_profile(ctx: Optional[CliContext], profile_name: str, json_mode: bool):
    """Test connectivity for a profile."""
    if ctx:
        json_mode = json_mode or ctx.json_mode

    pm = ProfileManager()

    # Validate profile exists
    validation = pm.validate_profile(profile_name)
    if not validation["valid"]:
        if json_mode:
            output_json({
                "success": False,
                "error": validation["error"],
                "available_profiles": validation.get("available_profiles"),
            })
        else:
            click.echo(f"Error: {validation['error']}")
        return

    profile = pm.profiles[profile_name]

    # Try to connect
    try:
        from odoo_cli.client import get_odoo_client

        client = get_odoo_client(
            url=profile.url,
            db=profile.db,
            username=profile.username,
            password=profile.password,
            timeout=profile.timeout,
            verify_ssl=profile.verify_ssl,
        )

        # Test with a simple call
        version = client.get_version()

        if json_mode:
            output_json({
                "success": True,
                "profile": profile_name,
                "status": "connected",
                "server_version": version,
                "url": profile.url,
                "db": profile.db,
            })
        else:
            click.echo(f"✓ Profile '{profile_name}' connected successfully!")
            click.echo(f"  Server: {profile.url}")
            click.echo(f"  Version: {version}")

    except Exception as e:
        if json_mode:
            output_json({
                "success": False,
                "profile": profile_name,
                "status": "failed",
                "error": str(e),
            })
        else:
            click.echo(f"✗ Profile '{profile_name}' connection failed!")
            click.echo(f"  Error: {e}")


@profiles.command("current")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_obj
def current_profile(ctx: Optional[CliContext], json_mode: bool):
    """Show the currently active profile."""
    if ctx:
        json_mode = json_mode or ctx.json_mode

    pm = ProfileManager()
    active = pm.get_active_profile_name()

    if not active:
        if json_mode:
            output_json({
                "success": True,
                "active_profile": None,
                "message": "No profile active, using .env configuration",
            })
        else:
            click.echo("No profile active. Using .env configuration.")
        return

    profile = pm.profiles.get(active)

    if json_mode:
        output_json({
            "success": True,
            "active_profile": active,
            "url": profile.url if profile else None,
            "db": profile.db if profile else None,
            "source": "ODOO_PROFILE env var" if active else "default",
        })
    else:
        click.echo(f"Active profile: {active}")
        if profile:
            click.echo(f"  URL: {profile.url}")
            click.echo(f"  DB:  {profile.db}")


@profiles.command("add")
@click.argument("profile_name")
@click.option("--url", required=True, help="Odoo server URL")
@click.option("--db", required=True, help="Database name")
@click.option("--username", "-u", required=True, help="Login username")
@click.option("--password", "-p", required=True, help="Login password")
@click.option("--timeout", type=int, default=30, help="Connection timeout (default: 30)")
@click.option("--no-verify-ssl", is_flag=True, help="Disable SSL verification")
@click.option("--default", "set_default", is_flag=True, help="Set as default profile")
@click.option("--readonly", is_flag=True, help="Block write operations (safe for production)")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_obj
def add_profile(
    ctx: Optional[CliContext],
    profile_name: str,
    url: str,
    db: str,
    username: str,
    password: str,
    timeout: int,
    no_verify_ssl: bool,
    set_default: bool,
    readonly: bool,
    json_mode: bool,
):
    """Add a new profile.

    Example:
        odoo-cli profiles add local --url http://localhost:8069 --db odoo --username admin --password admin
        odoo-cli profiles add prod --url https://prod.odoo.com --db prod --username admin --password secret --readonly
    """
    if ctx:
        json_mode = json_mode or ctx.json_mode

    pm = ProfileManager()
    result = pm.add_profile(
        name=profile_name,
        url=url,
        db=db,
        username=username,
        password=password,
        timeout=timeout,
        verify_ssl=not no_verify_ssl,
        default=set_default,
        readonly=readonly,
    )

    if json_mode:
        output_json(result)
    else:
        if result["success"]:
            click.echo(f"✓ {result['message']}")
            click.echo(f"  Config saved to: {pm.config_path}")
        else:
            click.echo(f"✗ Error: {result['error']}")


@profiles.command("edit")
@click.argument("profile_name")
@click.option("--url", help="New Odoo server URL")
@click.option("--db", help="New database name")
@click.option("--username", "-u", help="New username")
@click.option("--password", "-p", help="New password")
@click.option("--timeout", type=int, help="New connection timeout")
@click.option("--verify-ssl/--no-verify-ssl", default=None, help="SSL verification")
@click.option("--readonly/--no-readonly", default=None, help="Block/allow write operations")
@click.option("--confirm", is_flag=True, help="Confirm dangerous operations (removing readonly)")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_obj
def edit_profile(
    ctx: Optional[CliContext],
    profile_name: str,
    url: Optional[str],
    db: Optional[str],
    username: Optional[str],
    password: Optional[str],
    timeout: Optional[int],
    verify_ssl: Optional[bool],
    readonly: Optional[bool],
    confirm: bool,
    json_mode: bool,
):
    """Edit an existing profile.

    Only specify the fields you want to change.

    Example:
        odoo-cli profiles edit staging --url https://new-staging.odoo.com
        odoo-cli profiles edit staging --password newpassword
        odoo-cli profiles edit production --readonly
        odoo-cli profiles edit production --no-readonly --confirm
    """
    if ctx:
        json_mode = json_mode or ctx.json_mode

    pm = ProfileManager()
    result = pm.update_profile(
        name=profile_name,
        url=url,
        db=db,
        username=username,
        password=password,
        timeout=timeout,
        verify_ssl=verify_ssl,
        readonly=readonly,
        confirmed=confirm,
    )

    # Handle confirmation requirement for removing readonly
    if result.get("requires_confirmation") and not json_mode:
        click.echo(f"⚠️  WARNING: {result['error']}")
        click.echo(f"   {result.get('warning', '')}")
        click.echo()
        user_input = click.prompt(f"Type '{profile_name}' to confirm", default="")
        if user_input == profile_name:
            # Retry with confirmation
            result = pm.update_profile(
                name=profile_name,
                url=url,
                db=db,
                username=username,
                password=password,
                timeout=timeout,
                verify_ssl=verify_ssl,
                readonly=readonly,
                confirmed=True,
            )
        else:
            click.echo("Cancelled.")
            return

    if json_mode:
        output_json(result)
    else:
        if result["success"]:
            click.echo(f"✓ {result['message']}")
        else:
            click.echo(f"✗ Error: {result['error']}")
            if result.get("hint"):
                click.echo(f"   Hint: {result['hint']}")


@profiles.command("delete")
@click.argument("profile_name")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_obj
def delete_profile(
    ctx: Optional[CliContext],
    profile_name: str,
    force: bool,
    json_mode: bool,
):
    """Delete a profile.

    Example:
        odoo-cli profiles delete local
        odoo-cli profiles delete local --force
    """
    if ctx:
        json_mode = json_mode or ctx.json_mode

    pm = ProfileManager()

    # Check if profile exists
    if profile_name not in pm.profiles:
        if json_mode:
            output_json({"success": False, "error": f"Profile '{profile_name}' not found"})
        else:
            click.echo(f"✗ Error: Profile '{profile_name}' not found")
        return

    profile = pm.profiles[profile_name]

    # Check if profile is protected first
    if profile.protected:
        if json_mode:
            output_json({
                "success": False,
                "error": f"Profile '{profile_name}' is protected and cannot be deleted via CLI",
                "hint": "Edit ~/.config/odoo-cli/config.yaml directly to delete protected profiles",
            })
        else:
            click.echo(f"✗ Error: Profile '{profile_name}' is protected and cannot be deleted via CLI")
            click.echo(f"   Hint: Edit ~/.config/odoo-cli/config.yaml directly to delete protected profiles")
        return

    # Confirm deletion unless forced
    if not force and not json_mode:
        click.echo(f"Profile: {profile_name}")
        click.echo(f"  URL: {profile.url}")
        click.echo(f"  DB:  {profile.db}")
        if not click.confirm("Delete this profile?"):
            click.echo("Cancelled.")
            return

    result = pm.delete_profile(profile_name)

    if json_mode:
        output_json(result)
    else:
        if result["success"]:
            click.echo(f"✓ {result['message']}")
        else:
            click.echo(f"✗ Error: {result['error']}")


@profiles.command("rename")
@click.argument("old_name")
@click.argument("new_name")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_obj
def rename_profile(
    ctx: Optional[CliContext],
    old_name: str,
    new_name: str,
    json_mode: bool,
):
    """Rename a profile.

    Example:
        odoo-cli profiles rename staging staging-old
    """
    if ctx:
        json_mode = json_mode or ctx.json_mode

    pm = ProfileManager()
    result = pm.rename_profile(old_name, new_name)

    if json_mode:
        output_json(result)
    else:
        if result["success"]:
            click.echo(f"✓ {result['message']}")
        else:
            click.echo(f"✗ Error: {result['error']}")


@profiles.command("set-default")
@click.argument("profile_name")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON")
@click.pass_obj
def set_default_profile(
    ctx: Optional[CliContext],
    profile_name: str,
    json_mode: bool,
):
    """Set a profile as the default.

    The default profile is used when no --profile flag or ODOO_PROFILE is set.

    Example:
        odoo-cli profiles set-default production
    """
    if ctx:
        json_mode = json_mode or ctx.json_mode

    pm = ProfileManager()
    result = pm.set_default(profile_name)

    if json_mode:
        output_json(result)
    else:
        if result["success"]:
            click.echo(f"✓ {result['message']}")
        else:
            click.echo(f"✗ Error: {result['error']}")
