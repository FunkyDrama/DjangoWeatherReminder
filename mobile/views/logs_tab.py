import asyncio
from datetime import datetime

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
)
from services.api_service import APIError, APIService, TokenExpiredError
from services.auth_session import AuthSession

_PAGE_SIZE = 10


def _format_dt(dt_str: str | None) -> str:
    """
    Formats a datetime string into a readable format. If the input is None or invalid, it returns
    either a placeholder or a truncated version of the original string. The function handles ISO
    8601 datetime strings and converts them to the format "DD Mon YYYY, HH:MM".

    :param dt_str: A string representing a datetime in ISO 8601 format or None.
    :type dt_str: str | None
    :return: A string representing the formatted datetime or a fallback value if the input is
        None or invalid.
    :rtype: str
    """
    if not dt_str:
        return "—"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y, %H:%M")
    except Exception:
        return dt_str[:16]


def _is_success(status: str) -> bool:
    """
    Determines if the provided status indicates a successful operation.

    This function checks whether the given status string represents a
    successful state by comparing it (case-insensitively) to the term "sent".

    :param status: The status to evaluate.
    :type status: str
    :return: True if the status is "sent" (case-insensitive), otherwise False.
    :rtype: bool
    """
    return status.lower() == "sent"


class LogsTab:
    """
    Manages the display, interaction, and functionality of the Notification Logs tab
    in the application.

    The LogsTab class handles building the user interface elements required to
    display notification logs, managing the asynchronous loading of logs from the
    API, and displaying relevant status messages (e.g., errors or empty state).

    :ivar page: The application page reference to build and manage the UI.
    :type page: ft.Page
    :ivar api: The API service instance used to fetch notifications and metadata.
    :type api: APIService
    """

    def __init__(self, page: ft.Page, api: APIService) -> None:
        self.page = page
        self.api = api
        self._built = False
        self._root: ft.Control | None = None
        self._notif_types = {
            "email": {"label": "Email", "icon": "EMAIL_OUTLINED"},
            "webhook": {"label": "Webhook", "icon": "LINK"},
        }
        self._is_refreshing = False
        self._last_scroll_px = 0.0
        self._pull_visual = 0.0
        self._offset = 0
        self._total_count = 0
        self._has_more = False
        self._loading_more = False

    def build(self) -> ft.Control:
        if self._built:
            return self._root  # type: ignore[return-value]
        self._built = True
        self._root = self._build_content()
        return self._root

    def _build_content(self) -> ft.Control:
        self._loading = ft.Container(
            content=ft.Row(
                [ft.ProgressRing(width=32, height=32, color=PRIMARY, stroke_width=3)],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(vertical=40),
            visible=True,
        )
        self._error_text = ft.Text("", color=ERROR_COLOR, size=13, visible=False)
        self._empty_view = ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.NOTIFICATIONS_NONE, size=64, color="#D1D5DB"),
                    ft.Container(height=12),
                    ft.Text("No notifications yet", color=TEXT_SECONDARY, size=16),
                    ft.Text(
                        "Your notification history will appear here",
                        color="#9CA3AF",
                        size=13,
                    ),
                ],
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.symmetric(vertical=48),
            visible=False,
        )

        self._log_list = ft.Column(spacing=10, controls=[])

        self._more_loading = ft.Container(
            content=ft.Row(
                [ft.ProgressRing(width=22, height=22, color=PRIMARY, stroke_width=2.5)],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(vertical=10),
            visible=False,
        )

        self._pull_spacer = ft.Container(
            height=0,
            animate=ft.Animation(140, ft.AnimationCurve.EASE_OUT),
        )

        self._lv = ft.ListView(
            expand=True,
            padding=ft.Padding.all(20),
            spacing=10,
            on_scroll=self._on_list_scroll,
            controls=[
                self._pull_spacer,
                self._error_text,
                self._loading,
                self._empty_view,
                self._log_list,
                self._more_loading,
            ],
        )

        self._header_ring = ft.ProgressRing(
            width=20, height=20, color=ft.Colors.WHITE, stroke_width=2.5, visible=False
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
                            ft.Icon(
                                ft.Icons.NOTIFICATIONS, color=ft.Colors.WHITE, size=24
                            ),
                            ft.Text(
                                "Notification Logs",
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

        self.page.run_task(self._load_logs)
        return root

    async def _load_logs(self, show_inner: bool = True) -> None:
        self._error_text.visible = False
        self._empty_view.visible = False
        if show_inner:
            self._loading.visible = True
            self._log_list.controls.clear()
            self._offset = 0
            self._total_count = 0
            self._has_more = False
        self.page.update()

        try:
            metadata = await asyncio.to_thread(self.api.get_subscription_metadata)
            self._notif_types = {
                str(item["value"]): {
                    "label": str(item.get("label", item["value"])),
                    "icon": str(item.get("icon", "NOTIFICATIONS_NONE")),
                }
                for item in metadata.get("notification_types", [])
                if "value" in item
            } or self._notif_types
            result = await asyncio.to_thread(self.api.get_logs, _PAGE_SIZE, 0)
            self._render_page(result, reset=True)
        except TokenExpiredError:
            await self._handle_token_expired()
        except APIError as ex:
            self._error_text.value = ex.message
            self._error_text.visible = True
        except Exception:
            self._error_text.value = "Failed to load logs."
            self._error_text.visible = True
        finally:
            self._loading.visible = False
            self.page.update()

    def _render_page(self, result: dict, *, reset: bool = False) -> None:
        logs = result.get("results", [])
        total = result.get("count", len(logs))

        if reset:
            self._log_list.controls.clear()
            self._offset = 0

        if not logs and reset:
            self._empty_view.visible = True
            self._total_count = 0
            self._has_more = False
            return

        self._empty_view.visible = False
        self._total_count = total

        for entry in logs:
            self._log_list.controls.append(self._build_log_card(entry))

        self._offset += len(logs)
        self._has_more = self._offset < total

    async def _load_more_async(self) -> None:
        try:
            self._more_loading.visible = True
            self.page.update()
            result = await asyncio.to_thread(
                self.api.get_logs, _PAGE_SIZE, self._offset
            )
            self._render_page(result, reset=False)
            self._more_loading.visible = False
            self.page.update()
        except TokenExpiredError:
            await self._handle_token_expired()
        except Exception:
            pass
        finally:
            self._loading_more = False

    def _build_log_card(self, entry: dict) -> ft.Container:
        status = entry.get("status", "")
        success = _is_success(status)
        notif_type = entry.get("notification_type", "")
        notif_meta = self._notif_types.get(
            notif_type,
            {"label": notif_type.capitalize(), "icon": "NOTIFICATIONS_NONE"},
        )

        status_badge = ft.Container(
            content=ft.Text(
                "✓ Sent" if success else "✗ Failed",
                size=11,
                weight=ft.FontWeight.W_600,
                color=SUCCESS_COLOR if success else ERROR_COLOR,
            ),
            bgcolor=SUCCESS_BG if success else ERROR_BG,
            border_radius=20,
            padding=ft.Padding.symmetric(horizontal=10, vertical=3),
        )

        return ft.Container(
            bgcolor=CARD_COLOR,
            border_radius=14,
            padding=16,
            shadow=ft.BoxShadow(
                blur_radius=12, color="#0000000D", offset=ft.Offset(0, 2)
            ),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                entry.get("city", "Unknown"),
                                size=16,
                                weight=ft.FontWeight.W_600,
                                color=TEXT_PRIMARY,
                                expand=True,
                            ),
                            status_badge,
                        ],
                    ),
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.Row(
                                spacing=4,
                                controls=[
                                    ft.Icon(
                                        getattr(
                                            ft.Icons,
                                            str(notif_meta["icon"]),
                                            ft.Icons.NOTIFICATIONS_NONE,
                                        ),
                                        size=16,
                                        color=TEXT_SECONDARY,
                                    ),
                                    ft.Text(
                                        str(notif_meta["label"]),
                                        size=13,
                                        color=TEXT_SECONDARY,
                                    ),
                                ],
                            ),
                            ft.Container(width=1, height=12, bgcolor=BORDER_COLOR),
                            ft.Text(
                                _format_dt(entry.get("sent_at")),
                                size=13,
                                color=TEXT_SECONDARY,
                            ),
                        ],
                    ),
                ],
            ),
        )

    async def _handle_token_expired(self) -> None:
        auth_session: AuthSession = self.page.auth_session
        await auth_session.logout_and_redirect("/login")

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
        pixels = getattr(e, "pixels", None)
        if pixels is None:
            return

        if not self._is_refreshing:
            if pixels < -8 and self._last_scroll_px >= 0:
                self._last_scroll_px = pixels
                self._start_refresh()
                return
            self._last_scroll_px = pixels

        if self._is_refreshing or self._loading_more or not self._has_more:
            return
        max_extent = getattr(e, "max_scroll_extent", None)
        if max_extent is not None and max_extent > 50 and pixels >= max_extent - 150:
            self._loading_more = True
            self.page.run_task(self._load_more_async)

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
            await self._load_logs(show_inner=False)
        finally:
            self._header_ring.visible = False
            self._is_refreshing = False
            self._last_scroll_px = 0.0
            self._pull_visual = 0.0
            self._pull_spacer.height = 0
            self.page.update()
