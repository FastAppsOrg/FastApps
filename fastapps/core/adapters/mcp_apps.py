"""Adapter for MCP Apps Extension (SEP-1865 draft)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from mcp import types

from fastapps.core.protocol import ProtocolAdapter
from fastapps.core.utils import get_cli_version
from fastapps.core.adapters.utils import _execute_widget_call, _inject_protocol_hint
from fastapps.core.widget import BaseWidget, ClientContext, UserContext

if TYPE_CHECKING:
    from fastapps.core.server import WidgetMCPServer


class MCPAppsAdapter(ProtocolAdapter):
    """
    Implements handler wiring for the MCP Apps extension (ui:// resources, text/html+mcp).

    References:
    - reference/ext-apps/specification/draft/apps.mdx
    """

    def register_handlers(self, widget_server: "WidgetMCPServer") -> None:
        server = widget_server.mcp._mcp_server

        original_initialize = server.request_handlers.get(types.InitializeRequest)

        async def initialize_handler(
            req: types.InitializeRequest,
        ) -> types.ServerResult:
            # MCP Apps uses ui/initialize between host <-> iframe.
            # Here we just mirror locale negotiation for consistency.
            meta = req.params._meta if hasattr(req.params, "_meta") else {}
            requested_locale = meta.get("openai/locale") or meta.get("webplus/i18n")

            if requested_locale:
                widget_server.client_locale = requested_locale
                for widget in widget_server.widgets_by_id.values():
                    resolved = widget.negotiate_locale(requested_locale)
                    widget.resolved_locale = resolved

            if original_initialize:
                return await original_initialize(req)

            capabilities = types.ServerCapabilities()
            # Advertise MCP Apps extension if supported by the types model
            try:
                setattr(capabilities, "extensions", {"io.modelcontextprotocol/ui": {}})
            except Exception:
                pass

            return types.ServerResult(
                types.InitializeResult(
                    protocolVersion=req.params.protocolVersion,
                    capabilities=capabilities,
                    serverInfo=types.Implementation(
                        name="FastApps", version=get_cli_version()
                    ),
                )
            )

        server.request_handlers[types.InitializeRequest] = initialize_handler

        @server.list_tools()
        async def list_tools_handler() -> List[types.Tool]:
            tools_list = []
            for w in widget_server.widgets_by_id.values():
                tool_meta = {
                    "ui/resourceUri": w.template_uri,
                }

                if "securitySchemes" not in tool_meta and widget_server.server_requires_auth:
                    tool_meta["securitySchemes"] = [
                        {"type": "oauth2", "scopes": widget_server.server_auth_scopes}
                    ]

                tools_list.append(
                    types.Tool(
                        name=w.identifier,
                        title=w.title,
                        description=w.description or w.title,
                        inputSchema=w.get_input_schema(),
                        _meta=tool_meta,
                    )
                )
            return tools_list

        @server.list_resources()
        async def list_resources_handler() -> List[types.Resource]:
            resources = []
            for w in widget_server.widgets_by_id.values():
                resources.append(self._build_ui_resource(w))
            return resources

        async def read_resource_handler(
            req: types.ReadResourceRequest,
        ) -> types.ServerResult:
            widget = widget_server.widgets_by_uri.get(str(req.params.uri))
            if not widget:
                return types.ServerResult(
                    types.ReadResourceResult(
                        contents=[],
                        _meta={"error": f"Unknown resource: {req.params.uri}"},
                    )
                )

            html = _inject_protocol_hint(widget.build_result.html, "mcp-apps")

            contents = [
                types.TextResourceContents(
                    uri=widget.template_uri,
                    mimeType="text/html+mcp",
                    text=html,
                    _meta=self._build_ui_meta(widget),
                )
            ]
            return types.ServerResult(types.ReadResourceResult(contents=contents))

        async def call_tool_handler(req: types.CallToolRequest) -> types.ServerResult:
            widget = widget_server.widgets_by_id.get(req.params.name)
            result = await _execute_widget_call(widget_server, widget, req)

            if isinstance(result, types.ServerResult):
                return result

            # MCP Apps relies on host rendering the referenced UI resource.
            return types.ServerResult(
                types.CallToolResult(
                    content=[types.TextContent(type="text", text=widget.invoked)],
                    structuredContent=result,
                )
            )

        server.request_handlers[types.ReadResourceRequest] = read_resource_handler
        server.request_handlers[types.CallToolRequest] = call_tool_handler

    def _build_ui_resource(self, widget: BaseWidget) -> types.Resource:
        """Create a Resource describing the UI for MCP Apps."""
        return types.Resource(
            name=widget.title,
            title=widget.title,
            uri=widget.template_uri,
            description=f"{widget.title} widget markup",
            mimeType="text/html+mcp",
            _meta=self._build_ui_meta(widget),
        )

    def _build_ui_meta(self, widget: BaseWidget) -> Dict[str, Any]:
        """Map widget CSP/domain preferences to MCP Apps meta."""
        meta: Dict[str, Any] = {"ui": {}}
        csp: Dict[str, Any] = {}

        widget_csp = widget.widget_csp or {}
        resource_domains = widget_csp.get("resource_domains") or []
        connect_domains = widget_csp.get("connect_domains") or []

        if connect_domains:
            csp["connect_domains"] = connect_domains
        if resource_domains:
            csp["resource_domains"] = resource_domains

        if csp:
            meta["ui"]["csp"] = csp

        if widget.widget_domain:
            meta["ui"]["domain"] = widget.widget_domain
        if widget.widget_prefers_border:
            meta["ui"]["prefersBorder"] = True

        return meta
