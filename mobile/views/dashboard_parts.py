import asyncio
import threading
from typing import Optional

import flet as ft

from palette import (
    BORDER_COLOR,
    CARD_COLOR,
    ERROR_COLOR,
    PRIMARY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from services.api_service import APIError, APIService


def resolve_icon(name: str, fallback: str = ft.Icons.NOTIFICATIONS_NONE):
    """
    Resolves and retrieves an icon attribute from a predefined set of icons based on the provided name.
    If the specified icon name is not found, a fallback icon is returned.

    :param name: The name of the icon to resolve.
    :type name: str
    :param fallback: The fallback icon to use if the specified name does not exist. Defaults to
        `ft.Icons.NOTIFICATIONS_NONE`.
    :type fallback: str
    :return: The resolved icon corresponding to the provided name or the fallback icon.
    :rtype: str
    """
    return getattr(ft.Icons, name, fallback)


def section_title(text: str) -> ft.Text:
    """
    Generates a formatted text element with specific styling.

    This function creates a text element with a bold font weight, a font size of 17,
    and a specified primary text color. The input text is displayed in the formatted
    text element.

    :param text: The text content to be displayed.
    :type text: str
    :return: A styled text element created with the specified input text.
    :rtype: ft.Text
    """
    return ft.Text(text, size=17, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)


def card(content: ft.Control, padding: int = 16) -> ft.Container:
    """
    Creates a container styled as a card element with consistent spacing, background
    color, and shadow. The card is suitable for displaying content with a visually
    distinct layout.

    :param content: The primary content to be displayed inside the card. Typically,
        this is an instance of a control element to be rendered within the container.
    :param padding: The amount of padding inside the card, specified in pixels. Default
        value is 16. Adjust this value to control the spacing around the content.
    :return: A `ft.Container` instance that represents the card element with the specified
        content, padding, and visual styling.
    """
    return ft.Container(
        content=content,
        bgcolor=CARD_COLOR,
        border_radius=16,
        padding=padding,
        shadow=ft.BoxShadow(blur_radius=16, color="#0000000D", offset=ft.Offset(0, 3)),
    )


def badge(label: str, bg: str, fg: str) -> ft.Container:
    """
    Generates a visual badge with custom label, background color, and foreground (text) color.

    This function creates a badge represented as a container element. The badge
    includes a text label rendered with specified formatting such as font size,
    weight, and color. The container also provides customizable styling options
    for background color, padding, and border radius. This is ideal for creating
    small decorative labels or indicators in a user interface.

    :param label: The text to display within the badge.
    :type label: str
    :param bg: The background color of the badge.
    :type bg: str
    :param fg: The foreground (text) color of the label.
    :type fg: str
    :return: A container element styled as a badge containing the specified label.
    :rtype: ft.Container
    """
    return ft.Container(
        content=ft.Text(label, size=11, weight=ft.FontWeight.W_600, color=fg),
        bgcolor=bg,
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=10, vertical=3),
    )


def city_suggestion_tile(label: str, on_click) -> ft.Container:
    """
    Create a city suggestion tile component.

    This function generates a container styled to represent a suggestion tile
    for a city, including a label and an icon. It also supports an action
    triggered by an on-click event.

    :param label: The text label displayed on the tile.
    :type label: str
    :param on_click: The callback function to execute when the tile is clicked.
    :return: A styled container representing the suggestion tile for a city.
    :rtype: ft.Container
    """
    return ft.Container(
        on_click=on_click,
        bgcolor=CARD_COLOR,
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=8,
        content=ft.ListTile(
            leading=ft.Icon(ft.Icons.LOCATION_ON_OUTLINED, color=PRIMARY, size=18),
            title=ft.Text(label, size=13, color=TEXT_PRIMARY),
            dense=True,
        ),
    )


