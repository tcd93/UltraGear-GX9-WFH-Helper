import asyncio
import os
import sys
from pathlib import Path

from aiowebostv import WebOsClient
from dotenv import load_dotenv

from discover import get_monitor_ip

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

HOST = get_monitor_ip()
CLIENT_KEY = os.getenv("LG_MONITOR_CLIENT_KEY", "")
HEARTBEAT_SECONDS = 3


async def main():
    client = WebOsClient(HOST, CLIENT_KEY, heartbeat=HEARTBEAT_SECONDS)

    # HOME page on start
    initial_command = sys.argv[1] if len(sys.argv) > 1 else "HOME"

    try:
        await client.connect()
        if initial_command:
            await client.button(initial_command)
    finally:
        await client.disconnect()

    input_runner_path = BASE_DIR / "input_hook.py"
    process = await asyncio.create_subprocess_exec(sys.executable, str(input_runner_path))
    exit_code = await process.wait()
    if exit_code != 0:
        print(f"input_hook.py exited with code {exit_code}")


if __name__ == "__main__":
    asyncio.run(main())
