"""
A read timeout is not retried (the server keeps running the call), a connection error is; known
whole-table scans are refused on production unless allowed.
"""

import datetime

import pytest
import requests
from urllib3.exceptions import ReadTimeoutError
from click.testing import CliRunner

import odoo_cli.client as client_module
from odoo_cli.client import (ALLOW_HEAVY_ENV, HeavyQueryRefused, OdooClient, ServerStillRunningTimeout,
                             heavy_query_reason)


RECENT = (datetime.date.today() - datetime.timedelta(days=3)).isoformat()


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

    def test_a_timeout_while_reading_the_body_is_not_retried(self, monkeypatch):
        # requests raises it as ConnectionError(ReadTimeoutError) once the headers have arrived
        wrapped = requests.exceptions.ConnectionError(ReadTimeoutError(None, "/jsonrpc", "Read timed out."))
        client, calls = make_client(raises=[wrapped], monkeypatch=monkeypatch)
        with pytest.raises(ServerStillRunningTimeout):
            client.search_read("res.partner", [])
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
            client.search_read("queue.job", [("func_string", "ilike", "x"), ("date_created", ">=", RECENT)])
        with pytest.raises(HeavyQueryRefused):
            client.search_count("queue.job", [("func_string", "ilike", "x"), ("method_name", "=", "send")])
        assert calls == []

    def test_queue_job_func_string_with_window_and_method_passes(self, monkeypatch):
        monkeypatch.delenv(ALLOW_HEAVY_ENV, raising=False)
        client, calls = make_client(readonly=True)
        client.search_read("queue.job", ["&", "&", ("func_string", "ilike", "x"),
                                         ("date_created", ">=", RECENT), ("method_name", "=", "send")])
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

    def test_cli_flag_is_listed(self):
        from odoo_cli.cli import cli
        result = CliRunner().invoke(cli, ["--help"])
        assert "--allow-heavy-query" in result.output

    def test_every_branch_must_be_restricted(self, monkeypatch):
        monkeypatch.delenv(ALLOW_HEAVY_ENV, raising=False)
        client, calls = make_client(readonly=True)
        for domain in (
            ["|", ("body", "ilike", "x"), ("res_id", "=", 7)],          # the body branch is unrestricted
            [("body", "ilike", "x"), "!", ("res_id", "in", [7])],       # a negated res_id restricts nothing
            ["!", ("body", "not ilike", "x")],
        ):
            with pytest.raises(HeavyQueryRefused):
                client.search_read("mail.message", domain)
        client.search_read("mail.message", ["|", ("body", "ilike", "x"), ("subject", "ilike", "y"), ("res_id", "in", [7])])
        assert calls == [["mail.message", "search_read"]]

    def test_an_old_date_or_a_negative_filter_is_no_window(self, monkeypatch):
        monkeypatch.delenv(ALLOW_HEAVY_ENV, raising=False)
        client, _calls = make_client(readonly=True)
        with pytest.raises(HeavyQueryRefused):
            client.search_read("queue.job", [("func_string", "ilike", "x"), ("date_created", ">=", "1900-01-01"),
                                             ("method_name", "=", "send")])
        with pytest.raises(HeavyQueryRefused):
            client.search_read("queue.job", [("func_string", "ilike", "x"), ("date_created", ">=", RECENT),
                                             ("method_name", "!=", False)])

    def test_records_pinned_by_id_pass(self, monkeypatch):
        monkeypatch.delenv(ALLOW_HEAVY_ENV, raising=False)
        client, calls = make_client(readonly=True)
        client.search_read("queue.job", [("id", "=", 7), ("func_string", "ilike", "x")])
        client.search_read("mail.message", [("id", "in", [1, 2]), ("body", "ilike", "x")])
        assert len(calls) == 2

    def test_name_search_execute_and_nested_domains_are_checked(self, monkeypatch):
        monkeypatch.delenv(ALLOW_HEAVY_ENV, raising=False)
        client, calls = make_client(readonly=True)
        with pytest.raises(HeavyQueryRefused):
            client.execute("mail.message", "name_search", "", [("body", "ilike", "x")])
        with pytest.raises(HeavyQueryRefused):
            client.execute("mail.message", "search", [("parent_id", "any", [("body", "ilike", "x")])])
        payload = {"jsonrpc": "2.0", "method": "call", "id": 1, "params": {
            "service": "object", "method": "execute",
            "args": ["demo", 2, "x", "mail.message", "search", [("body", "ilike", "x")]]}}
        with pytest.raises(HeavyQueryRefused):
            client._jsonrpc_call(payload)
        assert calls == []

    def test_the_cli_flag_reaches_the_client(self, monkeypatch):
        from odoo_cli.models import context as context_module
        made = OdooClient(url="https://example.com", db="d", username="u", password="x")
        monkeypatch.setattr("odoo_cli.client.get_odoo_client", lambda **kwargs: made)
        ctx = context_module.CliContext(config={"url": "u", "db": "d", "username": "u", "password": "x"},
                                        json_mode=True, console=None, allow_heavy_query=True)
        monkeypatch.setattr(ctx, "require_profile", lambda: None, raising=False)
        assert ctx.client.allow_heavy_query is True

    def test_a_dotted_path_to_the_text_field_counts(self, monkeypatch):
        monkeypatch.delenv(ALLOW_HEAVY_ENV, raising=False)
        client, calls = make_client(readonly=True)
        with pytest.raises(HeavyQueryRefused):
            client.search_read("mail.message", [("parent_id.body", "ilike", "x")])
        with pytest.raises(HeavyQueryRefused):
            client.search_read("mail.message", [("parent_id", "any", [("parent_id.body", "ilike", "x")])])
        assert calls == []

    def test_a_negated_inequality_restricts_and_a_large_domain_without_text_passes(self, monkeypatch):
        monkeypatch.delenv(ALLOW_HEAVY_ENV, raising=False)
        client, calls = make_client(readonly=True)
        client.search_read("mail.message", [("body", "ilike", "x"), "!", ("res_id", "!=", 7)])
        big = []
        for i in range(9):
            big += ["|", ("subject", "ilike", str(i)), ("record_name", "ilike", str(i))]
        client.search_read("mail.message", big)
        assert len(calls) == 2

