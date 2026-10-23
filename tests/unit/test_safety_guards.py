"""
Unit tests for the two safety guards: a readonly profile runs only read methods without --force,
and a named profile that does not exist stops the run instead of falling back.
"""

import json

import pytest
from click.testing import CliRunner

import odoo_cli.config as config_module
from odoo_cli.cli import cli
from odoo_cli.client import OdooClient
from odoo_cli.config import ProfileNotFoundError, load_config


def readonly_client(readonly=True):
    client = OdooClient(url="https://example.com", db="demo", username="admin", password="x", readonly=readonly)
    client.uid = 2  # connected
    calls = []
    client._jsonrpc_call = lambda payload: calls.append(payload["params"]["args"][4]) or []
    return client, calls


class TestReadonlyGuard:
    """A readonly profile refuses every method outside the read allowlist."""

    def test_a_custom_module_method_is_refused_without_force(self):
        client, calls = readonly_client()
        with pytest.raises(PermissionError, match="action_confirm"):
            client.execute("sale.order", "action_confirm", [1])
        with pytest.raises(PermissionError, match="--force"):
            client.execute("product.template", "custom_scope_apply", "name", False)
        assert calls == []

    def test_standard_writes_stay_refused(self):
        client, calls = readonly_client()
        for method in ("create", "write", "unlink", "copy"):
            with pytest.raises(PermissionError):
                client.execute("res.partner", method, [1])
        assert calls == []

    def test_read_methods_run(self):
        client, calls = readonly_client()
        client.search_read("res.partner", [], ["name"])
        client.search_count("res.partner", [])
        client.execute("res.partner", "read_group", [], ["name"], ["name"])
        client.execute("ir.model.data", "check_object_reference", "base", "main_company")
        assert calls == ["search_read", "search_count", "read_group", "check_object_reference"]

    def test_force_and_a_writable_profile_pass_everything(self):
        client, calls = readonly_client()
        client._force_write = True
        client.execute("sale.order", "action_confirm", [1])
        writable, writable_calls = readonly_client(readonly=False)
        writable.execute("sale.order", "action_confirm", [1])
        assert calls == ["action_confirm"] and writable_calls == ["action_confirm"]


class FakeProfiles:
    def __init__(self, profiles):
        self.profiles = profiles

    def list_profiles(self):
        return list(self.profiles)

    def get_config(self, name=None):
        return self.profiles.get(name) if name else None

    def get_profile(self, name=None):
        return None


@pytest.fixture
def profiles(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # no .env of the developer's checkout
    monkeypatch.delenv("ODOO_PROFILE", raising=False)
    monkeypatch.setattr(config_module, "get_config_search_paths", lambda: [])
    fake = FakeProfiles({"staging": {"url": "https://staging.example.com", "db": "demo_staging",
                                     "username": "admin", "password": "x"}})
    monkeypatch.setattr(config_module, "_profile_manager", fake)
    return fake


class TestUnknownProfile:
    """A named profile that is not defined never falls back to another configuration."""

    def test_an_unknown_flag_profile_raises(self, profiles):
        with pytest.raises(ProfileNotFoundError, match="Unknown profile 'prod'.*staging"):
            load_config(profile="prod")

    def test_an_unknown_env_profile_raises(self, profiles, monkeypatch):
        monkeypatch.setenv("ODOO_PROFILE", "prod")
        with pytest.raises(ProfileNotFoundError):
            load_config()

    def test_a_known_profile_loads(self, profiles):
        assert load_config(profile="staging")["db"] == "demo_staging"

    def test_the_cli_exits_2_before_connecting(self, profiles):
        result = CliRunner().invoke(cli, ["--json", "-p", "prod", "exec", "-c", "result = 1"])
        assert result.exit_code == 2
        answer = json.loads(result.output)
        assert answer["success"] is False and answer["error_type"] == "profile_not_found"
