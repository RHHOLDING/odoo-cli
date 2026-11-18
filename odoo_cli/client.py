"""
Odoo JSON-RPC client for high-performance API interactions.

This client provides a simple interface to interact with Odoo via JSON-RPC protocol,
offering 75% higher throughput and 43% faster response times compared to XML-RPC.

Features:
- Persistent HTTP session with connection pooling
- Retry on connection errors only (2s delay, max 3 attempts); a timeout is not retried, the
  server keeps running the call
- Refuses known heavy scans on production unless overridden
- Response caching for frequently accessed data
- Configurable timeout and SSL verification
"""

import json
import os
import re
import time
import logging
import urllib.parse
from typing import Optional, Dict, Any, List, Union
from functools import wraps

import requests

logger = logging.getLogger(__name__)


class ServerStillRunningTimeout(TimeoutError):
    """No answer within the client timeout. The server is still running the call."""


class HeavyQueryRefused(PermissionError):
    """A search known to scan a whole large table on production, refused before it is sent."""


# Set to 1 to run a refused heavy query on purpose (same as --allow-heavy-query).
ALLOW_HEAVY_ENV = 'ODOO_CLI_ALLOW_HEAVY_QUERY'
# Model methods whose first positional argument (or ``domain`` keyword) is a search domain.
DOMAIN_METHODS = frozenset({
    'search', 'search_read', 'search_count', 'search_fetch', 'read_group',
    'web_search_read', 'web_read_group',
})
LIKE_OPERATORS = frozenset({'like', 'ilike', '=like', '=ilike', 'not like', 'not ilike'})


def _domain_leaves(domain: Any) -> List[tuple]:
    """The ``(field, operator, value)`` leaves of a domain (operators ``&``, ``|``, ``!`` skipped)."""
    leaves = []
    for item in domain or []:
        if isinstance(item, (list, tuple)) and len(item) == 3 and isinstance(item[0], str):
            leaves.append((item[0].split('.')[0], str(item[1]).lower(), item[2]))
    return leaves


def heavy_query_reason(model: str, method: str, args: tuple, kwargs: Dict[str, Any]) -> Optional[str]:
    """Why this call would scan a whole large table on production, or None.

    Two patterns took 30-180 s each on production (pg_slow_queries, November 2026) and, with the
    old retry on timeout, held up to three of its eight HTTP workers at once:

    - ``queue.job`` searched by ``func_string`` (like/ilike) without a ``date_created`` window and a
      ``model_name`` or ``method_name`` filter;
    - ``mail.message`` searched by ``body`` (like/ilike) without ``res_id`` (``=`` or ``in``).
    """
    if method not in DOMAIN_METHODS:
        return None
    domain = kwargs.get('domain')
    if domain is None and args and isinstance(args[0], (list, tuple)):
        domain = args[0]
    leaves = _domain_leaves(domain)
    fields = {field for field, _op, _value in leaves}
    liked = {field for field, op, _value in leaves if op in LIKE_OPERATORS}
    if model == 'queue.job' and 'func_string' in liked:
        dated = any(field == 'date_created' and op in ('>', '>=', '=') for field, op, _value in leaves)
        narrowed = bool(fields & {'model_name', 'method_name'})
        if not (dated and narrowed):
            return ("queue.job searched by func_string (like/ilike) without a date_created window "
                    "('>=' a recent date) and a model_name or method_name filter")
    if model == 'mail.message' and 'body' in liked:
        if not any(field == 'res_id' and op in ('=', 'in') for field, op, _value in leaves):
            return "mail.message searched by body (like/ilike) without res_id ('=' or 'in')"
    return None


