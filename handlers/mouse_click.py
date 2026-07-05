import asyncio
from aiowebostv import WebOsClient
import mouse

from app_state import AppState


def mouse_event_handler(
    event, loop: asyncio.AbstractEventLoop, client: WebOsClient, app_state: AppState
):
    if not app_state.in_webos():
        return

    if isinstance(event, mouse.ButtonEvent):
        if event.event_type == mouse.DOWN:
            if event.button == mouse.LEFT:
                coro = client.click()
            elif event.button == mouse.RIGHT:
                coro = client.button("BACK")
            else:
                return
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            future.add_done_callback(
                lambda f: print(f.exception()) if f.exception() else None
            )

    elif isinstance(event, mouse.WheelEvent):
        if event.delta == 0:
            return
        future = asyncio.run_coroutine_threadsafe(
            client.scroll(0, -event.delta),
            loop,
        )
        future.add_done_callback(
            lambda f: print(f.exception()) if f.exception() else None
        )
