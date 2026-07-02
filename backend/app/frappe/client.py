import json
import time
from typing import Any

import httpx
import structlog

from app.core.exceptions import AuthenticationError, FrappeClientError, FrappeUnavailableError, PermissionDenied

logger = structlog.get_logger(__name__)


class FrappeClient:
    """Async HTTP client that preserves the authenticated Frappe user context."""

    def __init__(
        self,
        base_url: str,
        auth_mode: str = "token",
        api_key: str | None = None,
        api_secret: str | None = None,
        session_cookie_name: str = "sid",
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.auth_mode = auth_mode.lower()
        self.api_key = api_key
        self.api_secret = api_secret
        self.session_cookie_name = session_cookie_name
        self.timeout = httpx.Timeout(timeout, connect=min(timeout, 10.0))

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.auth_mode == "token":
            if not self.api_key or not self.api_secret:
                raise AuthenticationError("Frappe token credentials are not configured.")
            headers["Authorization"] = f"token {self.api_key}:{self.api_secret}"
        return headers

    @staticmethod
    def _normalize_path(path: str) -> str:
        return f"/{path.lstrip('/')}"

    def _request_cookies(self, cookies: dict | None) -> dict[str, str]:
        if self.auth_mode != "session":
            return {}
        value = (cookies or {}).get(self.session_cookie_name)
        return {self.session_cookie_name: value} if value else {}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json_body: dict | None = None,
        cookies: dict | None = None,
    ) -> dict[str, Any]:
        normalized_path = self._normalize_path(path)
        started = time.perf_counter()
        status_code: int | None = None
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._headers(),
                timeout=self.timeout,
            ) as client:
                response = await client.request(
                    method,
                    normalized_path,
                    params=params,
                    json=json_body,
                    cookies=self._request_cookies(cookies),
                )
                status_code = response.status_code
                payload = self._decode_response(response)
                if response.is_error:
                    self._raise_frappe_error(payload, response.status_code)
                self._raise_companion_error(payload)
                return payload
        except (AuthenticationError, PermissionDenied, FrappeClientError):
            raise
        except httpx.RequestError as exc:
            raise FrappeUnavailableError(
                "Unable to reach the Frappe server.",
                {"path": normalized_path},
            ) from exc
        finally:
            logger.info(
                "frappe_request",
                method=method,
                path=normalized_path,
                status=status_code,
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
                auth_mode=self.auth_mode,
            )

    @staticmethod
    def _decode_response(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise FrappeClientError(
                "Frappe returned a non-JSON response.",
                502,
                {"status": response.status_code},
            ) from exc
        if not isinstance(payload, dict):
            raise FrappeClientError("Frappe returned an invalid response.", 502)
        return payload

    @classmethod
    def _raise_companion_error(cls, payload: dict[str, Any]) -> None:
        if payload.get("exc") or payload.get("exception"):
            cls._raise_clean_error(cls._extract_error_message(payload), 500, {})
        companion = payload.get("message")
        if isinstance(companion, dict) and companion.get("success") is False:
            message = str(companion.get("message") or "Frappe rejected the request.")
            details = companion.get("details") if isinstance(companion.get("details"), dict) else {}
            cls._raise_clean_error(message, 400, details)

    @classmethod
    def _raise_frappe_error(cls, payload: dict[str, Any], status_code: int) -> None:
        message = cls._extract_error_message(payload)
        cls._raise_clean_error(message, status_code, {"frappeStatus": status_code})

    @staticmethod
    def _raise_clean_error(message: str, status_code: int, details: dict[str, Any]) -> None:
        lowered = message.lower()
        if status_code == 401 or "authentication" in lowered or "login required" in lowered or "not logged in" in lowered or "guest user" in lowered:
            raise AuthenticationError("Invalid or expired Frappe credentials.", details)
        if status_code == 403 or "permission" in lowered or "not allowed" in lowered or "not permitted" in lowered:
            logger.warning("frappe_permission_denied", message=message)
            raise PermissionDenied(message, details)
        if status_code == 404 or "does not exist" in lowered or "not found" in lowered:
            raise FrappeClientError(message, 404, details)
        if status_code >= 500:
            raise FrappeClientError("Frappe could not complete the request.", 502, details)
        raise FrappeClientError(message, 422 if status_code in {400, 409, 417, 422} else status_code, details)

    @staticmethod
    def _extract_error_message(payload: dict[str, Any]) -> str:
        server_messages = payload.get("_server_messages")
        if isinstance(server_messages, str):
            try:
                decoded = json.loads(server_messages)
                if isinstance(decoded, list) and decoded:
                    item = json.loads(decoded[0]) if isinstance(decoded[0], str) else decoded[0]
                    if isinstance(item, dict) and item.get("message"):
                        return str(item["message"])
            except (ValueError, TypeError):
                pass
        for key in ("message", "exception", "exc_type"):
            value = payload.get(key)
            if isinstance(value, str) and value and not value.lstrip().startswith("["):
                return value.splitlines()[0][:300]
        return "Frappe rejected the request."

    async def get(self, path: str, params: dict | None = None, cookies: dict | None = None) -> dict:
        return await self._request("GET", path, params=params, cookies=cookies)

    async def post(self, path: str, json: dict | None = None, cookies: dict | None = None) -> dict:
        return await self._request("POST", path, json_body=json, cookies=cookies)

    async def put(self, path: str, json: dict | None = None, cookies: dict | None = None) -> dict:
        return await self._request("PUT", path, json_body=json, cookies=cookies)

    async def delete(self, path: str, cookies: dict | None = None) -> dict:
        return await self._request("DELETE", path, cookies=cookies)
