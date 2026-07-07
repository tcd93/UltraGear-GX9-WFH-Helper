import mouse
from aiowebostv import WebOsClient

async def mouse_event_handler(event, client: WebOsClient):
    if not client.is_connected():
        return

    if isinstance(event, mouse.ButtonEvent):
        if event.event_type == mouse.DOWN:
            if event.button == mouse.LEFT:
                await client.click()
            elif event.button == mouse.RIGHT:
                await client.button("BACK")

    elif isinstance(event, mouse.WheelEvent):
        if event.delta != 0:
            await client.scroll(0, -event.delta)
