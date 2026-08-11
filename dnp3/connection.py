"""
Connection state management module for Arcon DNP3 Client.
Tracks link state and handles auto-reconnect backoff configuration.
"""

from enum import Enum
from typing import Callable, List, Optional


class ConnectionState(Enum):
    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting..."
    CONNECTED = "Connected"
    CONNECTION_LOST = "Connection Lost"
    RECONNECTING = "Reconnecting..."


class ConnectionManager:
    """Manages connection status transitions and listener callbacks."""

    def __init__(self):
        self._state = ConnectionState.DISCONNECTED
        self._listeners: List[Callable[[ConnectionState, str], None]] = []
        self._last_error: Optional[str] = None

    @property
    def state(self) -> ConnectionState:
        return self._state

    def set_state(self, state: ConnectionState, message: str = ""):
        """Sets connection state and notifies all registered listeners."""
        self._state = state
        if message:
            self._last_error = message
        for listener in self._listeners:
            try:
                listener(state, message)
            except Exception:
                pass

    def add_listener(self, callback: Callable[[ConnectionState, str], None]):
        """Adds a listener callback(state, message)."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[ConnectionState, str], None]):
        """Removes a listener callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)
