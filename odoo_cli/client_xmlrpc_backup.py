"""
Standalone Odoo XML-RPC client adapted from MCP server
Bundled directly into the CLI tool for independence
"""

import json
import os
import re
import socket
import urllib.parse
import http.client
import xmlrpc.client
from typing import Optional, Dict, Any, List, Union


class OdooClient:
    """Client for interacting with Odoo via XML-RPC"""

    def __init__(
        self,
        url: str,
        db: str,
        username: str,
        password: str,
        timeout: int = 30,
        verify_ssl: bool = True,
    ):
        """
        Initialize the Odoo client with connection parameters

        Args:
            url: Odoo server URL (with or without protocol)
            db: Database name
            username: Login username
            password: Login password
            timeout: Connection timeout in seconds
            verify_ssl: Whether to verify SSL certificates
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

        # Set timeout and SSL verification
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Setup connections
        self._common: Optional[xmlrpc.client.ServerProxy] = None
        self._models: Optional[xmlrpc.client.ServerProxy] = None

        # Parse hostname for logging
        parsed_url = urllib.parse.urlparse(self.url)
        self.hostname = parsed_url.netloc

    def connect(self) -> None:
        """Initialize the XML-RPC connection and authenticate"""
        # Create transport with appropriate settings
        is_https = self.url.startswith("https://")
        transport = RedirectTransport(
            timeout=self.timeout,
            use_https=is_https,
            verify_ssl=self.verify_ssl
        )

        # Setup endpoints
        self._common = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/common", transport=transport, allow_none=True
        )
        self._models = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/object", transport=transport, allow_none=True
        )

        # Authenticate and get user ID
        try:
            self.uid = self._common.authenticate(
                self.db, self.username, self.password, {}
            )
            if not self.uid:
                raise ValueError("Authentication failed: Invalid username or password")
        except (socket.error, socket.timeout, ConnectionError, TimeoutError) as e:
            raise ConnectionError(f"Failed to connect to Odoo server: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to authenticate with Odoo: {str(e)}")

    def _ensure_connected(self) -> None:
        """Ensure client is connected before operations"""
        if not self.uid:
            self.connect()

    def _execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """Execute a method on an Odoo model"""
        self._ensure_connected()
        return self._models.execute_kw(
            self.db, self.uid, self.password, model, method, args, kwargs
        )

    def execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """
        Execute an arbitrary method on a model

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
        order: Optional[str] = None
    ) -> List[int]:
        """
        Search for record IDs matching a domain

        Args:
            model: Model name (e.g., 'res.partner')
            domain: Search domain (default: [])
            offset: Number of records to skip
            limit: Maximum number of records
            order: Sort order (e.g., 'name ASC')

        Returns:
            List of matching record IDs
        """
        domain = domain or []
        kwargs = {'offset': offset}
        if limit is not None:
            kwargs['limit'] = limit
        if order is not None:
            kwargs['order'] = order

        return self._execute(model, 'search', [domain], **kwargs)

    def read(
        self,
        model: str,
        ids: List[int],
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Read records by IDs

        Args:
            model: Model name
            ids: List of record IDs
            fields: Fields to read (None for all)

        Returns:
            List of record dictionaries
        """
        kwargs = {}
        if fields is not None:
            kwargs['fields'] = fields

        return self._execute(model, 'read', ids, kwargs)

    def search_read(
        self,
        model: str,
        domain: List = None,
        fields: Optional[List[str]] = None,
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search and read records in a single call

        Args:
            model: Model name (e.g., 'res.partner')
            domain: Search domain (default: [])
            fields: Fields to return (None for all)
            offset: Number of records to skip
            limit: Maximum number of records
            order: Sort order

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

        return self._execute(model, 'search_read', [domain], **kwargs)

    def search_count(self, model: str, domain: List = None) -> int:
        """
        Count records matching a domain

        Args:
            model: Model name
            domain: Search domain (default: [])

        Returns:
            Number of matching records
        """
        domain = domain or []
        return self._execute(model, 'search_count', [domain])

    def fields_get(
        self,
        model: str,
        allfields: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get field definitions for a model

        Args:
            model: Model name
            allfields: Specific fields to get (None for all)

        Returns:
            Dictionary of field definitions
        """
        kwargs = {}
        if allfields is not None:
            kwargs['allfields'] = allfields

        return self._execute(model, 'fields_get', [], kwargs)

    def get_models(self) -> List[str]:
        """
        Get list of all available models

        Returns:
            List of model names
        """
        model_ids = self._execute('ir.model', 'search', [])
        if not model_ids:
            return []

        records = self._execute('ir.model', 'read', model_ids, ['model'])
        return sorted([r['model'] for r in records])

    def search_employees(self, name_pattern: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for employees by name pattern

        Args:
            name_pattern: Name to search for
            limit: Maximum results

        Returns:
            List of employee records
        """
        domain = [('name', 'ilike', name_pattern)]
        fields = ['name', 'work_email', 'department_id', 'job_id', 'user_id']

        return self.search_read('hr.employee', domain, fields, limit=limit)

    def search_holidays(
        self,
        employee_name: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for time-off/holiday records

        Args:
            employee_name: Filter by employee name
            state: Filter by state (draft, confirm, validate, refuse)
            limit: Maximum results

        Returns:
            List of holiday records
        """
        domain = []

        if employee_name:
            # First find employee IDs
            emp_domain = [('name', 'ilike', employee_name)]
            emp_ids = self.search('hr.employee', emp_domain)
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

        return self.search_read('hr.leave', domain, fields, limit=limit)


class RedirectTransport(xmlrpc.client.Transport):
    """Transport that adds timeout, SSL verification, and redirect handling"""

    def __init__(
        self,
        timeout: int = 30,
        use_https: bool = True,
        verify_ssl: bool = True,
        max_redirects: int = 5
    ):
        super().__init__()
        self.timeout = timeout
        self.use_https = use_https
        self.verify_ssl = verify_ssl
        self.max_redirects = max_redirects

        # Handle SSL verification
        if use_https and not verify_ssl:
            import ssl
            self.context = ssl._create_unverified_context()
        else:
            self.context = None

    def make_connection(self, host: str) -> http.client.HTTPConnection:
        """Create HTTP(S) connection with timeout"""
        if self.use_https:
            if self.context:
                conn = http.client.HTTPSConnection(
                    host, timeout=self.timeout, context=self.context
                )
            else:
                conn = http.client.HTTPSConnection(host, timeout=self.timeout)
        else:
            conn = http.client.HTTPConnection(host, timeout=self.timeout)

        return conn

    def request(self, host: str, handler: str, request_body: bytes, verbose: bool = False):
        """Send request with redirect handling"""
        redirects = 0

        while redirects < self.max_redirects:
            try:
                return super().request(host, handler, request_body, verbose)
            except xmlrpc.client.ProtocolError as err:
                if err.errcode in (301, 302, 303, 307, 308):
                    if 'location' in err.headers:
                        redirects += 1
                        location = err.headers.get('location')
                        parsed = urllib.parse.urlparse(location)
                        if parsed.netloc:
                            host = parsed.netloc
                        handler = parsed.path
                        if parsed.query:
                            handler += '?' + parsed.query
                        continue
                raise

        raise xmlrpc.client.ProtocolError(
            host + handler, 310, 'Too many redirects', {}
        )


def get_odoo_client(
    url: Optional[str] = None,
    db: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    timeout: Optional[int] = None,
    verify_ssl: Optional[bool] = None
) -> OdooClient:
    """
    Get configured Odoo client instance

    Args:
        url: Override URL from config
        db: Override database from config
        username: Override username from config
        password: Override password from config
        timeout: Connection timeout in seconds
        verify_ssl: Whether to verify SSL certificates

    Returns:
        Configured OdooClient instance
    """
    # Import here to avoid circular dependency
    from odoo_cli.config import load_config

    config = load_config()

    # Override with provided arguments
    url = url or config.get('url')
    db = db or config.get('db')
    username = username or config.get('username')
    password = password or config.get('password')
    timeout = timeout or config.get('timeout', 30)
    verify_ssl = verify_ssl if verify_ssl is not None else config.get('verify_ssl', True)

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
        verify_ssl=verify_ssl
    )

    # Connect immediately
    client.connect()

    return client