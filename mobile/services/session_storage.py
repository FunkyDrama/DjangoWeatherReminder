from typing import Optional

import flet as ft

try:
    import flet_secure_storage as fss
except Exception:  # pragma: no cover - optional dependency
    fss = None


class SessionStorage:
    """
    Handles token storage and retrieval with support for secure storage fallback.

    SessionStorage provides functionality to store, retrieve, and clear access and
    refresh tokens using secure storage if available, and shared preferences as a
    fallback. This class is designed to prioritize secure token management while
    offering flexibility to use alternative storage mechanisms where necessary.

    :ivar page: Reference to the page object, which is used to attach services
        like secure storage.
    :type page: ft.Page
    """

    ACCESS_KEY = "access_token"
    REFRESH_KEY = "refresh_token"

    def __init__(self, page: ft.Page, shared_prefs: ft.SharedPreferences) -> None:
        self.page = page
        self._sp = shared_prefs
        self._secure: Optional[object] = None

    async def init(self) -> None:
        """Try enabling secure storage; keep SharedPreferences as fallback."""
        if fss is None:
            return
        try:
            secure = fss.SecureStorage()
            self.page.services.append(secure)
            if hasattr(secure, "get_availability"):
                available = await secure.get_availability()
                if available is False:
                    return
            self._secure = secure
        except Exception:
            self._secure = None

    async def load_tokens(self) -> tuple[str | None, str | None]:
        access = await self._get(self.ACCESS_KEY)
        refresh = await self._get(self.REFRESH_KEY)
        return access, refresh

    async def save_tokens(self, access: str, refresh: str) -> None:
        await self._set(self.ACCESS_KEY, access)
        await self._set(self.REFRESH_KEY, refresh)

    async def clear_tokens(self) -> None:
        await self._remove(self.ACCESS_KEY)
        await self._remove(self.REFRESH_KEY)

    async def _get(self, key: str) -> str | None:
        if self._secure:
            try:
                value = await self._secure.get(key)
                if value is not None:
                    return value
            except Exception:
                pass

        return await self._sp.get(key)

    async def _set(self, key: str, value: str) -> None:
        wrote_secure = False
        if self._secure:
            try:
                await self._secure.set(key, value)
                wrote_secure = True
            except Exception:
                wrote_secure = False

        if wrote_secure:
            await self._sp.remove(key)
        else:
            await self._sp.set(key, value)

    async def _remove(self, key: str) -> None:
        if self._secure:
            try:
                await self._secure.remove(key)
            except Exception:
                pass
        await self._sp.remove(key)
