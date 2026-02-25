import asyncio
from datetime import datetime

import flet as ft

from palette import (
    BG_COLOR,
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
from services.auth_session import AuthSession
from services.api_service import APIError, APIService, TokenExpiredError


def _format_dt(dt_str: str | None) -> str:
    """
    Formats an ISO 8601 datetime string into a user-friendly format or provides a
    default placeholder if input is invalid or not provided.

    :param dt_str: ISO 8601 formatted datetime string. Accepts None to indicate
        absence of a value.
    :type dt_str: str | None
    :return: Formatted datetime string in the format "DD Mon YYYY, HH:MM" or "—" if
        the input is None. If parsing fails, the first 16 characters of the input string
        are returned.
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
    Determines if the given status indicates a successful operation.

    This function checks whether the input status is equal to "sent"
    (case-insensitive). It is typically used to validate the status value
    and confirm if the desired operation has been completed successfully.

    :param status: The status string to evaluate.
    :type status: str
    :return: True if the status is equal to "sent" (case-insensitive),
        otherwise False.
    :rtype: bool
    """
    return status.lower() == "sent"


class LogsTab:
    """
    Handles the display and management of the logs tab within the application.

    The class is responsible for building a user interface to display notification logs, handling interactions such
    as pull-to-refresh, and fetching and rendering notification log data from an external API. It dynamically
    constructs the UI using various components based on the state of the logs (e.g., loading, error, empty state, or
    populated logs).

    :ivar page: Reference to the main application page.
    :type page: ft.Page
    :ivar api: Service instance used to fetch logs and metadata from an external API.
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
        self._pull_distance = 0.0

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
            padding=ft.padding.symmetric(vertical=40),
            visible=True,
        )
        self._error_text = ft.Text("", color=ERROR_COLOR, size=13, visible=False)
        self._pull_hint = ft.Container(
            content=ft.Text("Pull down to refresh", size=12, color=TEXT_SECONDARY),
            padding=ft.padding.only(bottom=8),
            visible=False,
        )
        self._log_list = ft.Column(spacing=10, visible=False)
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
            padding=ft.padding.symmetric(vertical=48),
            visible=False,
        )

        root = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            controls=[
                ft.Container(
                    bgcolor=PRIMARY,
                    padding=ft.padding.only(left=20, right=20, top=48, bottom=16),
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
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    expand=True,
                    bgcolor=BG_COLOR,
                    padding=ft.padding.all(20),
                    content=ft.Column(
                        spacing=12,
                        controls=[
                            self._pull_hint,
                            self._error_text,
                            self._loading,
                            self._log_list,
                            self._empty_view,
                        ],
                    ),
                ),
            ],
        )

        root = ft.GestureDetector(
            on_vertical_drag_start=self._on_vertical_drag_start,
            on_vertical_drag_update=self._on_vertical_drag_update,
            on_vertical_drag_end=self._on_vertical_drag_end,
            content=root,
        )

        self.page.run_task(self._load_logs)
        return root

    async def _load_logs(self) -> None:
        self._pull_hint.visible = False
        self._loading.visible = True
        self._log_list.visible = False
        self._empty_view.visible = False
        self._error_text.visible = False
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
            logs = await asyncio.to_thread(self.api.get_logs)
            self._render_logs(logs)
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

    def _render_logs(self, logs: list[dict]) -> None:
        if not logs:
            self._empty_view.visible = True
            self._log_list.visible = False
            return
        logs = sorted(
            logs,
            key=lambda e: (str(e.get("sent_at") or ""), int(e.get("id") or 0)),
            reverse=True,
        )
        self._log_list.controls.clear()
        for entry in logs:
            self._log_list.controls.append(self._build_log_card(entry))
        self._log_list.visible = True
        self._empty_view.visible = False

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
            padding=ft.padding.symmetric(horizontal=10, vertical=3),
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

    def _on_vertical_drag_start(self, e) -> None:
        self._pull_distance = 0.0

    def _on_vertical_drag_update(self, e) -> None:
        if self._loading.visible:
            return
        delta = float(e.primary_delta or 0.0)
        self._pull_distance = max(0.0, self._pull_distance + delta)

        if self._pull_distance > 6:
            if self._pull_distance >= 90:
                self._pull_hint.content.value = "Release to refresh"
            else:
                self._pull_hint.content.value = "Pull down to refresh"
            self._pull_hint.visible = True
            self.page.update()

    def _on_vertical_drag_end(self, e) -> None:
        should_refresh = self._pull_distance >= 90 and not self._loading.visible
        self._pull_distance = 0.0
        self._pull_hint.visible = False
        self.page.update()
        if should_refresh:
            self.page.run_task(self._load_logs)
