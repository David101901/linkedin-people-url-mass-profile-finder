import logging
from typing import Any, Dict, Optional

import requests

class HttpClient:
    """
    Lightweight HTTP client wrapper.

    This client is generic and does not contain any website-specific scraping logic.
    It can be reused wherever simple, logged HTTP GET requests are needed.
    """

    def __init__(self, logger: Optional[logging.Logger] = None, timeout: float = 10.0) -> None:
        self._session = requests.Session()
        self._timeout = timeout
        self._logger = logger or logging.getLogger("http_client")

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Perform a GET request and return the response text.

        Raises a requests.HTTPError if a non-success status code is returned.
        """
        self._logger.debug("HTTP GET %s params=%r headers=%r", url, params, headers)
        try:
            response = self._session.get(
                url,
                params=params,
                headers=headers,
                timeout=self._timeout,
            )
            response.raise_for_status()
            self._logger.debug(
                "HTTP %s -> %d (%d bytes)",
                response.url,
                response.status_code,
                len(response.content),
            )
            return response.text
        except requests.RequestException as exc:
            self._logger.error("HTTP request failed for %s: %s", url, exc)
            raise