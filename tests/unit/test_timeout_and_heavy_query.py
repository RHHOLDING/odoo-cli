"""
A read timeout is not retried (the server keeps running the call), a connection error is; known
whole-table scans are refused on production unless allowed.
"""

import pytest
import requests
from click.testing import CliRunner

import odoo_cli.client as client_module
from odoo_cli.client import (ALLOW_HEAVY_ENV, HeavyQueryRefused, OdooClient, ServerStillRunningTimeout,
                             heavy_query_reason)


class FakeResponse:
    def json(self):
        return {"result": []}


def make_client(db="demo", readonly=False, raises=None, monkeypatch=None):
    """A connected client whose session records every request and raises the given errors in turn."""
    client = OdooClient(url="https://example.com", db=db, username="u", password="x", readonly=readonly,
                        timeout=5)
    client.uid = 2
    calls = []
    errors = list(raises or [])

    def post(url, json=None, **kwargs):
        calls.append(json["params"]["args"][3:5] if json["params"].get("service") == "object" else None)
        if errors:
            raise errors.pop(0)
        return FakeResponse()

    client.session.post = post
    if monkeypatch is not None:
        monkeypatch.setattr(client_module.time, "sleep", lambda _s: None)
    return client, calls


class TestTimeoutIsNotRetried:

    def test_a_read_timeout_is_sent_once_and_names_the_running_call(self, monkeypatch):
        client, calls = make_client(raises=[requests.exceptions.ReadTimeout("slow")], monkeypatch=monkeypatch)
        with pytest.raises(ServerStillRunningTimeout, match="keeps running this call"):
            client.search_read("res.partner", [], ["name"])
        assert len(calls) == 1

    def test_a_connection_error_is_still_retried(self, monkeypatch):
        client, calls = make_client(raises=[requests.exceptions.ConnectionError("reset")], monkeypatch=monkeypatch)
        assert client.search_read("res.partner", [], ["name"]) == []
        assert len(calls) == 2

    def test_a_connect_timeout_never_reached_the_server_and_is_retried(self, monkeypatch):
        client, calls = make_client(raises=[requests.exceptions.ConnectTimeout("no route")], monkeypatch=monkeypatch)
        assert client.search_count("res.partner", []) == []
        assert len(calls) == 2


class TestHeavyQueryGuard:

    def test_queue_job_func_string_without_window_is_refused_on_production(self, monkeypatch):
        monkeypatch.delenv(ALLOW_HEAVY_ENV, raising=False)
        client, calls = make_client(readonly=True)
        with pytest.raises(HeavyQueryRefused, match="func_string"):
            client.search_read("queue.job", [("func_string", "ilike", "AC000001478")], ["state"])
        # a date window alone is not enough, a model or method filter alone neither
        with pytest.raises(HeavyQueryRefused):
            client.search_read("queue.job", [("func_string", "ilike", "x"), ("date_created", ">=", "2026-11-11")])
        with pytest.raises(HeavyQueryRefused):
            client.search_count("queue.job", [("func_string", "ilike", "x"), ("method_name", "=", "send")])
        assert calls == []

    def test_queue_job_func_string_with_window_and_method_passes(self, monkeypatch):
        monkeypatch.delenv(ALLOW_HEAVY_ENV, raising=False)
        client, calls = make_client(readonly=True)
        client.search_read("queue.job", ["&", "&", ("func_string", "ilike", "x"),
                                         ("date_created", ">=", "2026-11-11"), ("method_name", "=", "send")])
        assert calls == [["queue.job", "search_read"]]

    def test_mail_message_body_needs_res_id(self, monkeypatch):
        monkeypatch.delenv(ALLOW_HEAVY_ENV, raising=False)
        client, calls = make_client(db="rhholding-production-1", readonly=False)
        with pytest.raises(HeavyQueryRefused, match="res_id"):
            client.search_read("mail.message", [("model", "in", ["purchase.order"]), ("body", "ilike", "Dispo-Notiz")])
        with pytest.raises(HeavyQueryRefused):
            client.execute("mail.message", "search", [("res_id", "!=", False), ("body", "ilike", "x")])
        client.search_read("mail.message", [("res_id", "in", [7, 8]), ("body", "ilike", "Dispo-Notiz")])
        client.search_read("mail.message", [("model", "=", "purchase.order")])  # no body search
        assert calls == [["mail.message", "search_read"], ["mail.message", "search_read"]]

    def test_domain_given_as_keyword_is_checked(self):
        assert heavy_query_reason("mail.message", "search_read", (), {"domain": [["body", "ilike", "x"]]})
        assert heavy_query_reason("mail.message", "read", ([1],), {}) is None

    def test_override_by_attribute_and_environment(self, monkeypatch):
        client, calls = make_client(readonly=True)
        client.allow_heavy_query = True
        client.search_read("mail.message", [("body", "ilike", "x")])
        monkeypatch.setenv(ALLOW_HEAVY_ENV, "1")
        other, other_calls = make_client(readonly=True)
        other.search_read("queue.job", [("func_string", "ilike", "x")])
        assert len(calls) == 1 and len(other_calls) == 1

    def test_not_production_is_not_checked(self, monkeypatch):
        monkeypatch.delenv(ALLOW_HEAVY_ENV, raising=False)
        client, calls = make_client(db="odoo_main", readonly=False)
        client.search_read("mail.message", [("body", "ilike", "x")])
        assert len(calls) == 1

    def test_cli_flag_reaches_the_client(self):
        from odoo_cli.cli import cli
        result = CliRunner().invoke(cli, ["--help"])
        assert "--allow-heavy-query" in result.output
