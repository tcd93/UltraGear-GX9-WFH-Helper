import asyncio
import keyboard
from aiowebostv import WebOsClient

from app_state import AppState

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


def keyboard_input_handler(
    event: keyboard.KeyboardEvent,
    loop: asyncio.AbstractEventLoop,
    client: WebOsClient,
    app_state: AppState,
):
    if event.event_type != "down":
        return

    if not app_state.in_webos():
        return

    # PROBLEM: hotkeys might conflict with text input.
    # This should be called before `send_button`
    send_ime_text(event, loop, client)

    # navigation keys
    if event.name in HOTKEYS:
        send_button(HOTKEYS[event.name], loop, client)

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


def send_button(button: str, loop: asyncio.AbstractEventLoop, client: WebOsClient):
    future = asyncio.run_coroutine_threadsafe(
        client.button(button),
        loop,
    )

    future.add_done_callback(lambda f: print(f.exception()) if f.exception() else None)


def send_ime_text(
    event: keyboard.KeyboardEvent,
    loop: asyncio.AbstractEventLoop,
    client: WebOsClient,
):
    """https://www.webosose.org/docs/reference/ls2-api/com-webos-service-ime"""

    if event.name == "backspace":
        future = asyncio.run_coroutine_threadsafe(
            client.request("com.webos.service.ime/deleteCharacters", {"count": 1}),
            loop,
        )
    elif event.name == "enter":
        future = asyncio.run_coroutine_threadsafe(
            client.request("com.webos.service.ime/sendEnterKey"),
            loop,
        )
    else:
        text = normalize_key_text(event)
        if text is None:
            return
        future = asyncio.run_coroutine_threadsafe(
            client.request("com.webos.service.ime/insertText", {"text": text}),
            loop,
        )
    
    future.add_done_callback(lambda f: print(f.exception()) if f.exception() else None)


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

