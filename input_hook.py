import asyncio
import os
from pathlib import Path

import keyboard
import mouse
from aiowebostv import WebOsClient
from dotenv import load_dotenv

from app_state import AppState
from discover import get_monitor_ip
from handlers.keyboard_input import keyboard_input_handler
from handlers.mouse_click import mouse_event_handler
from handlers.mouse_pos_polling import mouse_pos_polling

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
    keyboard_capture_enabled = False

    client = WebOsClient(HOST, CLIENT_KEY, heartbeat=HEARTBEAT_SECONDS)

    def request_shutdown():
        if not shutdown_future.done():
            app_state.running = False
            loop.call_soon_threadsafe(shutdown_future.set_result, None)

    def set_keyboard_capture(enabled: bool):
        nonlocal keyboard_hook
        nonlocal keyboard_capture_enabled

        if keyboard_capture_enabled == enabled:
            return

        if keyboard_hook is not None:
            keyboard.unhook(keyboard_hook)

        keyboard_hook = keyboard.hook(
            lambda event: keyboard_input_handler(event, loop, client, app_state),
            suppress=enabled,
        )
        keyboard_capture_enabled = enabled

        if enabled:
            print("Keyboard captured for webOS input")
        else:
            print("Keyboard passthrough enabled")

    def update_input_mode():
        should_capture = (
            app_state.in_webos()
            and client.is_connected()
            and not app_state.reconnecting
        )
        set_keyboard_capture(should_capture)

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

    async def move_sender_worker():
        while app_state.running:
            await asyncio.sleep(1 / 120.0)

            if app_state.move_in_flight:
                continue

            if (
                app_state.reconnecting
                or not app_state.in_webos()
                or not client.is_connected()
            ):
                app_state.latest_move_delta = None
                continue

            pending_move = app_state.latest_move_delta
            if pending_move is None:
                continue

            app_state.latest_move_delta = None
            dx, dy = pending_move

            app_state.move_in_flight = True
            try:
                await client.move(dx, dy)
            except Exception as exc:
                print(exc)
            finally:
                app_state.move_in_flight = False

    if not await connect_and_subscribe():
        request_shutdown()

    reconnect_task = asyncio.create_task(reconnect_monitor())
    move_sender_task = asyncio.create_task(move_sender_worker())
    mouse_polling_task = asyncio.create_task(mouse_pos_polling(client, app_state))

    set_keyboard_capture(False)

    update_input_mode()

    mouse.hook(lambda event: mouse_event_handler(event, loop, client, app_state))

    try:
        await shutdown_future
    finally:
        app_state.running = False

        reconnect_task.cancel()
        move_sender_task.cancel()
        mouse_polling_task.cancel()
        try:
            await reconnect_task
        except asyncio.CancelledError:
            pass

        try:
            await move_sender_task
        except asyncio.CancelledError:
            pass

        try:
            await mouse_polling_task
        except asyncio.CancelledError:
            pass

        keyboard.unhook_all()
        mouse.unhook_all()
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
