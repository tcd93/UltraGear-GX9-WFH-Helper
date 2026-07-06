import asyncio
import time
from concurrent.futures import Future

from aiowebostv import WebOsClient
import mouse

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


def mouse_pos_polling(
    loop: asyncio.AbstractEventLoop, client: WebOsClient, app_state: AppState
):
    prev_x, prev_y = mouse.get_position()
    # Poll at 60Hz to reduce traffic and improve Wi-Fi tolerance.
    poll_interval = 1 / 60.0

    while app_state.running:
        time.sleep(poll_interval)
        try:
            x, y = mouse.get_position()
        except OSError:
            continue

        dx = x - prev_x
        dy = y - prev_y
        prev_x, prev_y = x, y

        if app_state.reconnecting or not app_state.in_webos() or not client.is_connected():
            continue

        if dx == 0 and dy == 0:
            continue

        future = asyncio.run_coroutine_threadsafe(client.move(dx, dy), loop)
        future.add_done_callback(_log_future_exception)
