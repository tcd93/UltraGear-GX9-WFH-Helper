import asyncio
import time
from concurrent.futures import Future
import keyboard
from aiowebostv import WebOsClient

from app_state import AppState


ERROR_LOG_INTERVAL_SECONDS = 2.0
_last_error_log_by_message: dict[str, float] = {}


def _log_future_exception(future: Future):
    try:
        exception = future.exception()
    except Exception:
        return

    if exception is None:
        return

    now = time.monotonic()
    message = str(exception)
    last_logged = _last_error_log_by_message.get(message, 0.0)
    if now - last_logged >= ERROR_LOG_INTERVAL_SECONDS:
        _last_error_log_by_message[message] = now
        print(exception)

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

    if app_state.reconnecting:
        return

    if not app_state.in_webos():
        return

    if not client.is_connected():
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
    if not client.is_connected():
        return

    future = asyncio.run_coroutine_threadsafe(
        client.button(button),
        loop,
    )

    future.add_done_callback(_log_future_exception)


def send_ime_text(
    event: keyboard.KeyboardEvent,
    loop: asyncio.AbstractEventLoop,
    client: WebOsClient,
):
    """https://www.webosose.org/docs/reference/ls2-api/com-webos-service-ime"""

    if not client.is_connected():
        return

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

    future.add_done_callback(_log_future_exception)


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

