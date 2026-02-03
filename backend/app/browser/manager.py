"""
BrowserManager - Manages browser sessions across all rooms.

This is a singleton - only one instance exists for the entire application.
It keeps track of which rooms have active browser sessions.
"""

from app.browser.session import BrowserSession


class BrowserManager:
    """
    Manages multiple BrowserSession instances, one per room.

    Usage:
        manager = BrowserManager()
        session = await manager.create_session("ABC123")
        session = manager.get_session("ABC123")
        await manager.close_session("ABC123")
    """

    def __init__(self):
        # Dictionary mapping room_code -> BrowserSession
        self._sessions: dict[str, BrowserSession] = {}
        # Dictionary mapping room_code -> (controller_id, controller_username)
        self._controllers: dict[str, tuple[int, str]] = {}

    def get_session(self, room_code: str) -> BrowserSession | None:
        """
        Get an existing browser session for a room.

        Returns:
            The BrowserSession if it exists, None otherwise
        """
        return self._sessions.get(room_code)

    async def create_session(self, room_code: str) -> BrowserSession:
        """
        Create a new browser session for a room.

        If a session already exists for this room, returns the existing one.

        Args:
            room_code: The room to create a session for

        Returns:
            The new (or existing) BrowserSession
        """
        # Check if session already exists
        existing = self.get_session(room_code)
        if existing and existing.is_running:
            return existing

        # Create new session
        session = BrowserSession(room_code)
        await session.start()

        # Store in our dictionary
        self._sessions[room_code] = session

        print(f"[BrowserManager] Created session for room {room_code}")
        print(f"[BrowserManager] Active sessions: {len(self._sessions)}")

        return session

    async def close_session(self, room_code: str) -> None:
        """
        Close and remove a browser session.

        Args:
            room_code: The room whose session to close
        """
        session = self._sessions.pop(room_code, None)

        if session:
            await session.stop()
            print(f"[BrowserManager] Closed session for room {room_code}")
            print(f"[BrowserManager] Active sessions: {len(self._sessions)}")

    async def close_all_sessions(self) -> None:
        """
        Close all active browser sessions.

        Call this when shutting down the server.
        """
        room_codes = list(self._sessions.keys())

        for room_code in room_codes:
            await self.close_session(room_code)

        print("[BrowserManager] All sessions closed")

    @property
    def active_session_count(self) -> int:
        """Get the number of active browser sessions."""
        return len(self._sessions)

    # ─────────────────────────────────────────────────────────────────────────
    # Remote Control Management
    # ─────────────────────────────────────────────────────────────────────────

    def get_controller(self, room_code: str) -> tuple[int, str] | None:
        """
        Get the current controller for a room.

        Returns:
            Tuple of (user_id, username) or None if no controller set
        """
        return self._controllers.get(room_code)

    def set_controller(self, room_code: str, user_id: int, username: str) -> None:
        """Set the controller for a room."""
        self._controllers[room_code] = (user_id, username)
        print(f"[BrowserManager] Controller for {room_code}: {username} (id={user_id})")

    def clear_controller(self, room_code: str) -> None:
        """Clear the controller for a room."""
        self._controllers.pop(room_code, None)

    def is_controller(self, room_code: str, user_id: int) -> bool:
        """Check if a user is the current controller."""
        controller = self.get_controller(room_code)
        return controller is not None and controller[0] == user_id


# Singleton instance - use this throughout the application
browser_manager = BrowserManager()
