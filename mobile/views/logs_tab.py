import asyncio
from datetime import datetime
from math import ceil
from time import monotonic

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
_SHIFT_COOLDOWN = 0.45  # min seconds between consecutive window shifts
_NEAR_EDGE_PX = 180  # scroll trigger distance for short lists
_MIN_MOVE_PX = 6  # min scroll delta to count as directional movement
_TRIGGER_TOP = 0.25  # shift up when in top 25 % of scroll range
_TRIGGER_BOTTOM = 0.65  # shift down when past 65 % of scroll range

_LOCAL_TZ = datetime.now().astimezone().tzinfo


def _format_dt(dt_str: str | None) -> str:
    """
    Formats a given datetime string into a readable format based on the local timezone.

    If the input datetime string is `None` or invalid, the function will return a default
    placeholder string. If the input datetime string is valid, it is converted from its
    ISO 8601 format to the local timezone and formatted as "dd.mm.yyyy HH:MM". Any
    exceptions encountered during processing will result in returning a truncated version
    of the original input.

    :param dt_str: A string representing a datetime in ISO 8601 format or None.
    :type dt_str: str | None
    :return: A formatted datetime string in "dd.mm.yyyy HH:MM" format or a fallback string
        for invalid or None inputs.
    :rtype: str
    """
    if not dt_str:
        return "—"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.astimezone(_LOCAL_TZ).strftime("%d.%m.%Y %H:%M")
    except Exception:
        return dt_str[:16]


def _is_success(status: str) -> bool:
    """
    Determines if the given status indicates a successful operation.

    This function evaluates whether a provided status string corresponds to
    a successful state. Specifically, it checks if the status is 'sent',
    case-insensitively.

    :param status: A string representing the operation's status.
    :type status: str

    :return: True if the status is "sent", otherwise False.
    :rtype: bool
    """
    return status.lower() == "sent"