class SubscriptionDialog:
    """
    Represents a dialog for creating or editing a subscription.

    This class is responsible for managing the interface and functionality for
    subscribing to notifications. It allows users to specify a city, notification
    frequency, and notification type. The class can also prepopulate fields based
    on existing subscription details and fetch metadata such as intervals and
    notification types dynamically from an API service.

    :ivar page: The current page instance to manage UI components.
    :type page: ft.Page

    :ivar api: The API service instance used for fetching metadata and managing
        subscriptions.
    :type api: APIService

    :ivar on_saved: A callback function invoked after the subscription is
        successfully saved.
    :type on_saved: Callable

    :ivar existing: The existing subscription details, used for prepopulating
        dialog fields if not None.
    :type existing: Optional[dict]

    :ivar city_field: The text field where the user specifies the city name.
    :type city_field: ft.TextField

    :ivar interval_dd: A dropdown allowing the user to select the frequency of
        notifications.
    :type interval_dd: ft.Dropdown

    :ivar notif_rg: A radio group for selecting a notification type.
    :type notif_rg: ft.RadioGroup

    :ivar error_text: A text component for displaying error messages to the user
        during input validation or save failures.
    :type error_text: ft.Text

    :ivar save_btn: A button that triggers the save operation for the subscription.
    :type save_btn: ft.ElevatedButton

    :ivar dialog: The dialog component that encapsulates all form controls and
        actions.
    :type dialog: ft.AlertDialog
    """

    def __init__(
        self,
        page: ft.Page,
        api: APIService,
        on_saved,
        existing: Optional[dict] = None,
        options: Optional[dict] = None,
    ) -> None:
        self.page = page
        self.api = api
        self.on_saved = on_saved
        self.existing = existing
        self._options = options or {}
        self._search_timer: Optional[threading.Timer] = None
        self._build()

    def _build(self) -> None:
        ex = self.existing
        intervals = self._options.get("intervals") if self._options else None
        notif_types = self._options.get("notification_types") if self._options else None
        if not intervals or not notif_types:
            metadata = self.api.get_subscription_metadata()
            intervals = metadata.get("intervals")
            notif_types = metadata.get("notification_types")
        if not intervals and ex:
            intervals = [
                (str(ex["interval_hours"]), f"Every {ex['interval_hours']} hours")
            ]
        if not notif_types and ex:
            ex_type = str(ex["notification_type"])
            notif_types = [
                {
                    "value": ex_type,
                    "label": ex_type.capitalize(),
                    "icon": "NOTIFICATIONS_NONE",
                }
            ]
        if not intervals or not notif_types:
            raise RuntimeError("Subscription metadata is unavailable.")

        self._city_suggestions = ft.Column(visible=False, spacing=2)

        self.city_field = ft.TextField(
            label="City",
            hint_text="Type to search…",
            value=ex["city"]["name"] if ex else "",
            prefix_icon=ft.Icons.LOCATION_CITY,
            border_color=BORDER_COLOR,
            focused_border_color=PRIMARY,
            border_radius=10,
            text_size=15,
            cursor_color=PRIMARY,
            on_change=self._on_city_change,
        )

        self.interval_dd = ft.Dropdown(
            label="Notification frequency",
            value=str(ex["interval_hours"]) if ex else str(intervals[0][0]),
            options=[ft.DropdownOption(key=k, text=v) for k, v in intervals],
            border_color=BORDER_COLOR,
            focused_border_color=PRIMARY,
            border_radius=10,
        )
        if not any(str(k) == str(self.interval_dd.value) for k, _ in intervals):
            self.interval_dd.value = str(intervals[0][0])

        self.notif_rg = ft.RadioGroup(
            value=ex["notification_type"] if ex else str(notif_types[0]["value"]),
            content=ft.Row(
                controls=[
                    ft.Radio(
                        value=str(item["value"]),
                        label=str(item.get("label", item["value"])),
                    )
                    for item in notif_types
                ],
                spacing=20,
            ),
        )
        available_notif_values = {str(item["value"]) for item in notif_types}
        if self.notif_rg.value not in available_notif_values:
            self.notif_rg.value = str(notif_types[0]["value"])

        self.error_text = ft.Text("", color=ERROR_COLOR, size=12, visible=False)
        self.save_btn = ft.ElevatedButton(
            content=ft.Text(
                "Save", color=ft.Colors.WHITE, size=14, weight=ft.FontWeight.W_600
            ),
            style=ft.ButtonStyle(
                bgcolor={"": PRIMARY, "disabled": "#9CA3AF"},
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=self._handle_save,
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Edit Subscription" if ex else "New Subscription",
                size=18,
                weight=ft.FontWeight.BOLD,
                color=TEXT_PRIMARY,
            ),
            content=ft.Column(
                tight=True,
                width=320,
                spacing=14,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    self.city_field,
                    self._city_suggestions,
                    self.interval_dd,
                    ft.Text("Notify via", size=14, color=TEXT_SECONDARY),
                    self.notif_rg,
                    self.error_text,
                ],
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text("Cancel", color=TEXT_SECONDARY),
                    on_click=lambda e: self.page.pop_dialog(),
                ),
                self.save_btn,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def open(self) -> None:
        self.page.show_dialog(self.dialog)

    def _on_city_change(self, e) -> None:
        query = e.control.value.strip()
        if self._search_timer:
            self._search_timer.cancel()
        if len(query) < 2:
            self._city_suggestions.controls.clear()
            self._city_suggestions.visible = False
            self.page.update()
            return
        self._search_timer = threading.Timer(
            0.5,
            lambda: self.page.run_task(self._fetch_suggestions, query),
        )
        self._search_timer.start()

    async def _fetch_suggestions(self, query: str) -> None:
        try:
            cities = await asyncio.to_thread(self.api.search_cities, query)
        except Exception:
            return

        tiles = []
        for city in cities[:4]:
            label = city["name"]
            if city.get("state"):
                label += f", {city['state']}"
            label += f"  ({city['country']})"

            name = city["name"]

            def make_click(city_name=name):
                def on_click(e):
                    self.city_field.value = city_name
                    self._city_suggestions.controls.clear()
                    self._city_suggestions.visible = False
                    self.page.update()

                return on_click

            tiles.append(city_suggestion_tile(label, make_click()))

        self._city_suggestions.controls = tiles
        self._city_suggestions.visible = bool(tiles)
        self.page.update()

    async def _handle_save(self, e) -> None:
        city = self.city_field.value.strip()
        if not city:
            self.error_text.value = "Please enter a city name."
            self.error_text.visible = True
            self.page.update()
            return

        self._city_suggestions.controls.clear()
        self._city_suggestions.visible = False
        self.error_text.visible = False
        self.save_btn.disabled = True
        self.page.update()

        try:
            interval = int(self.interval_dd.value)
            notif = self.notif_rg.value

            if notif == "webhook" and not (self.api.current_user or {}).get(
                "webhook_url"
            ):
                self.save_btn.disabled = False
                self.page.pop_dialog()
                snack = ft.SnackBar(
                    ft.Text("Webhook URL not set. Please configure it in Profile."),
                    open=True,
                )
                self.page.overlay.append(snack)
                self.page.switch_tab(2)
                return

            if self.existing:
                await asyncio.to_thread(
                    self.api.update_subscription,
                    self.existing["id"],
                    city,
                    interval,
                    notif,
                )
            else:
                await asyncio.to_thread(
                    self.api.create_subscription,
                    city,
                    interval,
                    notif,
                )

            self.page.pop_dialog()
            await self.on_saved()
        except APIError as ex:
            self.error_text.value = ex.message
            self.error_text.visible = True
        except Exception:
            self.error_text.value = "Failed to save. Please try again."
            self.error_text.visible = True
        finally:
            self.save_btn.disabled = False
            self.page.update()
