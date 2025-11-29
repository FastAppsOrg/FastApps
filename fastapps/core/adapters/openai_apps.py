"""Default adapter for OpenAI Apps SDK-compatible behavior."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from mcp import types

from fastapps.core.protocol import ProtocolAdapter
from fastapps.core.utils import get_cli_version
from fastapps.core.adapters.utils import _execute_widget_call, _inject_protocol_hint
from fastapps.core.widget import BaseWidget, ClientContext, UserContext

if TYPE_CHECKING:
    from fastapps.core.server import WidgetMCPServer


class OpenAIAppsAdapter(ProtocolAdapter):
    """Implements the legacy/default OpenAI Apps SDK wiring."""

    def register_handlers(self, widget_server: "WidgetMCPServer") -> None:
        """Attach handlers on the given WidgetMCPServer."""
        server = widget_server.mcp._mcp_server

        original_initialize = server.request_handlers.get(types.InitializeRequest)

        async def initialize_handler(
            req: types.InitializeRequest,
        ) -> types.ServerResult:
            meta = req.params._meta if hasattr(req.params, "_meta") else {}
            requested_locale = meta.get("openai/locale") or meta.get("webplus/i18n")

            if requested_locale:
                widget_server.client_locale = requested_locale
                for widget in widget_server.widgets_by_id.values():
                    resolved = widget.negotiate_locale(requested_locale)
                    widget.resolved_locale = resolved

            if original_initialize:
                return await original_initialize(req)

            return types.ServerResult(
                types.InitializeResult(
                    protocolVersion=req.params.protocolVersion,
                    capabilities=types.ServerCapabilities(),
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
                tool_meta = w.get_tool_meta()

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
                meta = w.get_resource_meta()
                resource = types.Resource(
                    name=w.title,
                    title=w.title,
                    uri=w.template_uri,
                    description=f"{w.title} widget markup",
                    mimeType="text/html+skybridge",
                    _meta=meta,
                )
                resources.append(resource)
            return resources

        @server.list_resource_templates()
        async def list_resource_templates_handler() -> List[types.ResourceTemplate]:
            return [
                types.ResourceTemplate(
                    name=w.title,
                    title=w.title,
                    uriTemplate=w.template_uri,
                    description=f"{w.title} widget markup",
                    mimeType="text/html+skybridge",
                    _meta=w.get_resource_meta(),
                )
                for w in widget_server.widgets_by_id.values()
            ]

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

            html = _inject_protocol_hint(widget.build_result.html, "openai-apps")

            contents = [
                types.TextResourceContents(
                    uri=widget.template_uri,
                    mimeType="text/html+skybridge",
                    text=html,
                    _meta=widget.get_resource_meta(),
                )
            ]
            return types.ServerResult(types.ReadResourceResult(contents=contents))

        async def call_tool_handler(req: types.CallToolRequest) -> types.ServerResult:
            widget = widget_server.widgets_by_id.get(req.params.name)
            result = await _execute_widget_call(widget_server, widget, req)

            if isinstance(result, types.ServerResult):
                return result

            widget_resource = widget.get_embedded_resource()
            meta: Dict[str, Any] = {
                "openai.com/widget": widget_resource.model_dump(mode="json"),
                "openai/outputTemplate": widget.template_uri,
                "openai/toolInvocation/invoking": widget.invoking,
                "openai/toolInvocation/invoked": widget.invoked,
                "openai/widgetAccessible": widget.widget_accessible,
                "openai/resultCanProduceWidget": True,
            }

            if widget.resolved_locale:
                meta["openai/locale"] = widget.resolved_locale

            return types.ServerResult(
                types.CallToolResult(
                    content=[types.TextContent(type="text", text=widget.invoked)],
                    structuredContent=result,
                    _meta=meta,
                )
            )

        server.request_handlers[types.ReadResourceRequest] = read_resource_handler
        server.request_handlers[types.CallToolRequest] = call_tool_handler

        self._register_assets_proxy(widget_server)

    def _register_assets_proxy(self, widget_server: "WidgetMCPServer") -> None:
        """Proxy /assets requests to local asset server (same behavior as before)."""
        app = getattr(widget_server.mcp._mcp_server, "http_app", None)
        if app is None:
            app = widget_server.mcp.http_app()

        try:
            from starlette.middleware.cors import CORSMiddleware

            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
                allow_credentials=False,
            )
        except Exception:
            pass

        try:
            import httpx
            from starlette.responses import Response
            from starlette.routing import Route

            async def proxy_assets(request):
                path = request.path_params.get("path", "")
                upstream_url = f"http://127.0.0.1:4444/{path}"

                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        upstream_response = await client.get(upstream_url)

                        allowed_headers = {
                            "content-type",
                            "cache-control",
                            "etag",
                            "last-modified",
                            "content-length",
                        }
                        response_headers = {
                            k: v
                            for k, v in upstream_response.headers.items()
                            if k.lower() in allowed_headers
                        }

                        if "content-type" not in response_headers:
                            response_headers["content-type"] = "application/octet-stream"

                        response_headers["access-control-allow-origin"] = "*"
                        response_headers["access-control-allow-methods"] = "GET, OPTIONS"
                        response_headers["access-control-allow-headers"] = "*"

                        return Response(
                            content=upstream_response.content,
                            status_code=upstream_response.status_code,
                            headers=response_headers,
                        )
                except httpx.RequestError:
                    return Response(
                        content=b"Asset server unavailable",
                        status_code=502,
                        headers={"content-type": "text/plain"},
                    )

            app.routes.append(Route("/assets/{path:path}", proxy_assets, methods=["GET"]))
        except Exception as e:
            # Log error but don't crash
            print(f"Warning: Could not register /assets proxy route: {e}")
            pass
