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


class LoginView:
    """
    Represents a login view in the application.

    This class is responsible for providing the structure, layout, and interaction
    logic for the login screen. It includes input fields for email and password,
    error handling for invalid input or connection issues, and manages user sign-in
    using the provided API service and the `AuthSession` in the application.

    :ivar page: The application page instance where the view will be rendered.
    :type page: ft.Page
    :ivar api: The API service to handle login-related requests.
    :type api: APIService
    """

    def __init__(self, page: ft.Page, api: APIService) -> None:
        self.page = page
        self.api = api

    def get_view(self) -> ft.View:
        page, api = self.page, self.api

        email_field = build_auth_field(
            "Email",
            "you@example.com",
            kb=ft.KeyboardType.EMAIL,
            icon=ft.Icons.EMAIL_OUTLINED,
        )
        password_field = build_auth_field(
            "Password",
            "Enter your password",
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
        login_btn = ft.ElevatedButton(
            content=ft.Text(
                "Sign In", color=ft.Colors.WHITE, size=15, weight=ft.FontWeight.W_600
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
            login_btn.disabled = active
            login_btn.content = (
                spinner
                if active
                else ft.Text(
                    "Sign In",
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

        async def handle_login(e) -> None:
            if not email_field.value or not password_field.value:
                show_error("Please enter your email and password.")
                return

            error_box.visible = False
            set_loading(True)
            try:
                data = await asyncio.to_thread(
                    api.login, email_field.value.strip(), password_field.value
                )
                auth_session: AuthSession = page.auth_session
                await auth_session.establish(data["access"], data["refresh"])
                await page.push_route("/")
            except APIError as ex:
                show_error(ex.message)
            except Exception:
                show_error("Connection error. Please try again.")
            finally:
                set_loading(False)

        login_btn.on_click = handle_login

        return ft.View(
            route="/login",
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
                            ft.Container(height=48),
                            ft.Container(
                                width=96,
                                height=96,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Image(
                                    src="favicon.png", width=76, height=76
                                ),
                            ),
                            ft.Container(height=20),
                            ft.Text(
                                "Weather Reminder",
                                size=26,
                                weight=ft.FontWeight.BOLD,
                                color=TEXT_PRIMARY,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Container(height=6),
                            ft.Text(
                                "Sign in to your account",
                                size=14,
                                color=TEXT_SECONDARY,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Container(height=36),
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
                                        email_field,
                                        password_field,
                                        error_box,
                                        ft.Container(height=2),
                                        ft.Row([login_btn]),
                                    ],
                                ),
                            ),
                            ft.Container(height=20),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Text(
                                        "Don't have an account?",
                                        size=14,
                                        color=TEXT_SECONDARY,
                                    ),
                                    ft.TextButton(
                                        content=ft.Text(
                                            "Sign up", color=PRIMARY, size=14
                                        ),
                                        on_click=lambda e: page.run_task(
                                            page.push_route, "/register"
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
            ],
        )