class LogsTab:
    """
    Represents a tab for displaying notification logs in a user interface.

    This class is responsible for building and managing the visual elements
    necessary for rendering and interacting with notification logs. It provides
    features to dynamically fetch, display, and paginate through notifications
    retrieved from an API.

    :ivar page: The main page instance where this tab is rendered.
    :type page: ft.Page
    :ivar api: The API service instance used to fetch notification data.
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
        self._has_more = False
        self._loading_more = False
        self._pages: dict[int, list[dict]] = {}
        self._start_page = 0
        self._total_pages = 0
        self._paging_busy = False
        self._prefetching: set[int] = set()
        self._last_shift_at = 0.0

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
        self._more_loading = ft.Container(
            content=ft.Row(
                [ft.ProgressRing(width=22, height=22, color=PRIMARY, stroke_width=2.5)],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(vertical=10),
            visible=False,
        )
        self._top_loading = ft.Container(
            content=ft.Row(
                [ft.ProgressRing(width=20, height=20, color=PRIMARY, stroke_width=2.5)],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(vertical=8),
            visible=False,
        )
        self._pull_spacer = ft.Container(
            height=0,
            animate=ft.Animation(140, ft.AnimationCurve.EASE_OUT),
        )

        self._lv = ft.ListView(
            expand=True,
            build_controls_on_demand=True,
            padding=ft.Padding.all(20),
            spacing=10,
            on_scroll=self._on_list_scroll,
            controls=[
                self._pull_spacer,
                self._error_text,
                self._loading,
                self._empty_view,
                self._more_loading,
            ],
        )

        self._lv_wrapper = ft.Container(
            content=self._lv,
            animate_opacity=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
            opacity=1.0,
            expand=True,
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
                    content=self._lv_wrapper,
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
        self._pages = {}
        self._start_page = 0
        self._total_pages = 0
        self._has_more = False
        self._paging_busy = False
        self._prefetching.clear()
        self._last_shift_at = 0.0
        self._render_window()
        if show_inner:
            self._loading.visible = True
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
            await self._fetch_page(0)
            self._render_window()
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

    def _store_page(self, result: dict, page_num: int) -> None:
        logs = result.get("results", [])
        total = result.get("count", len(logs))

        if total == 0:
            self._empty_view.visible = True
            self._total_pages = 0
            self._has_more = False
            self._pages = {}
            return

        self._empty_view.visible = False
        self._total_pages = max(1, ceil(total / _PAGE_SIZE))
        self._pages[page_num] = logs
        self._has_more = max(self._pages) < self._total_pages - 1

    def _render_window(self) -> None:
        cards = [
            self._build_log_card(entry)
            for entry in self._pages.get(self._start_page, [])
        ]
        self._lv.controls = [
            self._pull_spacer,
            self._error_text,
            self._loading,
            self._empty_view,
            self._top_loading,
            *cards,
            self._more_loading,
        ]

    async def _fetch_page(self, page_num: int) -> None:
        if page_num < 0:
            return
        if self._total_pages and page_num >= self._total_pages:
            return
        if page_num in self._pages:
            return
        result = await asyncio.to_thread(
            self.api.get_logs, _PAGE_SIZE, page_num * _PAGE_SIZE
        )
        self._store_page(result, page_num)

    async def _prefetch_page(self, page_num: int) -> None:
        if page_num < 0 or page_num in self._prefetching or page_num in self._pages:
            return
        if self._total_pages and page_num >= self._total_pages:
            return
        self._prefetching.add(page_num)
        try:
            await self._fetch_page(page_num)
        except Exception:
            pass
        finally:
            self._prefetching.discard(page_num)

    async def _shift_window_down(self) -> None:
        if self._paging_busy or self._is_refreshing:
            return
        if self._start_page >= self._total_pages - 1:
            return
        self._paging_busy = True
        self._loading_more = True
        next_page = self._start_page + 1
        try:
            self._more_loading.visible = True
            self.page.update()
            await self._fetch_page(next_page)
            self._more_loading.visible = False
            self._lv_wrapper.opacity = 0.0
            self.page.update()
            await asyncio.sleep(0.12)
            self._start_page = next_page
            self._render_window()
            self._lv_wrapper.opacity = 1.0
            self.page.update()
            self.page.run_task(self._prefetch_page, next_page + 1)
        except TokenExpiredError:
            await self._handle_token_expired()
        except Exception:
            pass
        finally:
            self._paging_busy = False
            self._loading_more = False
            self._more_loading.visible = False
            self._lv_wrapper.opacity = 1.0
            self.page.update()

    async def _shift_window_up(self) -> None:
        if self._paging_busy or self._is_refreshing:
            return
        if self._start_page <= 0:
            return
        self._paging_busy = True
        prev_page = self._start_page - 1
        try:
            self._top_loading.visible = True
            self.page.update()
            await self._fetch_page(prev_page)
            self._top_loading.visible = False
            self._lv_wrapper.opacity = 0.0
            self.page.update()
            await asyncio.sleep(0.12)
            self._start_page = prev_page
            self._render_window()
            self._lv_wrapper.opacity = 1.0
            self.page.update()
            self.page.run_task(self._prefetch_page, prev_page - 1)
        except TokenExpiredError:
            await self._handle_token_expired()
        except Exception:
            pass
        finally:
            self._top_loading.visible = False
            self._paging_busy = False
            self._lv_wrapper.opacity = 1.0
            self.page.update()

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
        if self._is_refreshing or self._start_page > 0:
            return
        delta = getattr(e, "primary_delta", None) or 0
        at_top = self._last_scroll_px <= 1
        if at_top and delta > 0:
            self._pull_visual = min(56.0, self._pull_visual + delta * 0.55)
            self._pull_spacer.height = self._pull_visual
            self.page.update()
        elif self._pull_visual > 0:
            self._pull_visual = 0.0
            self._pull_spacer.height = 0
            self.page.update()

    def _on_drag_end(self, e) -> None:
        if self._is_refreshing:
            return
        if self._start_page > 0:
            self._pull_visual = 0.0
            self._pull_spacer.height = 0
            return
        was_pulled = self._pull_visual > 15
        if self._pull_visual > 0:
            self._pull_visual = 0.0
            self._pull_spacer.height = 0
            self.page.update()
        if was_pulled:
            self._start_refresh()

    def _on_list_scroll(self, e) -> None:
        pixels = getattr(e, "pixels", None)
        if pixels is None:
            return
        prev = self._last_scroll_px

        if not self._is_refreshing:
            if self._start_page == 0 and pixels < -8 and prev >= 0:
                self._last_scroll_px = pixels
                self._start_refresh()
                return
            self._last_scroll_px = pixels

        if self._is_refreshing or self._loading_more or self._paging_busy:
            return

        max_extent = getattr(e, "max_scroll_extent", None)
        top_trigger = _NEAR_EDGE_PX
        bottom_trigger = None
        if max_extent is not None and max_extent > 0:
            if max_extent > _NEAR_EDGE_PX * 2:
                top_trigger = max_extent * _TRIGGER_TOP
                bottom_trigger = max_extent * _TRIGGER_BOTTOM
            else:
                bottom_trigger = max_extent - _NEAR_EDGE_PX

        movement = pixels - prev
        now = monotonic()
        in_cooldown = now - self._last_shift_at < _SHIFT_COOLDOWN

        if (
            pixels <= top_trigger
            and self._start_page > 0
            and movement < -_MIN_MOVE_PX
            and not in_cooldown
        ):
            self._last_shift_at = now
            self.page.run_task(self._shift_window_up)
            return

        can_shift_down = (
            self._total_pages > 0 and self._start_page < self._total_pages - 1
        )
        if (
            bottom_trigger is not None
            and max_extent is not None
            and max_extent > 0
            and pixels >= bottom_trigger
            and can_shift_down
            and movement > _MIN_MOVE_PX
            and not in_cooldown
        ):
            self._last_shift_at = now
            self.page.run_task(self._shift_window_down)

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
