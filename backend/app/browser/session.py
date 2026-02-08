"""
BrowserSession - Represents a single browser instance for a room.

Each room gets one browser session that all participants see.

Note: Uses sync Playwright API with a dedicated thread per session
to avoid threading conflicts.
"""

import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


class BrowserSession:
    """
    Wraps a Playwright browser page with methods for remote control.

    Each session has its own dedicated thread to avoid Playwright
    threading issues.

    Features:
    - Popup blocking: New tabs/popups are automatically closed
    - Off-screen rendering: Window is hidden but still captures via CDP
    """

    def __init__(self, room_code: str):
        self.room_code = room_code
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._is_running = False
        self._blocked_popups: List[str] = []  # Track blocked popup URLs
        # Dedicated single-thread executor for this session
        # All Playwright calls MUST happen on this same thread
        self._executor = ThreadPoolExecutor(max_workers=1)

    @property
    def is_running(self) -> bool:
        return self._is_running and self._page is not None

    def _handle_popup(self, popup: Page) -> None:
        """Handle popup windows - close them and log."""
        try:
            url = popup.url or "about:blank"
            print(f"[BrowserSession] Blocked popup: {url}")
            self._blocked_popups.append(url)
            popup.close()
        except Exception as e:
            print(f"[BrowserSession] Error closing popup: {e}")

    def _start_sync(self, width: int, height: int) -> None:
        """Synchronous browser start - runs in dedicated thread."""
        self._playwright = sync_playwright().start()

        # Launch headed (not headless) so audio works, but position off-screen
        self._browser = self._playwright.chromium.launch(
            headless=False,
            args=[
                # Position off-screen (Playwright CDP screenshots still work!)
                "--window-position=-32000,-32000",
                "--window-size=1280,720",
                "--autoplay-policy=no-user-gesture-required",  # Allow autoplay
                "--disable-background-timer-throttling",  # Keep audio playing
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--force-device-scale-factor=1",  # Consistent scaling
            ]
        )

        # Create browser context
        self._context = self._browser.new_context(
            viewport={"width": width, "height": height},
        )

        # Create main page FIRST (before adding popup handler)
        self._page = self._context.new_page()

        # NOW add popup blocking - this will only affect NEW pages (popups)
        # not our main page which already exists
        self._context.on("page", self._handle_popup)

        self._is_running = True
        print(f"[BrowserSession] Started for room {self.room_code} (off-screen, popups blocked)")

    async def start(self, width: int = 1280, height: int = 720) -> None:
        """Launch the browser and create a new page."""
        if self._is_running:
            return

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self._start_sync, width, height)

    def _stop_sync(self) -> None:
        """Synchronous browser stop - runs in dedicated thread."""
        self._is_running = False

        if self._page:
            self._page.close()
            self._page = None

        if self._context:
            self._context.close()
            self._context = None

        if self._browser:
            self._browser.close()
            self._browser = None

        if self._playwright:
            self._playwright.stop()
            self._playwright = None

        if self._blocked_popups:
            print(f"[BrowserSession] Blocked {len(self._blocked_popups)} popups during session")
        print(f"[BrowserSession] Stopped for room {self.room_code}")

    async def stop(self) -> None:
        """Close the browser and clean up resources."""
        if not self._is_running:
            return

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self._stop_sync)

        # Shutdown the executor
        self._executor.shutdown(wait=False)

    def _navigate_sync(self, url: str) -> None:
        """Synchronous navigation - runs in dedicated thread."""
        if not self._page:
            raise RuntimeError("Browser not started")

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        self._page.goto(url, wait_until="domcontentloaded")
        print(f"[BrowserSession] Navigated to {url}")

    async def navigate(self, url: str) -> None:
        """Navigate to a URL."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self._navigate_sync, url)

    def _click_sync(self, x: int, y: int) -> None:
        """Synchronous click - runs in dedicated thread."""
        if not self._page:
            raise RuntimeError("Browser not started")
        self._page.mouse.click(x, y)

    async def click(self, x: int, y: int) -> None:
        """Click at specific coordinates."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self._click_sync, x, y)

    def _type_text_sync(self, text: str) -> None:
        """Synchronous typing - runs in dedicated thread."""
        if not self._page:
            raise RuntimeError("Browser not started")
        self._page.keyboard.type(text)

    async def type_text(self, text: str) -> None:
        """Type text at the current cursor position."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self._type_text_sync, text)

    def _press_key_sync(self, key: str) -> None:
        """Synchronous key press - runs in dedicated thread."""
        if not self._page:
            raise RuntimeError("Browser not started")
        self._page.keyboard.press(key)

    async def press_key(self, key: str) -> None:
        """Press a special key (Enter, Backspace, Tab, etc.)"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self._press_key_sync, key)

    def _scroll_sync(self, delta_x: int, delta_y: int) -> None:
        """Synchronous scroll - runs in dedicated thread."""
        if not self._page:
            raise RuntimeError("Browser not started")
        self._page.mouse.wheel(delta_x, delta_y)

    async def scroll(self, delta_x: int = 0, delta_y: int = 0) -> None:
        """Scroll the page."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self._scroll_sync, delta_x, delta_y)

    def _screenshot_sync(self) -> str:
        """Synchronous screenshot - runs in dedicated thread."""
        if not self._page:
            raise RuntimeError("Browser not started")

        # Lower quality for faster encoding/transfer
        image_bytes = self._page.screenshot(type="jpeg", quality=50)
        return base64.b64encode(image_bytes).decode("utf-8")

    async def screenshot(self) -> str:
        """Take a screenshot and return as base64-encoded string."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._screenshot_sync)

    def _get_current_url_sync(self) -> str:
        """Synchronous URL getter - runs in dedicated thread."""
        if not self._page:
            raise RuntimeError("Browser not started")
        return self._page.url

    async def get_current_url(self) -> str:
        """Get the current page URL."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._get_current_url_sync)
