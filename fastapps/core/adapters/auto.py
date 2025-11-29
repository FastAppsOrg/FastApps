"""Auto-select protocol adapter based on host capabilities."""

from __future__ import annotations

import logging

from typing import Optional, TYPE_CHECKING

from mcp import types

from fastapps.core.protocol import ProtocolAdapter
from fastapps.core.adapters.openai_apps import OpenAIAppsAdapter
from fastapps.core.adapters.mcp_apps import MCPAppsAdapter
from fastapps.core.adapters.utils import _inject_protocol_hint  # type: ignore[attr-defined]


logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from fastapps.core.server import WidgetMCPServer


class AutoProtocolAdapter(ProtocolAdapter):
    """
    Chooses OpenAI Apps or MCP Apps at runtime based on host capabilities.

    Logic:
    - Pre-register OpenAI handlers (baseline).
    - On initialize, inspect client capabilities.extensions["io.modelcontextprotocol/ui"].
    - If host advertises MCP Apps + supports text/html+mcp, switch to MCP handlers.
    - Keep chosen adapter for the rest of the session.
    """

    def __init__(self):
        self.active: Optional[ProtocolAdapter] = None
        self.openai_adapter = OpenAIAppsAdapter()
        self.mcp_adapter = MCPAppsAdapter()

    def register_handlers(self, widget_server: "WidgetMCPServer") -> None:
        # Start with OpenAI handlers as baseline
        self.openai_adapter.register_handlers(widget_server)
        self.active = self.openai_adapter

        server = widget_server.mcp._mcp_server
        original_initialize = server.request_handlers.get(types.InitializeRequest)

        async def initialize_handler(
            req: types.InitializeRequest,
        ) -> types.ServerResult:
            chosen = self._decide_adapter(req)
            if chosen is self.mcp_adapter and self.active is not self.mcp_adapter:
                # Switch to MCP handlers (overwrites request_handlers)
                self.mcp_adapter.register_handlers(widget_server)
                self.active = self.mcp_adapter

            # After potential switch, get the current initialize handler
            handler = server.request_handlers.get(types.InitializeRequest)
            if handler is initialize_handler and original_initialize:
                # Fallback to original if overwrite failed
                handler = original_initialize

            if handler:
                return await handler(req)

            # Should not happen, but fall back to minimal response
            return types.ServerResult(
                types.InitializeResult(
                    protocolVersion=req.params.protocolVersion,
                    capabilities=types.ServerCapabilities(),
                    serverInfo=types.Implementation(name="FastApps", version="auto"),
                )
            )

        server.request_handlers[types.InitializeRequest] = initialize_handler

    def _decide_adapter(self, req: types.InitializeRequest) -> ProtocolAdapter:
        try:
            caps = getattr(req.params, "capabilities", None)
            extensions = getattr(caps, "extensions", {}) if caps else {}
            ui_ext = extensions.get("io.modelcontextprotocol/ui")
            mime_types = ui_ext.get("mimeTypes", []) if isinstance(ui_ext, dict) else []
            if any(mt.lower() == "text/html+mcp" for mt in mime_types):
                logger.info("AutoAdapter selected MCP Apps based on client capabilities")
                return self.mcp_adapter
        except Exception:
            pass
        logger.info("AutoAdapter selected OpenAI Apps (default)")
        return self.openai_adapter
