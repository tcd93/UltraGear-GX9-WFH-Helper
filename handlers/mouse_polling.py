import asyncio
from collections.abc import Callable

import mouse
from aiowebostv import WebOsClient

from app_state import AppState

POLL_INTERVAL_SECONDS = 1 / 60.0
MOVE_DEADZONE_PIXELS = 2

# We don't use mouse.hook() for mouse movement because when app in
# fullscreen, OS may hide the cursor to a corner. So we poll the mouse
# position instead of relying on mouse events.


async def mouse_move_polling(
    client: WebOsClient,
    should_process_polling: Callable[[], bool],
):
    anchor_x = None
    anchor_y = None

    while should_process_polling():
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

        try:
            x, y = mouse.get_position()
        except OSError:
            continue

        if anchor_x is None or anchor_y is None:
            anchor_x, anchor_y = x, y
            continue

        dx = x - anchor_x
        dy = y - anchor_y

        if abs(dx) <= MOVE_DEADZONE_PIXELS and abs(dy) <= MOVE_DEADZONE_PIXELS:
            continue

        # Keep local cursor at a fixed anchor so desktop edges do not clip deltas.
        try:
            mouse.move(anchor_x, anchor_y, absolute=True, duration=0)
        except TypeError:
            pass

        await client.move(dx, dy)
