"""Protocol adapter interface for MCP UI variants.

Adapters allow the framework to target different MCP UI extensions
without rewriting widget or server code. The default behavior remains
OpenAI Apps SDK compatible; other adapters can register their own
handlers on the server instance.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapps.core.server import WidgetMCPServer


class ProtocolAdapter(ABC):
    """Defines how a protocol variation wires MCP handlers."""

    @abstractmethod
    def register_handlers(self, widget_server: "WidgetMCPServer") -> None:
        """Attach protocol-specific handlers to the given server."""
        raise NotImplementedError
