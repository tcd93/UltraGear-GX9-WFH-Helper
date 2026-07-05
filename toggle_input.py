import asyncio
import os
from pathlib import Path

from aiowebostv import WebOsClient
from dotenv import load_dotenv

from discover import get_monitor_ip

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

HOST = get_monitor_ip()
CLIENT_KEY = os.getenv("LG_MONITOR_CLIENT_KEY", "")

DP = "DisplayPort_1"
USB = "USB-C_1"

async def main():
    client = WebOsClient(HOST, CLIENT_KEY)

    await client.connect()

    current = await client.get_input()

    print("Current input:", current)

    current_id = None

    # Different versions of aiowebostv return different shapes
    if isinstance(current, dict):
        current_id = current.get("id") or current.get("appId")
    elif isinstance(current, str):
        current_id = current

    print("Current ID:", current_id)

    if current_id in (DP, "com.webos.app.dp1"):
        target = USB
    else:
        target = DP

    print("Switching to:", target)

    result = await client.set_input(target)
    print(result)

    await client.disconnect()


asyncio.run(main())