import asyncio

import flet as ft

from services.api_service import APIService
from services.session_storage import SessionStorage


class AuthSession:
    """
    Handles user authentication session management.

    This class facilitates managing the authentication session for a user,
    including restoring sessions from storage, establishing new sessions,
    and clearing sessions. It interacts with an API service for authentication
    and a session storage mechanism for maintaining tokens.

    :ivar page: The page object used for navigation and routing during session management.
    :type page: ft.Page
    :ivar api: The API service used for handling authentication and user information.
    :type api: APIService
    :ivar storage: The session storage used for saving and loading authentication tokens.
    :type storage: SessionStorage
    """

    def __init__(self, page: ft.Page, api: APIService, storage: SessionStorage) -> None:
        self.page = page
        self.api = api
        self.storage = storage

    async def restore(self) -> bool:
        access, refresh = await self.storage.load_tokens()
        if not access:
            return False

        self.api.access_token = access
        self.api.refresh_token = refresh
        try:
            self.api.current_user = await asyncio.to_thread(self.api.get_me)
            return True
        except Exception:
            await self.clear_local_session()
            return False

    async def establish(self, access: str, refresh: str) -> None:
        self.api.access_token = access
        self.api.refresh_token = refresh
        await self.storage.save_tokens(access, refresh)
        self.api.current_user = await asyncio.to_thread(self.api.get_me)

    async def clear_local_session(self) -> None:
        self.api.logout()
        await self.storage.clear_tokens()

    async def logout_and_redirect(self, route: str = "/login") -> None:
        await self.clear_local_session()
        await self.page.push_route(route)
