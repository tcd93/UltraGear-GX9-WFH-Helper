class AppState:
    def __init__(self):
        self.current_app: str | None = None
        self.last_app: str | None = None
        self.running = True
        self.reconnecting = False

    def in_webos(self) -> bool:
        return self.current_app is not None and not self.current_app.startswith(
            (
                "com.webos.app.dp",
                "com.webos.app.hdmi",
                "com.webos.app.usbc",
            )
        )
