import asyncio
import threading
from typing import Optional

import flet as ft
from services.api_service import APIError, APIService, TokenExpiredError
from services.auth_session import AuthSession
from views.dashboard_parts import (
    SubscriptionDialog,
    badge,
    card,
    city_suggestion_tile,
    resolve_icon,
    section_title,
)

from palette import (
    BG_COLOR,
    BORDER_COLOR,
    ERROR_BG,
    ERROR_COLOR,
    INFO_COLOR,
    PRIMARY,
    SUCCESS_COLOR,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class DashboardTab:
    """
    Represents the dashboard tab, providing UI components and logic
    for displaying weather information and user subscriptions.

    This class is responsible for rendering a weather card for city
    weather searches, handling user interactions, such as city search
    and subscriptions, and updating the UI state accordingly. It
    integrates with external services (e.g., APIService) to fetch
    required data dynamically.

    :ivar page: The application's main page to which controls are added.
    :type page: ft.Page
    :ivar api: Service used to interact with APIs for fetching data.
    :type api: APIService
    """

    def __init__(self, page: ft.Page, api: APIService) -> None:
        self.page = page
        self.api = api

        self._search_timer: Optional[threading.Timer] = None
        self._built = False
        self._root: Optional[ft.Control] = None

        self._weather_section: Optional[ft.Column] = None
        self._interval_options: list[tuple[str, str]] = []
        self._notif_types: list[dict] = []
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
        self._weather_card = ft.Container(visible=False)
        self._weather_loading = ft.Container(
            content=ft.Row(
                [ft.ProgressRing(width=28, height=28, color=PRIMARY, stroke_width=3)],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            visible=False,
            padding=ft.Padding.symmetric(vertical=12),
        )
        self._suggestions_col = ft.Column(visible=False, spacing=2)

        self._clear_btn = ft.IconButton(
            icon=ft.Icons.CLEAR,
            icon_size=18,
            icon_color=TEXT_SECONDARY,
            tooltip="Clear",
            visible=False,
            on_click=self._clear_city,
        )

        self._city_field = ft.TextField(
            hint_text="Search city…",
            prefix_icon=ft.Icons.SEARCH,
            suffix=self._clear_btn,
            border_color=BORDER_COLOR,
            focused_border_color=PRIMARY,
            border_radius=12,
            text_size=15,
            cursor_color=PRIMARY,
            expand=True,
            on_change=self._on_city_change,
            on_submit=self._on_city_submit,
        )

        self._weather_section = ft.Column(
            spacing=12,
            controls=[
                section_title("🌦  City Weather"),
                ft.Row(
                    controls=[
                        self._city_field,
                        ft.IconButton(
                            icon=ft.Icons.SEARCH,
                            icon_color=ft.Colors.WHITE,
                            bgcolor=PRIMARY,
                            on_click=self._on_city_submit,
                            tooltip="Search weather",
                        ),
                    ],
                    spacing=8,
                ),
                self._suggestions_col,
                self._weather_loading,
                self._weather_card,
            ],
        )

        self._sub_loading = ft.Container(
            content=ft.Row(
                [ft.ProgressRing(width=22, height=22, color=PRIMARY, stroke_width=2.5)],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            visible=False,
        )
        self._sub_list = ft.Column(spacing=10)
        self._sub_empty = ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(
                        ft.Icons.NOTIFICATIONS_OFF_OUTLINED, size=48, color="#D1D5DB"
                    ),
                    ft.Container(height=8),
                    ft.Text("No subscriptions yet", color=TEXT_SECONDARY, size=14),
                    ft.Text("Tap + to add one", color="#9CA3AF", size=12),
                ],
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.symmetric(vertical=24),
            visible=False,
        )
        self._sub_error = ft.Text("", color=ERROR_COLOR, size=13, visible=False)

        subs_section = ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    controls=[
                        section_title("🔔  My Subscriptions"),
                        ft.Container(expand=True),
                        ft.FloatingActionButton(
                            mini=True,
                            icon=ft.Icons.ADD,
                            bgcolor=PRIMARY,
                            foreground_color=ft.Colors.WHITE,
                            tooltip="Add subscription",
                            on_click=self._open_add_dialog,
                        ),
                    ],
                ),
                self._sub_error,
                self._sub_loading,
                self._sub_list,
                self._sub_empty,
            ],
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
            spacing=24,
            on_scroll=self._on_list_scroll,
            controls=[
                self._pull_spacer,
                self._weather_section,
                ft.Divider(color=BORDER_COLOR),
                subs_section,
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
                            ft.Image(src="icon.png", width=24, height=24),
                            ft.Text(
                                "Weather Reminder",
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

        self.page.run_task(self._load_subscriptions)
        return root

    def _on_city_change(self, e) -> None:
        query = e.control.value
        has_text = bool(query)
        self._clear_btn.visible = has_text

        if self._search_timer:
            self._search_timer.cancel()

        if len(query.strip()) < 2:
            self._suggestions_col.controls.clear()
            self._suggestions_col.visible = False
            self.page.update()
            return

        self._search_timer = threading.Timer(
            0.5,
            lambda: self.page.run_task(self._fetch_suggestions, query),
        )
        self._search_timer.start()

    def _clear_city(self, e) -> None:
        self._city_field.value = ""
        self._clear_btn.visible = False
        self._suggestions_col.controls.clear()
        self._suggestions_col.visible = False
        self._weather_loading.visible = False
        self._weather_card.visible = False
        self.page.update()

    async def _fetch_suggestions(self, query: str) -> None:
        try:
            cities = await asyncio.to_thread(self.api.search_cities, query)
        except Exception:
            return

        tiles = []
        for city in cities[:6]:
            label = city["name"]
            if city.get("state"):
                label += f", {city['state']}"
            label += f"  ({city['country']})"

            name = city["name"]

            def make_click(city_name=name):
                def on_click(e):
                    self._city_field.value = city_name
                    self._clear_btn.visible = True
                    self._suggestions_col.controls.clear()
                    self._suggestions_col.visible = False
                    self.page.update()
                    self.page.run_task(self._load_weather, city_name)

                return on_click

            tiles.append(city_suggestion_tile(label, make_click()))

        self._suggestions_col.controls = tiles
        self._suggestions_col.visible = bool(tiles)
        self.page.update()

    def _on_city_submit(self, e) -> None:
        city = self._city_field.value.strip()
        if not city:
            return
        self._suggestions_col.controls.clear()
        self._suggestions_col.visible = False
        self.page.update()
        self.page.run_task(self._load_weather, city)

    async def _load_weather(self, city: str) -> None:
        self._weather_loading.visible = True
        self._weather_card.visible = False
        self.page.update()

        try:
            data = await asyncio.to_thread(self.api.get_weather, city)
            new_card = self._build_weather_card(data)
            new_card.visible = True

            ws = self._weather_section
            ws.controls[3] = self._weather_loading
            ws.controls[4] = new_card
            self._weather_card = new_card
        except TokenExpiredError:
            await self._handle_token_expired()
        except APIError as ex:
            err = ft.Container(
                content=ft.Text(ex.message, color=ERROR_COLOR, size=13),
                bgcolor=ERROR_BG,
                border_radius=10,
                padding=12,
                visible=True,
            )
            ws = self._weather_section
            ws.controls[4] = err
            self._weather_card = err
        except Exception:
            pass
        finally:
            self._weather_loading.visible = False
            self.page.update()

    def _build_weather_card(self, data: dict) -> ft.Container:
        icon_code = str(data.get("icon", "01d"))

        def metric(icon, label: str, value: str, color: str) -> ft.Container:
            return ft.Container(
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    controls=[
                        ft.Icon(icon, color=color, size=22),
                        ft.Text(
                            value,
                            size=15,
                            weight=ft.FontWeight.W_600,
                            color=TEXT_PRIMARY,
                        ),
                        ft.Text(label, size=11, color=TEXT_SECONDARY),
                    ],
                ),
                bgcolor=BG_COLOR,
                border_radius=12,
                padding=12,
                expand=True,
            )

        return card(
            ft.Column(
                spacing=16,
                controls=[
                    ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Image(
                                src=f"https://openweathermap.org/img/wn/{icon_code}@2x.png",
                                width=64,
                                height=64,
                            ),
                            ft.Container(width=12),
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        data.get("city", ""),
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        color=TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        data.get("description", "").capitalize(),
                                        size=14,
                                        color=TEXT_SECONDARY,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        f"{data.get('temperature', '?')}°C",
                                        size=40,
                                        weight=ft.FontWeight.BOLD,
                                        color=PRIMARY,
                                    ),
                                    ft.Text(
                                        f"Feels like {data.get('feels_like', '?')}°C",
                                        size=13,
                                        color=TEXT_SECONDARY,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=8,
                        controls=[
                            metric(
                                ft.Icons.WATER_DROP,
                                "Humidity",
                                f"{data.get('humidity', '?')}%",
                                "#3B82F6",
                            ),
                            metric(
                                ft.Icons.AIR,
                                "Wind",
                                f"{data.get('wind_speed', '?')} m/s",
                                "#06B6D4",
                            ),
                        ],
                    ),
                ],
            ),
            padding=20,
        )

    async def _load_subscriptions(self, show_inner: bool = True) -> None:
        if show_inner:
            self._sub_loading.visible = True
        self._sub_error.visible = False
        self.page.update()
        try:
            metadata = await asyncio.to_thread(self.api.get_subscription_metadata)
            self._interval_options = metadata.get("intervals", self._interval_options)
            self._notif_types = metadata.get("notification_types", self._notif_types)
            subs = await asyncio.to_thread(self.api.get_subscriptions)
            self._render_subscriptions(subs)
        except TokenExpiredError:
            await self._handle_token_expired()
        except APIError as ex:
            self._sub_error.value = ex.message
            self._sub_error.visible = True
        except Exception:
            self._sub_error.value = "Failed to load subscriptions."
            self._sub_error.visible = True
        finally:
            self._sub_loading.visible = False
            self.page.update()

    def _render_subscriptions(self, subs: list[dict]) -> None:
        self._sub_list.controls.clear()
        self._sub_empty.visible = not subs
        for sub in subs:
            self._sub_list.controls.append(self._build_sub_card(sub))

    def _build_sub_card(self, sub: dict) -> ft.Container:
        city_name = sub["city"]["name"]
        interval_h = sub["interval_hours"]
        notif_type = sub["notification_type"]

        interval_label = next(
            (v for k, v in self._interval_options if k == str(interval_h)),
            f"Every {interval_h}h",
        )
        notif_meta = next(
            (item for item in self._notif_types if item["value"] == notif_type),
            {"label": notif_type.capitalize(), "icon": "NOTIFICATIONS_NONE"},
        )

        notif_badge = badge(
            f"{notif_meta.get('label', notif_type.capitalize())}",
            "#EFF6FF" if notif_type == "email" else "#F0FDF4",
            INFO_COLOR if notif_type == "email" else SUCCESS_COLOR,
        )

        return card(
            ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                        expand=True,
                        spacing=6,
                        controls=[
                            ft.Text(
                                city_name,
                                size=16,
                                weight=ft.FontWeight.W_600,
                                color=TEXT_PRIMARY,
                            ),
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Icon(
                                        resolve_icon(
                                            str(
                                                notif_meta.get(
                                                    "icon", "NOTIFICATIONS_NONE"
                                                )
                                            )
                                        ),
                                        size=14,
                                        color=TEXT_SECONDARY,
                                    ),
                                    notif_badge,
                                    ft.Container(
                                        content=ft.Text(
                                            interval_label,
                                            size=11,
                                            color=TEXT_SECONDARY,
                                        ),
                                        bgcolor=BG_COLOR,
                                        border_radius=20,
                                        padding=ft.Padding.symmetric(
                                            horizontal=10, vertical=3
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EDIT_OUTLINED,
                        icon_color=PRIMARY,
                        tooltip="Edit",
                        on_click=lambda e, s=sub: self._open_edit_dialog(s),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=ERROR_COLOR,
                        tooltip="Delete",
                        on_click=lambda e, s=sub: self._confirm_delete(s),
                    ),
                ],
            ),
        )

    def _open_add_dialog(self, e) -> None:
        self._open_subscription_dialog()

    def _open_edit_dialog(self, sub: dict) -> None:
        self._open_subscription_dialog(existing=sub)

    def _open_subscription_dialog(self, existing: Optional[dict] = None) -> None:
        try:
            SubscriptionDialog(
                self.page,
                self.api,
                on_saved=self._load_subscriptions,
                existing=existing,
                options={
                    "intervals": self._interval_options,
                    "notification_types": self._notif_types,
                },
            ).open()
        except Exception:
            self._sub_error.value = "Cannot open subscription dialog right now."
            self._sub_error.visible = True
            self.page.update()

    def _confirm_delete(self, sub: dict) -> None:
        async def do_delete(e) -> None:
            self.page.pop_dialog()
            try:
                await asyncio.to_thread(self.api.delete_subscription, sub["id"])
                await self._load_subscriptions()
            except APIError as ex:
                self._sub_error.value = ex.message
                self._sub_error.visible = True
                self.page.update()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Delete Subscription", weight=ft.FontWeight.BOLD),
                content=ft.Text(
                    f"Remove subscription for {sub['city']['name']}?",
                    color=TEXT_SECONDARY,
                ),
                actions=[
                    ft.TextButton(
                        content=ft.Text("Cancel", color=TEXT_SECONDARY),
                        on_click=lambda e: self.page.pop_dialog(),
                    ),
                    ft.Button(
                        content=ft.Text("Delete", color=ft.Colors.WHITE),
                        style=ft.ButtonStyle(
                            bgcolor=ERROR_COLOR,
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        on_click=do_delete,
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

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
            await self._load_subscriptions(show_inner=False)
        finally:
            self._header_ring.visible = False
            self._is_refreshing = False
            self._last_scroll_px = 0.0
            self._pull_visual = 0.0
            self._pull_spacer.height = 0
            self.page.update()

    async def _handle_token_expired(self) -> None:
        auth_session: AuthSession = self.page.auth_session
        await auth_session.logout_and_redirect("/login")