def retry_on_network_error(max_retries: int = 3, delay: float = 2.0):
    """
    Decorator to retry a function on connection errors.

    Only a connection that could not be made or broke is retried. A read timeout is not: the
    request reached the server, which keeps running it (and holds a worker) until it finishes, so a
    retry would run the same work again next to it.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay in seconds between retries
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.ConnectionError as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Network error (attempt {attempt + 1}/{max_retries}): {str(e)}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    continue

            # All retries exhausted
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class OdooClient:
    """
    JSON-RPC client for interacting with Odoo via high-performance protocol.

    Uses persistent HTTP session with connection pooling for optimal performance.
    Automatically retries on network errors and caches frequently accessed data.
    """

    def __init__(
        self,
        url: str,
        db: str,
        username: str,
        password: str,
        timeout: int = 30,
        verify_ssl: bool = True,
        readonly: bool = False,
    ):
        """
        Initialize the Odoo JSON-RPC client.

        Args:
            url: Odoo server URL (with or without protocol)
            db: Database name
            username: Login username
            password: Login password
            timeout: Connection timeout in seconds (default: 30)
            verify_ssl: Whether to verify SSL certificates (default: True)
            readonly: If True, block all write operations (default: False)
        """
        # Ensure URL has a protocol
        if not re.match(r"^https?://", url):
            url = f"https://{url}"

        # Remove trailing slash from URL if present
        url = url.rstrip("/")

        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid: Optional[int] = None
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.readonly = readonly
        self._force_write = False  # Temporary override for --force flag
        # Run a heavy query refused on production anyway (--allow-heavy-query or the environment)
        self.allow_heavy_query = os.environ.get(ALLOW_HEAVY_ENV, '').lower() in ('1', 'true', 'yes')

        # Create persistent session with connection pooling
        self.session = requests.Session()

        # Configure connection pooling (single persistent connection)
        from requests.adapters import HTTPAdapter
        adapter = HTTPAdapter(pool_connections=1, pool_maxsize=1)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        # Parse hostname for logging
        parsed_url = urllib.parse.urlparse(self.url)
        self.hostname = parsed_url.netloc

    def connect(self) -> None:
        """
        Authenticate with the Odoo server via JSON-RPC.

        Raises:
            ValueError: If authentication fails (invalid credentials)
            ConnectionError: If unable to connect to server
        """
        try:
            # Prepare JSON-RPC request for login
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "login",
                    "args": [self.db, self.username, self.password]
                },
                "id": 1
            }

            # Send request
            response = self.session.post(
                f"{self.url}/jsonrpc",
                json=payload,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            # Parse response
            data = response.json()

            # Check for errors
            if "error" in data:
                error_info = data.get("error", {})
                raise ValueError(
                    f"Authentication failed: {error_info.get('message', 'Unknown error')}"
                )

            # Extract uid from result
            self.uid = data.get("result")

            if not self.uid:
                raise ValueError("Authentication failed: Invalid username or password")

            logger.info(f"Successfully authenticated with {self.hostname} (uid: {self.uid})")

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to Odoo server: {str(e)}")

    def _ensure_connected(self) -> None:
        """Ensure client is connected before operations."""
        if not self.uid:
            self.connect()

    def _check_readonly(self, payload: Dict[str, Any]) -> None:
        """Refuse a model call outside :attr:`READ_METHODS` on a readonly profile (unless --force).

        Checked on the one request path every model call takes, so a payload built by hand is held
        to the same rule. ``common`` (login, version) always passes; of the ``db`` service only the
        listing methods do; any other service or call shape is refused.
        """
        if not self.readonly or self._force_write:
            return
        params = payload.get("params") or {}
        service, rpc = params.get("service"), params.get("method")
        if service == "common":
            return  # login, version
        if service == "db":
            # The database service creates, drops, duplicates and restores databases.
            if rpc in self.READ_DB_METHODS:
                return
            method = f"db.{rpc}"
        else:
            args = params.get("args") or []
            method = args[4] if service == "object" and rpc in ("execute", "execute_kw") and len(args) > 4 else rpc
        if method not in self.READ_METHODS:
            raise PermissionError(
                f"Method '{method}' blocked: profile is configured as readonly and only read methods "
                f"({', '.join(sorted(self.READ_METHODS))}) run without --force. If '{method}' only reads, "
                f"pass --force deliberately; otherwise use a non-readonly profile."
            )

    def _is_production(self) -> bool:
        """Production for the heavy-query guard: a readonly profile or a production database."""
        return bool(self.readonly) or 'production' in (self.db or '').lower()

    def _check_heavy_query(self, payload: Dict[str, Any]) -> None:
        """Refuse a known whole-table scan on production unless allowed (see heavy_query_reason)."""
        if self.allow_heavy_query or not self._is_production():
            return
        params = payload.get("params") or {}
        args = params.get("args") or []
        if params.get("service") != "object" or params.get("method") != "execute_kw" or len(args) < 5:
            return
        call_args = args[5] if len(args) > 5 and isinstance(args[5], (list, tuple)) else []
        call_kwargs = args[6] if len(args) > 6 and isinstance(args[6], dict) else {}
        reason = heavy_query_reason(args[3], args[4], tuple(call_args), call_kwargs)
        if reason:
            raise HeavyQueryRefused(
                f"Refused on production: {reason}. Such a search scans the whole table (30-180 s) and "
                f"holds a server worker meanwhile. Narrow it, or run it deliberately outside 05-10 UTC "
                f"with --allow-heavy-query (or {ALLOW_HEAVY_ENV}=1)."
            )

    @retry_on_network_error(max_retries=3, delay=2.0)
    def _jsonrpc_call(self, payload: Dict[str, Any]) -> Any:
        """
        Execute a JSON-RPC call with automatic retry on network errors.

        Args:
            payload: JSON-RPC request payload

        Returns:
            The result field from JSON-RPC response

        Raises:
            ValueError: If Odoo returns an error
            requests.RequestException: If network error after retries
        """
        self._check_readonly(payload)
        self._check_heavy_query(payload)
        try:
            response = self.session.post(
                f"{self.url}/jsonrpc",
                json=payload,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
        except requests.exceptions.ReadTimeout as e:
            raise ServerStillRunningTimeout(
                f"No answer from {self.hostname} within {self.timeout}s. The server keeps running this "
                f"call until it finishes and holds a worker meanwhile; it was not sent again. Do not "
                f"resend it at once: narrow the query (date window, ids) or raise --timeout."
            ) from e

        data = response.json()

        # Check for JSON-RPC errors
        if "error" in data:
            error_info = data.get("error", {})
            error_msg = error_info.get("message", "Unknown error")
            error_data = error_info.get("data", {})

            # Extract Odoo-specific error details if available
            if isinstance(error_data, dict):
                odoo_error = error_data.get("message", "")
                if odoo_error:
                    error_msg = f"{error_msg}: {odoo_error}"

            raise ValueError(f"Odoo error: {error_msg}")

        return data.get("result")

    # Methods a readonly profile may call without --force. Everything else is refused: a module's own
    # method (``action_*``, ``button_*``, ``*_apply`` ...) writes as easily as ``write`` does, and a
    # blocklist of the standard write methods let such a call through. ``default_get`` is left out on
    # purpose: a default may draw from a sequence, which writes.
    READ_METHODS = frozenset({
        'read', 'search', 'search_read', 'search_count', 'search_fetch',
        'fields_get', 'name_get', 'name_search', 'read_group',
        'web_read', 'web_search_read', 'web_read_group',
        'exists', 'get_metadata',
        'check_access_rights', 'check_access_rule', 'has_access',
        'get_views', 'fields_view_get', 'load_views',
        'xmlid_to_res_id', '_xmlid_to_res_id', 'check_object_reference', 'context_get',
    })
    READ_DB_METHODS = frozenset({'list', 'db_exist', 'server_version', 'list_lang', 'list_countries'})

    def _execute(self, model: str, method: str, *args, context: Optional[Dict] = None, **kwargs) -> Any:
        """
        Execute a method on an Odoo model via execute_kw.

        Args:
            model: The model name (e.g., 'res.partner')
            method: Method name to execute
            *args: Positional arguments to pass to the method
            context: Optional context dictionary for Odoo operations
            **kwargs: Keyword arguments to pass to the method

        Returns:
            Result of the method execution

        Raises:
            PermissionError: If readonly mode is enabled and method is not a read method
        """
        self._ensure_connected()

        # Merge context with existing context (command context overrides)
        if context:
            existing_context = kwargs.get('context', {})
            kwargs['context'] = {**existing_context, **context}

        # Prepare JSON-RPC request for execute_kw
        # Note: args is converted to list for JSON serialization (JSON-RPC doesn't support tuples)
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [self.db, self.uid, self.password, model, method, list(args), kwargs]
            },
            "id": 1
        }

        return self._jsonrpc_call(payload)

    def execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """
        Execute an arbitrary method on a model.

        Args:
            model: The model name (e.g., 'res.partner')
            method: Method name to execute
            *args: Positional arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method

        Returns:
            Result of the method execution
        """
        return self._execute(model, method, *args, **kwargs)

    def search(
        self,
        model: str,
        domain: List = None,
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> List[int]:
        """
        Search for record IDs matching a domain.

        Args:
            model: Model name (e.g., 'res.partner')
            domain: Search domain (default: [])
            offset: Number of records to skip
            limit: Maximum number of records
            order: Sort order (e.g., 'name ASC')
            context: Optional context dictionary

        Returns:
            List of matching record IDs
        """
        domain = domain or []
        kwargs = {'offset': offset}
        if limit is not None:
            kwargs['limit'] = limit
        if order is not None:
            kwargs['order'] = order

        return self._execute(model, 'search', domain, context=context, **kwargs)

    def read(
        self,
        model: str,
        ids: List[int],
        fields: Optional[List[str]] = None,
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Read records by IDs.

        Args:
            model: Model name
            ids: List of record IDs
            fields: Fields to read (None for all)
            context: Optional context dictionary

        Returns:
            List of record dictionaries
        """
        kwargs = {}
        if fields is not None:
            kwargs['fields'] = fields

        return self._execute(model, 'read', ids, context=context, **kwargs)

    def search_read(
        self,
        model: str,
        domain: List = None,
        fields: Optional[List[str]] = None,
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Search and read records in a single call.

        Args:
            model: Model name (e.g., 'res.partner')
            domain: Search domain (default: [])
            fields: Fields to return (None for all)
            offset: Number of records to skip
            limit: Maximum number of records
            order: Sort order
            context: Optional context dictionary

        Returns:
            List of record dictionaries
        """
        domain = domain or []
        kwargs = {}

        if offset:
            kwargs['offset'] = offset
        if fields is not None:
            kwargs['fields'] = fields
        if limit is not None:
            kwargs['limit'] = limit
        if order is not None:
            kwargs['order'] = order

        return self._execute(model, 'search_read', domain, context=context, **kwargs)

    def search_count(self, model: str, domain: List = None, context: Optional[Dict] = None) -> int:
        """
        Count records matching a domain.

        Args:
            model: Model name
            domain: Search domain (default: [])
            context: Optional context dictionary

        Returns:
            Number of matching records
        """
        domain = domain or []
        return self._execute(model, 'search_count', domain, context=context)

    def fields_get(
        self,
        model: str,
        allfields: Optional[List[str]] = None,
        attributes: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get field definitions for a model.

        Args:
            model: Model name
            allfields: Specific fields to get (None for all)
            attributes: Specific field attributes to include (None for all)
                       Common attributes: 'type', 'string', 'required', 'readonly',
                       'help', 'relation', 'selection', 'domain', 'default'

        Returns:
            Dictionary of field definitions
        """
        kwargs = {}
        if allfields is not None:
            kwargs['allfields'] = allfields
        if attributes is not None:
            kwargs['attributes'] = attributes

        return self._execute(model, 'fields_get', **kwargs)

    def name_get(
        self,
        model: str,
        ids: List[int],
        context: Optional[Dict] = None
    ) -> List[tuple]:
        """
        Get display names for record IDs.

        Returns the text representation for the records with the given IDs.
        This is more efficient than reading records when you only need names.

        Args:
            model: Model name
            ids: List of record IDs
            context: Optional context dictionary

        Returns:
            List of tuples [(id, name), ...] with display names
        """
        return self._execute(model, 'name_get', ids, context=context)

    def name_search(
        self,
        model: str,
        name: str = '',
        domain: List = None,
        operator: str = 'ilike',
        limit: int = 100,
        context: Optional[Dict] = None
    ) -> List[tuple]:
        """
        Search for records by name.

        Performs a fuzzy search on the name field (or _rec_name) of a model.
        Returns results as (id, display_name) tuples, suitable for selection lists.

        Args:
            model: Model name
            name: Name pattern to search for (default: '')
            domain: Additional domain filter (default: [])
            operator: Comparison operator (default: 'ilike' for fuzzy match)
            limit: Maximum number of results (default: 100)
            context: Optional context dictionary

        Returns:
            List of tuples [(id, name), ...] matching the search
        """
        domain = domain or []
        # name_search signature: name_search(name='', args=None, operator='ilike', limit=100)
        # where args is the domain filter
        return self._execute(
            model,
            'name_search',
            name,
            domain,
            operator,
            limit,
            context=context
        )

    def get_models(self) -> List[str]:
        """
        Get list of all available models.

        Results are cached for 24 hours to improve performance.
        Cache is stored in ~/.odoo-cli/cache/

        Returns:
            Sorted list of model names
        """
        from odoo_cli.cache import get_cached, set_cached, get_cache_key_for_models

        # Try to get from cache first
        cache_key = get_cache_key_for_models(self.url, self.db)
        cached_models = get_cached(cache_key, ttl_seconds=86400)  # 24 hours

        if cached_models is not None:
            return cached_models

        # Cache miss - fetch from server (using helper methods for consistency)
        model_ids = self.search('ir.model', domain=[])
        if not model_ids:
            return []

        records = self.read('ir.model', ids=model_ids, fields=['model'])
        models = sorted([r['model'] for r in records])

        # Store in cache
        set_cached(cache_key, models, ttl_seconds=86400)

        return models

    def search_employees(self, name_pattern: str, limit: int = 20, context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search for employees by name pattern.

        Args:
            name_pattern: Name to search for
            limit: Maximum results
            context: Optional context dictionary

        Returns:
            List of employee records
        """
        domain = [('name', 'ilike', name_pattern)]
        fields = ['name', 'work_email', 'department_id', 'job_id', 'user_id']

        return self.search_read('hr.employee', domain, fields, limit=limit, context=context)

    def search_holidays(
        self,
        employee_name: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 20,
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for time-off/holiday records.

        Args:
            employee_name: Filter by employee name
            state: Filter by state (draft, confirm, validate, refuse)
            limit: Maximum results
            context: Optional context dictionary

        Returns:
            List of holiday records
        """
        domain = []

        if employee_name:
            # First find employee IDs
            emp_domain = [('name', 'ilike', employee_name)]
            emp_ids = self.search('hr.employee', emp_domain, context=context)
            if emp_ids:
                domain.append(('employee_id', 'in', emp_ids))
            else:
                return []  # No matching employees

        if state:
            domain.append(('state', '=', state))

        fields = [
            'employee_id', 'holiday_status_id', 'date_from',
            'date_to', 'state', 'number_of_days'
        ]

        return self.search_read('hr.leave', domain, fields, limit=limit, context=context)


def get_odoo_client(
    url: Optional[str] = None,
    db: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    timeout: Optional[int] = None,
    verify_ssl: Optional[bool] = None,
    readonly: Optional[bool] = None
) -> OdooClient:
    """
    Get configured Odoo JSON-RPC client instance.

    Args:
        url: Override URL from config
        db: Override database from config
        username: Override username from config
        password: Override password from config
        timeout: Connection timeout in seconds
        verify_ssl: Whether to verify SSL certificates
        readonly: If True, block all write operations

    Returns:
        Configured OdooClient instance

    Raises:
        ValueError: If required configuration is missing
    """
    # Import here to avoid circular dependency
    from odoo_cli.config import load_config

    # Read the configuration only for what the caller left out: the CLI passes everything, readonly
    # included, from the profile it resolved, and a second load would resolve ODOO_PROFILE again,
    # ignoring --profile. Without an explicit readonly the configuration decides it.
    config = {} if all([url, db, username, password]) and readonly is not None else load_config()

    # Override with provided arguments
    url = url or config.get('url')
    db = db or config.get('db')
    username = username or config.get('username')
    password = password or config.get('password')
    timeout = timeout or config.get('timeout', 30)
    verify_ssl = verify_ssl if verify_ssl is not None else config.get('verify_ssl', True)
    readonly = readonly if readonly is not None else config.get('readonly', False)

    if not all([url, db, username, password]):
        raise ValueError(
            "Missing required configuration. Please provide URL, database, username, and password."
        )

    client = OdooClient(
        url=url,
        db=db,
        username=username,
        password=password,
        timeout=timeout,
        verify_ssl=verify_ssl,
        readonly=readonly
    )

    # Connect immediately
    client.connect()

    return client
