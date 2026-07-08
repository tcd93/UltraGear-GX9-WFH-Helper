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
HDMI1 = "HDMI_1"
HDMI2 = "HDMI_2"
USB = "USB-C_1"

async def main():
    client = WebOsClient(HOST, CLIENT_KEY)

    await client.connect()

    current_id: str = await client.get_input() # type: ignore

    print("Current ID:", current_id)

    if current_id in (HDMI2, "com.webos.app.hdmi2"):
        target = USB
    else:
        target = HDMI2

    print("Switching to:", target)

    try:
        result = await client.set_input(target)
    except Exception as e:
        print(f"Error setting input: {e}")
    finally:
        await client.disconnect()


asyncio.run(main())