import asyncio
import time
from concurrent.futures import Future
import keyboard
from aiowebostv import WebOsClient

HOTKEYS = {
    "home": "HOME",
    "up": "UP",
    "down": "DOWN",
    "left": "LEFT",
    "right": "RIGHT",
    "enter": "ENTER",
    # "backspace": "BACK", don't use backspace as it conflicts with text input
    "esc": "BACK",
}


async def keyboard_input_handler(
    event: keyboard.KeyboardEvent,
    client: WebOsClient,
):
    if event.event_type != "down":
        return

    if not client.is_connected():
        return

    # PROBLEM: hotkeys might conflict with text input.
    # This should be called before `send_button`
    await send_ime_text(event, client)

    # navigation keys
    if event.name in HOTKEYS:
        await send_button(HOTKEYS[event.name], client)

    return


SHIFT_CHAR_MAP = {
    "1": "!",
    "2": "@",
    "3": "#",
    "4": "$",
    "5": "%",
    "6": "^",
    "7": "&",
    "8": "*",
    "9": "(",
    "0": ")",
    "-": "_",
    "=": "+",
    "[": "{",
    "]": "}",
    ";": ":",
    "'": '"',
    ",": "<",
    ".": ">",
    "/": "?",
    "\\": "|",
    "`": "~",
}


async def send_button(button: str, client: WebOsClient):
    if not client.is_connected():
        return

    await client.button(button)


async def send_ime_text(
    event: keyboard.KeyboardEvent,
    client: WebOsClient,
):
    """https://www.webosose.org/docs/reference/ls2-api/com-webos-service-ime"""

    if not client.is_connected():
        return

    if event.name == "backspace":
        await client.request("com.webos.service.ime/deleteCharacters", {"count": 1})
    elif event.name == "enter":
        await client.request("com.webos.service.ime/sendEnterKey", {})
    else:
        text = normalize_key_text(event)
        if text is None:
            return
        await client.request("com.webos.service.ime/insertText", {"text": text})


def normalize_key_text(event) -> str | None:
    name = event.name
    if name == "space":
        return " "
    if name == "tab":
        return "\t"
    if len(name) == 1:
        if keyboard.is_pressed("shift"):
            if name.isalpha():
                return name.upper()
            return SHIFT_CHAR_MAP.get(name, name)
        return name
    return None

