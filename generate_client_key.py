import asyncio
import os
from pathlib import Path

from aiowebostv import WebOsClient
from dotenv import load_dotenv

from discover import get_monitor_ip

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)


def update_env_file(client_key: str) -> None:
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    updated_lines = []
    found = False

    for line in lines:
        if line.startswith("LG_MONITOR_CLIENT_KEY="):
            updated_lines.append(f"LG_MONITOR_CLIENT_KEY={client_key}")
            found = True
        else:
            updated_lines.append(line)

    if not found:
        updated_lines.append(f"LG_MONITOR_CLIENT_KEY={client_key}")

    ENV_PATH.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


async def generate_client_key() -> str:
    host = get_monitor_ip()
    print(f"Connecting to monitor at {host}...")
    print("Please approve the pairing prompt on the TV when it appears.")

    client = WebOsClient(host, None)

    try:
        connected = await client.connect()
        if not connected:
            raise RuntimeError("Failed to connect to the monitor.")

        client_key = client.client_key
        if not client_key:
            raise RuntimeError("The TV did not return a client key.")

        print("Client key received successfully.")
        return client_key
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


def main() -> None:
    try:
        client_key = asyncio.run(generate_client_key())
    except KeyboardInterrupt:
        print("Cancelled.")
        return
    except Exception as exc:
        print(f"Failed to generate client key: {exc}")
        return

    update_env_file(client_key)
    print(f"Saved LG_MONITOR_CLIENT_KEY to {ENV_PATH}")


if __name__ == "__main__":
    main()
