import asyncio

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
    WARNING_COLOR,
)
from services.auth_session import AuthSession
from services.api_service import APIError, APIService


class ProfileTab:
    """
    Represents the profile tab in the application where users can view and edit their profile
    information such as webhook settings. This class interacts with the API service to fetch
    and update user data, and provides a user interface for viewing and managing profile
    details.

    :ivar page: The Flet Page object representing the active UI page.
    :type page: ft.Page
    :ivar api: The API service used for making requests related to user data.
    :type api: APIService
    """

    def __init__(self, page: ft.Page, api: APIService) -> None:
        self.page = page
        self.api = api
        self._built = False
        self._root: ft.Control | None = None

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

        self._save_btn = ft.ElevatedButton(
            content=ft.Text(
                "Save Changes",
                color=ft.Colors.WHITE,
                size=15,
                weight=ft.FontWeight.W_600,
            ),
            style=ft.ButtonStyle(
                bgcolor={"": PRIMARY, "disabled": "#9CA3AF"},
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.padding.symmetric(vertical=14),
                elevation=0,
            ),
            expand=True,
            on_click=self._handle_save,
        )

        self._feedback = ft.Container(
            content=ft.Text("", size=13),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
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
            border=ft.border.all(1, "#FDE68A"),
            border_radius=10,
            padding=12,
            visible=not has_webhook,
        )

        root = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Container(
                    bgcolor=PRIMARY,
                    padding=ft.padding.only(left=20, right=20, top=48, bottom=16),
                    content=ft.Row(
                        spacing=4,
                        controls=[
                            ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=24),
                            ft.Text(
                                "Profile",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    bgcolor=BG_COLOR,
                    padding=ft.padding.all(20),
                    expand=True,
                    content=ft.Column(
                        spacing=16,
                        controls=[
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
                            ft.Container(height=8),
                            ft.Row(
                                [
                                    ft.OutlinedButton(
                                        content=ft.Row(
                                            controls=[
                                                ft.Icon(
                                                    ft.Icons.LOGOUT,
                                                    color=ERROR_COLOR,
                                                    size=18,
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
                                            padding=ft.padding.symmetric(vertical=14),
                                        ),
                                        expand=True,
                                        on_click=self._handle_logout,
                                    )
                                ]
                            ),
                        ],
                    ),
                ),
            ],
        )
        return root

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
    Creates a styled container representing an informational row with a label and a value.

    The container is formatted with padding and contains a column layout with two
    text elements. The first text element represents the label with secondary
    styling, and the second represents the value with primary styling.

    :param label: The label text to display in the informational row.
    :type label: str
    :param value: The value text to display alongside its corresponding label.
    :type value: str
    :return: A container with a column layout containing the label and value.
    :rtype: ft.Container
    """
    return ft.Container(
        padding=ft.padding.only(left=16, right=16, top=14, bottom=14),
        content=ft.Column(
            spacing=2,
            controls=[
                ft.Text(label, size=12, color=TEXT_SECONDARY),
                ft.Text(value, size=16, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ],
        ),
    )
