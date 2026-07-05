import json
import socket
from pathlib import Path
from urllib.parse import urlparse

from ssdpy import SSDPClient

CACHE_FILE = Path("cache.json")


def is_alive(ip: str, port: int = 3000, timeout: float = 0.3):
    """Check if the monitor's webOS port is reachable."""
    try:
        with socket.create_connection((ip, port), timeout):
            return True
    except OSError:
        return False


def discover_monitor():
    print("Discovering monitor via SSDP...")

    client = SSDPClient()
    responses = client.m_search(
        st="urn:lge-com:service:webos-second-screen:1"
    )

    if not responses:
        raise RuntimeError("LG monitor not found.")

    ip = urlparse(responses[0]["location"]).hostname

    CACHE_FILE.write_text(
        json.dumps({"ip": ip}, indent=4)
    )

    print(f"Found monitor: {ip}")

    return ip


def get_monitor_ip():
    # 1. Try cache
    if CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text())

        ip = cache.get("ip")

        if ip and is_alive(ip):
            print(f"Using cached IP: {ip}")
            return ip

        print("Cached IP no longer valid.")

    # 2. Fallback to SSDP
    return discover_monitor()

def main():
    ip = get_monitor_ip()
    print(f"Monitor IP: {ip}")

if __name__ == "__main__":
    main()