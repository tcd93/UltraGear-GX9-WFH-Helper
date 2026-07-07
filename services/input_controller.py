import asyncio
from collections.abc import Callable

import keyboard
from aiowebostv import WebOsClient
import mouse

from handlers.keyboard_input import keyboard_input_handler
from handlers.mouse_click import mouse_event_handler
from handlers.mouse_polling import mouse_move_polling


class InputController:
    def __init__(
        self,
        client: WebOsClient,
        interactive_input_enabled: Callable[[], bool],
    ):
        """
        Initialize the InputController.

        Args:
            client (WebOsClient): The WebOS client instance.
            interactive_input_enabled (Callable[[], bool]): A callable that returns a boolean indicating whether interactive input is enabled.
        """
        self._client = client
        self._is_interactive_input_enabled = interactive_input_enabled

        self._loop = asyncio.get_event_loop()
        self._keyboard_hook = None
        self._mouse_hook = None
        self._mouse_polling_task = None

    def _keyboard_hook_callback(self, event):
        if self._is_interactive_input_enabled() and event.event_type == "down":
            asyncio.run_coroutine_threadsafe(
                keyboard_input_handler(
                    event,
                    self._client,
                ),
                self._loop,
            )
            return True
        return None

    def _mouse_hook_callback(self, event):
        if self._is_interactive_input_enabled():
            asyncio.run_coroutine_threadsafe(
                mouse_event_handler(
                    event,
                    self._client,
                ),
                self._loop,
            )
            return True
        return None

    def update_input_mode(self):
        """
        Update the input mode based on enabled state of interactive input (`interactive_input_enabled`).
        If interactive input is enabled, it sets up hooks for keyboard and mouse events. 
        If not, it releases the hooks and stops mouse polling.
        """
        should_capture = self._is_interactive_input_enabled()
        if not should_capture:
            print("Inputs released for webOS input")
            self.close()
            return
        else:
            if self._keyboard_hook is None:
                print("Capturing keyboard inputs for webOS input...")
                self._keyboard_hook = keyboard.hook(
                    self._keyboard_hook_callback,
                    suppress=should_capture,
                )

            if self._mouse_hook is None:
                print("Capturing mouse inputs for webOS input...")
                self._mouse_hook = mouse.hook(
                    self._mouse_hook_callback,
                )

            if self._mouse_polling_task is None:
                print("Starting mouse move polling for webOS input...")
                self._mouse_polling_task = asyncio.run_coroutine_threadsafe(
                    mouse_move_polling(
                        self._client,
                        should_process_polling=self._is_interactive_input_enabled,
                    ),
                    self._loop,
                )

    def close(self):
        if self._keyboard_hook is not None:
            keyboard.unhook(self._keyboard_hook)
            self._keyboard_hook = None

        if self._mouse_hook is not None:
            mouse.unhook(self._mouse_hook)
            self._mouse_hook = None

        if self._mouse_polling_task is not None:
            self._mouse_polling_task.cancel()
            self._mouse_polling_task = None
