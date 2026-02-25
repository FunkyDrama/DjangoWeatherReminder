import flet as ft

from palette import BG_COLOR, PRIMARY
from services.api_service import APIService
from services.auth_session import AuthSession
from services.session_storage import SessionStorage
from views.dashboard_tab import DashboardTab
from views.login_view import LoginView
from views.logs_tab import LogsTab
from views.profile_tab import ProfileTab
from views.register_view import RegisterView


async def main(page: ft.Page) -> None:
    """
    Asynchronous function to initialize and configure the weather reminder application,
    manage session storage, and route handling.

    This function sets up the page title, theme, background color, dimensions, and
    services. It initializes session storage and an authentication session to manage
    user authentication. It also defines tab management and navigation handling, along
    with the logic for routing to different views in the application.

    :param page: The root page object for the application, which encapsulates the
                 UI components and services.
    :type page: ft.Page

    :return: This asynchronous function does not return any value.
    :rtype: None
    """
    page.title = "Weather Reminder by DK"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = BG_COLOR
    page.padding = 0
    page.window.width = 390
    page.window.height = 844
    shared_prefs = ft.SharedPreferences()
    page.services.append(shared_prefs)
    page.update()
    page.theme = ft.Theme(
        color_scheme_seed=PRIMARY,
        visual_density=ft.VisualDensity.COMFORTABLE,
    )

    api = APIService()
    session_storage = SessionStorage(page, shared_prefs)
    await session_storage.init()
    auth_session = AuthSession(page, api, session_storage)
    page.auth_session = auth_session

    _tabs: dict[int, ft.Control] = {}
    tab_content = ft.Container(expand=True, padding=0)

    def get_tab(index: int) -> ft.Control:
        if index not in _tabs:
            builders = {
                0: lambda: DashboardTab(page, api).build(),
                1: lambda: LogsTab(page, api).build(),
                2: lambda: ProfileTab(page, api).build(),
            }
            _tabs[index] = builders[index]()
        return _tabs[index]

    def switch_tab(index: int) -> None:
        tab_content.content = get_tab(index)
        for view in page.views:
            if view.route == "/" and view.navigation_bar:
                view.navigation_bar.selected_index = index
                break
        page.update()

    page.switch_tab = switch_tab

    def on_nav_change(e: ft.ControlEvent) -> None:
        tab_content.content = get_tab(e.control.selected_index)
        page.update()

    def build_main_shell() -> ft.View:
        _tabs.clear()
        tab_content.content = get_tab(0)
        return ft.View(
            route="/",
            controls=[tab_content],
            navigation_bar=ft.NavigationBar(
                selected_index=0,
                on_change=on_nav_change,
                bgcolor=ft.Colors.WHITE,
                indicator_color=PRIMARY + "22",
                destinations=[
                    ft.NavigationBarDestination(
                        icon=ft.Icons.CLOUD_OUTLINED,
                        selected_icon=ft.Icons.CLOUD,
                        label="Weather",
                    ),
                    ft.NavigationBarDestination(
                        icon=ft.Icons.NOTIFICATIONS_NONE,
                        selected_icon=ft.Icons.NOTIFICATIONS,
                        label="Logs",
                    ),
                    ft.NavigationBarDestination(
                        icon=ft.Icons.PERSON_OUTLINE,
                        selected_icon=ft.Icons.PERSON,
                        label="Profile",
                    ),
                ],
            ),
            bgcolor=BG_COLOR,
            padding=0,
        )

    async def route_change(e: ft.RouteChangeEvent) -> None:
        page.views.clear()
        route = page.route

        if route == "/login":
            page.views.append(LoginView(page, api).get_view())
        elif route == "/register":
            page.views.append(RegisterView(page, api).get_view())
        else:
            if not api.access_token:
                await page.push_route("/login")
                return
            page.views.append(build_main_shell())

        page.update()

    async def view_pop(e: ft.ViewPopEvent) -> None:
        page.views.pop()
        if page.views:
            await page.push_route(page.views[-1].route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    await page.push_route("/login")

    if await auth_session.restore():
        await page.push_route("/")


ft.run(main, assets_dir="assets")
