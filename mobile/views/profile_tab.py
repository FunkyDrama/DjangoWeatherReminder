import asyncio

import flet as ft

from palette import (
    BORDER_COLOR,
    CARD_COLOR,
    ERROR_BG,
    ERROR_COLOR,
    PRIMARY,
    SUCCESS_BG,
    SUCCESS_COLOR,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING_COLOR,
)
from services.auth_session import AuthSession
from services.api_service import APIError, APIService


class ProfileTab:
    """
    Handles the creation and functionality of a Profile tab within an application.

    The `ProfileTab` class provides a user interface to manage profile settings,
    including email display, webhook URL configuration, and session management
    (sign-out functionality). It integrates with a provided page layout and API
    service to allow dynamic content updating and user interaction. This class
    also handles refresh actions via gesture-based interactions.

    :ivar page: The main page object where the profile tab will be rendered.
    :type page: ft.Page
    :ivar api: The API service object used to retrieve and interact with user data.
    :type api: APIService
    """

    def __init__(self, page: ft.Page, api: APIService) -> None:
        self.page = page
        self.api = api
        self._built = False
        self._root: ft.Control | None = None
        self._is_refreshing: bool = False
        self._last_scroll_px: float = 0.0
        self._pull_visual: float = 0.0

    def build(self) -> ft.Control:
        if self._built:
            return self._root  # type: ignore[return-value]
        self._built = True
        self._root = self._build_content()
        return self._root

    def _build_content(self) -> ft.Control:
        page, api = self.page, self.api  # noqa: F841
        user = api.current_user or {}

        self._webhook_field = ft.TextField(
            label="Webhook URL",
            hint_text="https://example.com/webhook",
            value=user.get("webhook_url", "") or "",
            prefix_icon=ft.Icons.LINK,
            keyboard_type=ft.KeyboardType.URL,
            border_color=BORDER_COLOR,
            focused_border_color=PRIMARY,
            border_radius=10,
            text_size=15,
            cursor_color=PRIMARY,
            autocorrect=False,
        )

        self._save_btn = ft.Button(
            content=ft.Text(
                "Save Changes",
                color=ft.Colors.WHITE,
                size=15,
                weight=ft.FontWeight.W_600,
            ),
            style=ft.ButtonStyle(
                bgcolor={"": PRIMARY, "disabled": "#9CA3AF"},
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding.symmetric(vertical=14),
                elevation=0,
            ),
            expand=True,
            on_click=self._handle_save,
        )

        self._feedback = ft.Container(
            content=ft.Text("", size=13),
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            visible=False,
        )

        has_webhook = bool(user.get("webhook_url"))
        self._webhook_warning = ft.Container(
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(
                        ft.Icons.WARNING_AMBER_OUTLINED, color=WARNING_COLOR, size=18
                    ),
                    ft.Text(
                        "Webhook URL not set — webhook notifications will fail.",
                        size=13,
                        color=WARNING_COLOR,
                        expand=True,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            bgcolor="#FFFBEB",
            border=ft.Border.all(1, "#FDE68A"),
            border_radius=10,
            padding=12,
            visible=not has_webhook,
        )

        self._header_ring = ft.ProgressRing(
            width=20, height=20, color=ft.Colors.WHITE, stroke_width=2.5, visible=False
        )

        self._pull_spacer = ft.Container(
            height=0,
            animate=ft.Animation(140, ft.AnimationCurve.EASE_OUT),
        )

        self._lv = ft.ListView(
            expand=True,
            padding=ft.Padding.all(20),
            spacing=16,
            on_scroll=self._on_list_scroll,
            controls=[
                self._pull_spacer,
                ft.Container(
                    bgcolor=CARD_COLOR,
                    border_radius=16,
                    shadow=ft.BoxShadow(
                        blur_radius=16,
                        color="#0000000D",
                        offset=ft.Offset(0, 3),
                    ),
                    padding=0,
                    content=ft.Column(
                        spacing=0,
                        controls=[
                            _info_row("Email", user.get("email", "—")),
                        ],
                    ),
                ),
                ft.Container(
                    bgcolor=CARD_COLOR,
                    border_radius=16,
                    shadow=ft.BoxShadow(
                        blur_radius=16,
                        color="#0000000D",
                        offset=ft.Offset(0, 3),
                    ),
                    padding=16,
                    content=ft.Column(
                        spacing=14,
                        controls=[
                            ft.Text(
                                "Webhook Settings",
                                size=15,
                                weight=ft.FontWeight.W_600,
                                color=TEXT_PRIMARY,
                            ),
                            self._webhook_warning,
                            self._webhook_field,
                            self._feedback,
                            ft.Row([self._save_btn]),
                        ],
                    ),
                ),
                ft.Row(
                    [
                        ft.OutlinedButton(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.Icons.LOGOUT, color=ERROR_COLOR, size=18
                                    ),
                                    ft.Text(
                                        "Sign Out",
                                        color=ERROR_COLOR,
                                        size=15,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=8,
                            ),
                            style=ft.ButtonStyle(
                                side=ft.BorderSide(color=ERROR_COLOR),
                                shape=ft.RoundedRectangleBorder(radius=10),
                                padding=ft.Padding.symmetric(vertical=14),
                            ),
                            expand=True,
                            on_click=self._handle_logout,
                        )
                    ]
                ),
            ],
        )

        root = ft.Column(
            expand=True,
            spacing=0,
            controls=[
                ft.Container(
                    bgcolor=PRIMARY,
                    padding=ft.Padding.only(left=20, right=20, top=48, bottom=16),
                    content=ft.Row(
                        spacing=4,
                        controls=[
                            ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=24),
                            ft.Text(
                                "Profile",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                                expand=True,
                            ),
                            self._header_ring,
                        ],
                    ),
                ),
                ft.GestureDetector(
                    content=self._lv,
                    on_vertical_drag_update=self._on_drag_update,
                    on_vertical_drag_end=self._on_drag_end,
                    expand=True,
                ),
            ],
        )
        return root

    def _start_refresh(self) -> None:
        if self._is_refreshing:
            return
        self._is_refreshing = True
        self._header_ring.visible = True
        self.page.update()
        self.page.run_task(self._do_refresh)

    def _on_drag_update(self, e) -> None:
        if self._is_refreshing:
            return
        delta = getattr(e, "primary_delta", None) or 0
        at_top = self._last_scroll_px <= 1
        if at_top and delta > 0:
            self._pull_visual = min(56.0, self._pull_visual + (delta * 0.55))
            self._pull_spacer.height = self._pull_visual
            self.page.update()
        elif self._pull_visual > 0:
            self._pull_visual = 0.0
            self._pull_spacer.height = 0
            self.page.update()

    def _on_list_scroll(self, e) -> None:
        if self._is_refreshing:
            return
        pixels = getattr(e, "pixels", None)
        if pixels is None:
            return
        if pixels < -8 and self._last_scroll_px >= 0:
            self._last_scroll_px = pixels
            self._start_refresh()
            return
        self._last_scroll_px = pixels

    def _on_drag_end(self, e) -> None:
        if self._is_refreshing:
            return
        if self._pull_visual > 0:
            self._pull_visual = 0.0
            self._pull_spacer.height = 0
        vel = getattr(e, "primary_velocity", None)
        at_top = self._last_scroll_px <= 1
        if at_top and (vel is None or vel > 50):
            self._start_refresh()

    async def _do_refresh(self) -> None:
        try:
            await self._refresh_user()
        finally:
            self._header_ring.visible = False
            self._is_refreshing = False
            self._last_scroll_px = 0.0
            self._pull_visual = 0.0
            self._pull_spacer.height = 0
            self.page.update()

    async def _refresh_user(self) -> None:
        try:
            user = await asyncio.to_thread(self.api.get_me)
            self.api.current_user = user
            self._webhook_field.value = user.get("webhook_url", "") or ""
            self._webhook_warning.visible = not bool(user.get("webhook_url"))
            self._feedback.visible = False
            self.page.update()
        except Exception:
            pass

    async def _handle_save(self, e) -> None:
        webhook_url = self._webhook_field.value.strip()
        self._feedback.visible = False
        self._save_btn.disabled = True
        self.page.update()

        try:
            updated = await asyncio.to_thread(self.api.update_me, webhook_url)
            self.api.current_user = updated

            has_webhook = bool(updated.get("webhook_url"))
            self._webhook_warning.visible = not has_webhook

            self._feedback.bgcolor = SUCCESS_BG
            self._feedback.content = ft.Text(
                "Profile updated successfully.", color=SUCCESS_COLOR, size=13
            )
            self._feedback.visible = True
        except APIError as ex:
            self._feedback.bgcolor = ERROR_BG
            self._feedback.content = ft.Text(ex.message, color=ERROR_COLOR, size=13)
            self._feedback.visible = True
        except Exception:
            self._feedback.bgcolor = ERROR_BG
            self._feedback.content = ft.Text(
                "Failed to save. Please try again.", color=ERROR_COLOR, size=13
            )
            self._feedback.visible = True
        finally:
            self._save_btn.disabled = False
            self.page.update()

    async def _handle_logout(self, e) -> None:
        auth_session: AuthSession = self.page.auth_session
        self._built = False
        await auth_session.logout_and_redirect("/login")


def _info_row(label: str, value: str) -> ft.Container:
    """
    Creates a container with styled text rows for displaying a label and its associated value.

    :param label: The textual label to be displayed as the first row of the container.
    :type label: str
    :param value: The textual value to be displayed as the second row of the container.
    :type value: str
    :return: A styled container element consisting of two distinct rows for the label
        and value, respectively.
    :rtype: ft.Container
    """
    return ft.Container(
        padding=ft.Padding.only(left=16, right=16, top=14, bottom=14),
        content=ft.Column(
            spacing=2,
            controls=[
                ft.Text(label, size=12, color=TEXT_SECONDARY),
                ft.Text(value, size=16, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ],
        ),
    )
