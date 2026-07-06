import asyncio
import os
import sys
import threading
from pathlib import Path

import keyboard
import mouse
from aiowebostv import WebOsClient
from dotenv import load_dotenv

from discover import get_monitor_ip
from handlers.keyboard_input import keyboard_input_handler
from handlers.mouse_click import mouse_event_handler
from handlers.mouse_pos_polling import mouse_pos_polling
from app_state import AppState

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

HOST = get_monitor_ip()
CLIENT_KEY = os.getenv("LG_MONITOR_CLIENT_KEY", "")


async def main():
    app_state = AppState()
    loop = asyncio.get_event_loop()
    shutdown_future = loop.create_future()

    client = WebOsClient(HOST, CLIENT_KEY)
    await client.connect()

    def request_shutdown():
        if app_state.running:
            app_state.running = False

        if not shutdown_future.done():
            loop.call_soon_threadsafe(shutdown_future.set_result, None)

    async def app_changed(app_id: str):
        app_state.last_app = app_state.current_app
        app_state.current_app = app_id

        if (
            not app_state.in_webos()
            and app_state.last_app is not None
            and app_state.last_app.startswith("com.webos.app.home")
        ):
            if shutdown_future is not None and not shutdown_future.done():
                print("App not in webOS, shutting down...")
                request_shutdown()

    async def app_monitor(app_state: AppState):
        """Manually poll the current app state, since the WebOS TV does not 
        provide a reliable event for this (`subscribe_current_app` is not reliable)."""
        while app_state.running:
            try:
                app: str = await client.get_current_app()  # type: ignore

                if app != app_state.current_app:
                    print(f"App changed: {app_state.current_app} -> {app}")
                    await app_changed(app)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                if app_state.running:
                    print(f"Failed to get current app: {e}")

            await asyncio.sleep(1)  # Poll every second

    app_monitor_task = asyncio.create_task(app_monitor(app_state))

    # HOME page on start
    initial_command = sys.argv[1] if len(sys.argv) > 1 else "HOME"

    if initial_command:
        await client.button(initial_command)

    keyboard.hook(
        lambda event: keyboard_input_handler(event, loop, client, app_state),
        suppress=True,
    )

    threading.Thread(
        target=mouse_pos_polling,
        args=(loop, client, app_state),
    ).start()

    mouse.hook(lambda event: mouse_event_handler(event, loop, client, app_state))

    try:
        await shutdown_future
    finally:
        # Stop everyone first
        app_state.running = False

        # Stop new events arriving
        keyboard.unhook_all()
        mouse.unhook_all()

        # Stop polling task
        app_monitor_task.cancel()
        try:
            await app_monitor_task
        except asyncio.CancelledError:
            pass

        # Disconnect last
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
