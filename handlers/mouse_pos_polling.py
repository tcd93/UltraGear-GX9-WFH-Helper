import asyncio

from aiowebostv import WebOsClient
import mouse

from app_state import AppState


def _recenter_mouse(anchor_x: int, anchor_y: int):
    try:
        mouse.move(anchor_x, anchor_y, absolute=True, duration=0)
    except TypeError:
        mouse.move(anchor_x, anchor_y)


async def mouse_pos_polling(client: WebOsClient, app_state: AppState):
    anchor_x, anchor_y = await asyncio.to_thread(mouse.get_position)
    # Poll at 60Hz to reduce traffic and improve Wi-Fi tolerance.
    poll_interval = 1 / 60.0

    while app_state.running:
        await asyncio.sleep(poll_interval)
        try:
            x, y = await asyncio.to_thread(mouse.get_position)
        except OSError:
            continue

        if (
            app_state.reconnecting
            or not app_state.in_webos()
            or not client.is_connected()
        ):
            anchor_x, anchor_y = x, y
            app_state.latest_move_delta = None
            continue

        dx = x - anchor_x
        dy = y - anchor_y

        # Keep cursor near a fixed anchor while captured so movement stays relative
        # and does not get clipped by desktop screen edges.
        if dx != 0 or dy != 0:
            await asyncio.to_thread(_recenter_mouse, anchor_x, anchor_y)

        if dx == 0 and dy == 0:
            continue

        if app_state.latest_move_delta is None:
            app_state.latest_move_delta = (dx, dy)
        else:
            pending_dx, pending_dy = app_state.latest_move_delta
            app_state.latest_move_delta = (pending_dx + dx, pending_dy + dy)
