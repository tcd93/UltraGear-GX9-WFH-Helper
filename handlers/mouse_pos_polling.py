import asyncio
import time
from concurrent.futures import Future

from aiowebostv import WebOsClient
import mouse

from app_state import AppState


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

        if (
            app_state.reconnecting
            or not app_state.in_webos()
            or not client.is_connected()
        ):
            continue

        if dx == 0 and dy == 0:
            continue

        future = asyncio.run_coroutine_threadsafe(client.move(dx, dy), loop)
        future.add_done_callback(lambda f: print(f.exception()) if f.exception() else None)
