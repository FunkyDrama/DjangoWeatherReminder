import asyncio

import flet as ft

from palette import (
    BG_COLOR,
    CARD_COLOR,
    ERROR_BG,
    ERROR_COLOR,
    PRIMARY,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from services.auth_session import AuthSession
from services.api_service import APIError, APIService
from views.auth_fields import build_auth_field


class RegisterView:
    """
    Represents the registration view for the application.

    This class is responsible for creating and managing the user interface for
    the registration process. It includes fields for username, email, and
    password input, as well as error handling and integration with the API
    service to register users and establish authentication sessions.

    :ivar page: The current page instance passed to the view, used for rendering
        UI components and handling routing.
    :type page: ft.Page
    :ivar api: The `APIService` instance used for performing registration and
        authentication-related API calls.
    :type api: APIService
    """

    def __init__(self, page: ft.Page, api: APIService) -> None:
        self.page = page
        self.api = api

    def get_view(self) -> ft.View:
        page, api = self.page, self.api

        username_field = build_auth_field(
            "Username", "your_username", icon=ft.Icons.PERSON_OUTLINED
        )
        email_field = build_auth_field(
            "Email",
            "you@example.com",
            kb=ft.KeyboardType.EMAIL,
            icon=ft.Icons.EMAIL_OUTLINED,
        )
        password_field = build_auth_field(
            "Password",
            "Minimum 8 characters",
            password=True,
            icon=ft.Icons.LOCK_OUTLINED,
        )

        error_box = ft.Container(
            content=ft.Text("", color=ERROR_COLOR, size=13),
            bgcolor=ERROR_BG,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            visible=False,
        )

        spinner = ft.ProgressRing(
            width=22, height=22, color=ft.Colors.WHITE, stroke_width=2.5
        )
        register_btn = ft.ElevatedButton(
            content=ft.Text(
                "Create Account",
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
        )

        def set_loading(active: bool) -> None:
            register_btn.disabled = active
            register_btn.content = (
                spinner
                if active
                else ft.Text(
                    "Create Account",
                    color=ft.Colors.WHITE,
                    size=15,
                    weight=ft.FontWeight.W_600,
                )
            )
            page.update()

        def show_error(msg: str) -> None:
            error_box.content.value = msg
            error_box.visible = True
            page.update()

        async def handle_register(e) -> None:
            username = username_field.value.strip()
            email = email_field.value.strip()
            password = password_field.value

            if not username or not email or not password:
                show_error("Please fill in all fields.")
                return
            if len(password) < 8:
                show_error("Password must be at least 8 characters.")
                return

            error_box.visible = False
            set_loading(True)
            try:
                await asyncio.to_thread(api.register, username, email, password)
                data = await asyncio.to_thread(api.login, email, password)
                auth_session: AuthSession = page.auth_session
                await auth_session.establish(data["access"], data["refresh"])
                await page.push_route("/")
            except APIError as ex:
                show_error(ex.message)
            except Exception:
                show_error("Connection error. Please try again.")
            finally:
                set_loading(False)

        register_btn.on_click = handle_register

        return ft.View(
            route="/register",
            bgcolor=BG_COLOR,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Container(
                    expand=True,
                    padding=ft.padding.symmetric(horizontal=24, vertical=16),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                        controls=[
                            ft.Container(height=32),
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        icon=ft.Icons.ARROW_BACK,
                                        on_click=lambda e: page.run_task(
                                            page.push_route, "/login"
                                        ),
                                        icon_color=PRIMARY,
                                    ),
                                    ft.TextButton(
                                        content=ft.Text(
                                            "Back to Sign In", color=PRIMARY, size=14
                                        ),
                                        on_click=lambda e: page.run_task(
                                            page.push_route, "/login"
                                        ),
                                    ),
                                ],
                            ),
                            ft.Container(height=16),
                            ft.Container(
                                width=72,
                                height=72,
                                bgcolor=PRIMARY,
                                border_radius=20,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(
                                    ft.Icons.PERSON_ADD, size=36, color=ft.Colors.WHITE
                                ),
                            ),
                            ft.Container(height=16),
                            ft.Text(
                                "Create Account",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                color=TEXT_PRIMARY,
                            ),
                            ft.Container(height=4),
                            ft.Text(
                                "Fill in your details to get started",
                                size=14,
                                color=TEXT_SECONDARY,
                            ),
                            ft.Container(height=28),
                            ft.Container(
                                bgcolor=CARD_COLOR,
                                border_radius=20,
                                padding=24,
                                shadow=ft.BoxShadow(
                                    blur_radius=28,
                                    color="#00000014",
                                    offset=ft.Offset(0, 6),
                                ),
                                content=ft.Column(
                                    spacing=14,
                                    controls=[
                                        username_field,
                                        email_field,
                                        password_field,
                                        error_box,
                                        ft.Container(height=2),
                                        ft.Row([register_btn]),
                                    ],
                                ),
                            ),
                            ft.Container(height=20),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(
                                        "Already have an account?",
                                        size=14,
                                        color=TEXT_SECONDARY,
                                    ),
                                    ft.TextButton(
                                        content=ft.Text(
                                            "Sign in", color=PRIMARY, size=14
                                        ),
                                        on_click=lambda e: page.run_task(
                                            page.push_route, "/login"
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
            ],
        )
