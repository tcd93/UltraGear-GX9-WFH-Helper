import asyncio
import os
from pathlib import Path

from aiowebostv import WebOsClient
from dotenv import load_dotenv

from app_state import AppState
from discover import get_monitor_ip
from services.input_controller import InputController

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

HOST = get_monitor_ip()
CLIENT_KEY = os.getenv("LG_MONITOR_CLIENT_KEY", "")
HEARTBEAT_SECONDS = 3


async def main():
    client = WebOsClient(HOST, CLIENT_KEY, heartbeat=HEARTBEAT_SECONDS)
    shutdown_future = asyncio.get_event_loop().create_future()
    app_state = AppState()

    input_control = InputController(
        client=client,
        interactive_input_enabled=lambda: app_state.in_webos()
        and client.is_connected(),
    )

    async def app_changed(app_id: str):
        app_state.last_app = app_state.current_app
        app_state.current_app = app_id
        print(f"App changed from {app_state.last_app} to {app_state.current_app}")
        input_control.update_input_mode()

        if (
            not app_state.in_webos()
            and app_state.last_app is not None
            and app_state.last_app.startswith("com.webos.app.home")
        ):
            print("App not in webOS, shutting down...")
            input_control.close()
            shutdown_future.set_result(None)


    try:
        await client.connect()
        await client.subscribe_current_app(app_changed)
        await shutdown_future
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
