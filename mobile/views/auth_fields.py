import flet as ft

from palette import PRIMARY, TEXT_SECONDARY


def build_auth_field(
    label: str,
    hint: str,
    *,
    password: bool = False,
    kb=None,
    icon=None,
) -> ft.TextField:
    """
    Constructs and returns a configured text field component intended for authentication-related
    inputs such as usernames or passwords. This function customizes the appearance, behavior,
    and additional properties of the text field to suit authentication use cases.

    :param label: The label text to be displayed above the text field.
    :type label: str
    :param hint: The placeholder text to guide the user on the expected input.
    :type hint: str
    :param password: Indicates whether the text should be obscured for password entry.
    :type password: bool, optional
    :param kb: The keyboard type to be used for input (e.g., numeric, default). Defaults to None.
    :type kb: Optional
    :param icon: An optional icon to be displayed as a prefix in the text field. Defaults to None.
    :type icon: Optional
    :return: A configured text field component.
    :rtype: ft.TextField
    """
    return ft.TextField(
        label=label,
        hint_text=hint,
        password=password,
        can_reveal_password=password,
        keyboard_type=kb,
        autocorrect=False,
        prefix_icon=icon,
        border_color="#E5E7EB",
        focused_border_color=PRIMARY,
        border_radius=10,
        text_size=15,
        label_style=ft.TextStyle(color=TEXT_SECONDARY),
        cursor_color=PRIMARY,
    )
