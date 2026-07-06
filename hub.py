import asyncio
import os
import sys
import threading
import time
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
HEARTBEAT_SECONDS = 3
RECONNECT_CHECK_INTERVAL_SECONDS = 1
RECONNECT_MAX_BACKOFF_SECONDS = 10


async def main():
    app_state = AppState()
    loop = asyncio.get_event_loop()
    shutdown_future = loop.create_future()
    keyboard_hook = None

    client = WebOsClient(HOST, CLIENT_KEY, heartbeat=HEARTBEAT_SECONDS)

    def set_keyboard_capture(enabled: bool):
        nonlocal keyboard_hook

        if keyboard_hook is not None:
            keyboard.unhook(keyboard_hook)

        keyboard_hook = keyboard.hook(
            lambda event: keyboard_input_handler(event, loop, client, app_state),
            suppress=enabled,
        )

        if enabled:
            print("Keyboard captured for webOS input")
        else:
            print("Keyboard passthrough enabled")

    def update_input_mode():
        should_capture = (
            app_state.in_webos() and client.is_connected() and not app_state.reconnecting
        )
        set_keyboard_capture(should_capture)

    def request_shutdown():
        if not shutdown_future.done():
            # set the running flag to False to stop the mouse polling thread
            app_state.running = False
            loop.call_soon_threadsafe(shutdown_future.set_result, None)

    async def app_changed(app_id: str):
        app_state.last_app = app_state.current_app
        app_state.current_app = app_id
        print(f"Current app: {app_id}")
        update_input_mode()

        if (
            not app_state.in_webos()
            and app_state.last_app is not None
            and app_state.last_app.startswith("com.webos.app.home")
        ):
            if shutdown_future is not None and not shutdown_future.done():
                print("App not in webOS, shutting down...")
                request_shutdown()

    async def connect_and_subscribe() -> bool:
        try:
            app_state.reconnecting = True
            update_input_mode()
            await client.connect()
            await client.subscribe_current_app(app_changed)
            app_state.reconnecting = False
            update_input_mode()
            return True
        except Exception as exc:
            print(f"Initial connect/subscribe failed: {exc}")
            app_state.reconnecting = True
            update_input_mode()
            return False

    async def reconnect_monitor():
        backoff_seconds = 0.5
        while app_state.running:
            await asyncio.sleep(RECONNECT_CHECK_INTERVAL_SECONDS)

            if client.is_connected():
                backoff_seconds = 0.5
                app_state.reconnecting = False
                update_input_mode()
                continue

            while app_state.running and not client.is_connected():
                try:
                    app_state.reconnecting = True
                    update_input_mode()
                    print("Reconnecting to monitor...")
                    await client.connect()
                    await client.subscribe_current_app(app_changed)
                    app_state.reconnecting = False
                    update_input_mode()
                    print("Reconnected to monitor")
                    backoff_seconds = 0.5
                    break
                except Exception as exc:
                    print(f"Reconnect failed: {exc}")
                    await asyncio.sleep(backoff_seconds)
                    backoff_seconds = min(
                        backoff_seconds * 2,
                        RECONNECT_MAX_BACKOFF_SECONDS,
                    )

    if not await connect_and_subscribe():
        request_shutdown()

    reconnect_task = asyncio.create_task(reconnect_monitor())

    set_keyboard_capture(False)

    # HOME page on start
    initial_command = sys.argv[1] if len(sys.argv) > 1 else "HOME"

    if initial_command:
        await client.button(initial_command)

    update_input_mode()

    threading.Thread(
        target=mouse_pos_polling,
        args=(loop, client, app_state),
    ).start()

    mouse.hook(lambda event: mouse_event_handler(event, loop, client, app_state))

    try:
        await shutdown_future
    finally:
        app_state.running = False

        reconnect_task.cancel()
        try:
            await reconnect_task
        except asyncio.CancelledError:
            pass

        keyboard.unhook_all()
        mouse.unhook_all()
        if client is not None:
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
