from typing import Any

import requests

from config import API_BASE_URL


class APIError(Exception):
    """
    Represents an error specific to API operations.

    This exception is used to encapsulate API-related errors, allowing for
    the propagation of both an error message and an optional HTTP status
    code associated with the failure.

    :ivar message: The error message describing the API error.
    :type message: str
    :ivar status_code: The HTTP status code related to the error, if available.
    :type status_code: int | None
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TokenExpiredError(APIError):
    """
    Represents an error that is raised when a user's session has expired.

    This error indicates that the user's session is no longer valid, and they
    need to log in again to regain access. It extends the functionality of the
    APIError class and provides a specific error message and HTTP status code.
    """

    def __init__(self) -> None:
        super().__init__("Session expired. Please log in again.", 401)


class APIService:
    """
    Handles interactions with a RESTful API service.

    Provides methods to manage authentication, retrieve user data, interact with weather
    services, manage subscriptions, and fetch logs. This class is designed to facilitate
    communication with a backend server while handling errors and refreshing tokens
    automatically when necessary.

    :ivar access_token: The token used for authenticated requests. Set after login or
        during token refresh.
    :type access_token: str | None
    :ivar refresh_token: The token used for generating a new access token when the
        current one expires.
    :type refresh_token: str | None
    :ivar current_user: Information about the currently logged-in user.
    :type current_user: dict | None
    """

    def __init__(self) -> None:
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.current_user: dict | None = None
        self._subscription_metadata: dict | None = None

    @property
    def _auth_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        retry: bool = True,
        **kwargs: Any,
    ) -> requests.Response:
        url = f"{API_BASE_URL}{path}"
        try:
            resp = requests.request(
                method, url, headers=self._auth_headers, timeout=15, **kwargs
            )
        except requests.exceptions.ConnectionError:
            raise APIError("Connection failed. Check your internet connection.")
        except requests.exceptions.Timeout:
            raise APIError("Request timed out. Please try again.")

        if resp.status_code == 401 and retry and self.refresh_token:
            try:
                self.access_token = self._do_refresh()
                return self._request(method, path, retry=False, **kwargs)
            except Exception:
                self.access_token = None
                self.refresh_token = None
                raise TokenExpiredError()

        if not resp.ok:
            raise APIError(self._extract_error(resp), resp.status_code)

        return resp

    @staticmethod
    def _do_refresh_with_token(refresh_token: str) -> str:
        resp = requests.post(
            f"{API_BASE_URL}/auth/token/refresh/",
            json={"refresh": refresh_token},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["access"]

    def _do_refresh(self) -> str:
        return self._do_refresh_with_token(self.refresh_token)  # type: ignore[arg-type]

    @staticmethod
    def _extract_error(resp: requests.Response) -> str:
        try:
            data = resp.json()
            if isinstance(data, dict):
                if "detail" in data:
                    return str(data["detail"])
                if "non_field_errors" in data:
                    errs = data["non_field_errors"]
                    return errs[0] if errs else "Unknown error"
                parts: list[str] = []
                for key, val in data.items():
                    if isinstance(val, list):
                        parts.append(f"{key}: {', '.join(str(v) for v in val)}")
                    else:
                        parts.append(f"{key}: {val}")
                return "; ".join(parts) or f"Error {resp.status_code}"
            return str(data)
        except Exception:
            return f"Request failed ({resp.status_code})"

    def login(self, email: str, password: str) -> dict:
        resp = self._request(
            "POST", "/auth/login/", json={"email": email, "password": password}
        )
        return resp.json()

    def register(self, email: str, password: str) -> dict:
        resp = self._request(
            "POST",
            "/auth/register/",
            json={"email": email, "password": password},
        )
        return resp.json()

    def get_me(self) -> dict:
        return self._request("GET", "/auth/me/").json()

    def update_me(self, webhook_url: str) -> dict:
        return self._request(
            "PATCH", "/auth/me/", json={"webhook_url": webhook_url}
        ).json()

    def get_weather(
        self,
        city: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> dict:
        params: dict = {}
        if city:
            params["city"] = city
        elif lat is not None and lon is not None:
            params["lat"] = lat
            params["lon"] = lon
        return self._request("GET", "/weather/", params=params).json()

    def search_cities(self, query: str) -> list[dict]:
        if len(query.strip()) < 2:
            return []
        return self._request("GET", "/weather/cities/", params={"q": query}).json()

    def get_subscription_options(self) -> dict:
        """Backward-compatible helper for OPTIONS parsing."""
        try:
            resp = self._request("OPTIONS", "/subscriptions/")
            post_fields = resp.json().get("actions", {}).get("POST", {})
            intervals = [
                (str(c["value"]), c["display_name"])
                for c in post_fields.get("interval_hours", {}).get("choices", [])
            ]
            notif_types = [
                c["value"]
                for c in post_fields.get("notification_type", {}).get("choices", [])
            ]
            return {"intervals": intervals, "notification_types": notif_types}
        except Exception:
            return {}

    def get_subscription_metadata(self, *, force_refresh: bool = False) -> dict:
        """Return UI metadata for mobile based on existing DRF OPTIONS data."""
        if self._subscription_metadata is not None and not force_refresh:
            return self._subscription_metadata

        fallback = {
            "intervals": [
                ("1", "Every 1 hour"),
                ("3", "Every 3 hours"),
                ("6", "Every 6 hours"),
                ("12", "Every 12 hours"),
            ],
            "notification_types": [
                {"value": "email", "label": "Email", "icon": "EMAIL_OUTLINED"},
                {"value": "webhook", "label": "Webhook", "icon": "LINK"},
            ],
        }

        options = self.get_subscription_options()
        if options.get("intervals") and options.get("notification_types"):
            fallback = {
                "intervals": options["intervals"],
                "notification_types": [
                    {
                        "value": value,
                        "label": value.capitalize(),
                        "icon": "EMAIL_OUTLINED" if value == "email" else "LINK",
                    }
                    for value in options["notification_types"]
                ],
            }

        self._subscription_metadata = fallback
        return fallback

    def get_subscriptions(self) -> list[dict]:
        data = self._request("GET", "/subscriptions/").json()
        return data.get("results", data) if isinstance(data, dict) else data

    def create_subscription(
        self, city_name: str, interval_hours: int, notification_type: str
    ) -> dict:
        return self._request(
            "POST",
            "/subscriptions/",
            json={
                "city": {"name": city_name},
                "interval_hours": interval_hours,
                "notification_type": notification_type,
            },
        ).json()

    def update_subscription(
        self,
        sub_id: int,
        city_name: str,
        interval_hours: int,
        notification_type: str,
    ) -> dict:
        return self._request(
            "PUT",
            f"/subscriptions/{sub_id}/",
            json={
                "city": {"name": city_name},
                "interval_hours": interval_hours,
                "notification_type": notification_type,
            },
        ).json()

    def delete_subscription(self, sub_id: int) -> None:
        self._request("DELETE", f"/subscriptions/{sub_id}/")

    def get_logs(self, limit: int = 10, offset: int = 0) -> dict:
        data = self._request(
            "GET", "/notifications/logs/", params={"limit": limit, "offset": offset}
        ).json()
        if isinstance(data, dict) and "results" in data:
            return data
        return {"count": len(data), "results": data}

    def logout(self) -> None:
        self.access_token = None
        self.refresh_token = None
        self.current_user = None
        self._subscription_metadata = None
