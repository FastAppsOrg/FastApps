from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from mcp import types

from fastapps.core.utils import get_cli_version
from .protocol import ProtocolAdapter

from .widget import BaseWidget, ClientContext, UserContext

# Auth imports (optional, graceful degradation if not available)
try:
    from mcp.server.auth.provider import TokenVerifier
    from mcp.server.auth.settings import AuthSettings

    MCP_AUTH_AVAILABLE = True
except ImportError:
    MCP_AUTH_AVAILABLE = False
    AuthSettings = None
    TokenVerifier = None


class WidgetMCPServer:
    """
    FastMCP-based MCP server with widget metadata support.

    Handles tool registration, resource templates, and widget execution.
    Supports optional OAuth 2.1 authentication.
    """

    def __init__(
        self,
        name: str,
        widgets: List[BaseWidget],
        # OAuth 2.1 authentication parameters (optional)
        adapter: Optional[ProtocolAdapter] = None,
        auth_issuer_url: Optional[str] = None,
        auth_resource_server_url: Optional[str] = None,
        auth_required_scopes: Optional[List[str]] = None,
        auth_audience: Optional[str] = None,
        token_verifier: Optional["TokenVerifier"] = None,
        # Global CSP configuration for all widgets (optional)
        global_resource_domains: Optional[List[str]] = None,
        global_connect_domains: Optional[List[str]] = None,
    ):
        """
        Initialize MCP server with optional OAuth authentication and global CSP.

        Args:
            name: Server name
            widgets: List of widget instances
            adapter: Optional protocol adapter for UI variants (default: built-in OpenAI Apps behavior)
            auth_issuer_url: OAuth issuer URL (e.g., https://tenant.auth0.com)
            auth_resource_server_url: Your MCP server URL (e.g., https://example.com/mcp)
            auth_required_scopes: Required OAuth scopes (e.g., ["user", "read:data"])
            auth_audience: JWT audience claim (optional)
            token_verifier: Custom TokenVerifier (optional, uses JWTVerifier if not provided)
            global_resource_domains: Domains to allow for all widgets (scripts, styles, images)
            global_connect_domains: Domains to allow for API calls (fetch, XHR)

        Example (Simple):
            server = WidgetMCPServer(
                name="my-widgets",
                widgets=tools,
                auth_issuer_url="https://tenant.auth0.com",
                auth_resource_server_url="https://example.com/mcp",
                auth_required_scopes=["user"],
            )

        Example (With Global CSP):
            server = WidgetMCPServer(
                name="my-widgets",
                widgets=tools,
                global_resource_domains=[
                    "https://pub-YOUR-BUCKET-ID.r2.dev",  # R2 images
                    "https://fonts.googleapis.com",       # Google Fonts
                ],
                global_connect_domains=[
                    "https://api.example.com",  # External API
                ],
            )

        Example (Custom Verifier):
            server = WidgetMCPServer(
                name="my-widgets",
                widgets=tools,
                auth_issuer_url="https://tenant.auth0.com",
                auth_resource_server_url="https://example.com/mcp",
                token_verifier=MyCustomVerifier(),
            )
        """
        self.widgets_by_id = {w.identifier: w for w in widgets}
        self.widgets_by_uri = {w.template_uri: w for w in widgets}
        self.client_locale: Optional[str] = None

        # Optional protocol adapter (e.g., MCP Apps); default behavior remains intact
        self.adapter: Optional[ProtocolAdapter] = None

        # Store global CSP configuration
        self.global_resource_domains = global_resource_domains or []
        self.global_connect_domains = global_connect_domains or []

        # Auto-configure widget CSP based on PUBLIC_URL and global settings
        self._configure_widget_csp(widgets)

        # Store server auth configuration for per-widget inheritance
        self.server_requires_auth = bool(auth_issuer_url and auth_resource_server_url)
        self.server_auth_scopes = auth_required_scopes or []
        self.token_verifier_instance = None

        # Configure authentication if provided
        auth_settings = None
        verifier = token_verifier

        if auth_issuer_url and auth_resource_server_url:
            if not MCP_AUTH_AVAILABLE:
                raise ImportError(
                    "FastMCP auth support not available. "
                    "Please upgrade fastmcp: pip install --upgrade fastmcp or uv pip install --upgrade fastmcp"
                )

            # Use built-in JWTVerifier if no custom verifier provided
            if verifier is None:
                from ..auth.verifier import JWTVerifier

                verifier = JWTVerifier(
                    issuer_url=auth_issuer_url,
                    audience=auth_audience,
                    required_scopes=auth_required_scopes or [],
                )

            # Create AuthSettings for FastMCP
            auth_settings = AuthSettings(
                issuer_url=auth_issuer_url,
                resource_server_url=auth_resource_server_url,
                required_scopes=auth_required_scopes or [],
            )

            # Store verifier for per-widget validation
            self.token_verifier_instance = verifier

        # Initialize FastMCP with or without auth
        fastmcp_kwargs: Dict[str, Any] = {"name": name, "stateless_http": True}
        if auth_settings:
            fastmcp_kwargs.update({"token_verifier": verifier, "auth": auth_settings})
        self.mcp = FastMCP(**fastmcp_kwargs)

        # Use adapter if provided; otherwise fall back to built-in OpenAI Apps behavior
        if adapter:
            if not isinstance(adapter, ProtocolAdapter):
                raise TypeError("adapter must implement ProtocolAdapter")
            self.adapter = adapter
        else:
            from .adapters.openai_apps import OpenAIAppsAdapter

            self.adapter = OpenAIAppsAdapter()

        self.adapter.register_handlers(self)

    def _configure_widget_csp(self, widgets: List[BaseWidget]):
        """
        Auto-configure widget CSP based on:
        1. PUBLIC_URL environment variable
        2. Global CSP domains (global_resource_domains, global_connect_domains)
        3. Widget-specific CSP (widget.widget_csp)
        """
        import os

        public_url = os.environ.get("PUBLIC_URL", "").strip()

        # Configure CSP for all widgets
        for widget in widgets:
            # Initialize CSP if not present
            if widget.widget_csp is None:
                widget.widget_csp = {
                    "resource_domains": [],
                    "connect_domains": []
                }

            # Get existing domains
            resource_domains = widget.widget_csp.get("resource_domains", [])
            connect_domains = widget.widget_csp.get("connect_domains", [])

            # Merge PUBLIC_URL
            if public_url and public_url not in resource_domains:
                resource_domains.append(public_url)

            # Merge global resource domains
            for domain in self.global_resource_domains:
                if domain not in resource_domains:
                    resource_domains.append(domain)

            # Merge global connect domains
            for domain in self.global_connect_domains:
                if domain not in connect_domains:
                    connect_domains.append(domain)

            # Update widget CSP
            widget.widget_csp["resource_domains"] = resource_domains
            widget.widget_csp["connect_domains"] = connect_domains

    def _register_handlers(self):
        """Register all MCP handlers for widget support."""
        server = self.mcp._mcp_server

        # Handle MCP initialization to negotiate locale
        original_initialize = server.request_handlers.get(types.InitializeRequest)

        async def initialize_handler(
            req: types.InitializeRequest,
        ) -> types.ServerResult:
            # Extract requested locale from _meta
            meta = req.params._meta if hasattr(req.params, "_meta") else {}
            requested_locale = meta.get("openai/locale") or meta.get("webplus/i18n")

            # Negotiate locale with each widget
            if requested_locale:
                self.client_locale = requested_locale
                for widget in self.widgets_by_id.values():
                    resolved = widget.negotiate_locale(requested_locale)
                    widget.resolved_locale = resolved

            # Call original handler if it exists
            if original_initialize:
                return await original_initialize(req)

            # Default response if no original handler
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
            for w in self.widgets_by_id.values():
                tool_meta = w.get_tool_meta()

                # Per MCP spec: "Missing field: inherit server default policy"
                # If widget doesn't have explicit securitySchemes and server has auth,
                # inherit server's auth requirement
                if "securitySchemes" not in tool_meta and self.server_requires_auth:
                    tool_meta["securitySchemes"] = [
                        {"type": "oauth2", "scopes": self.server_auth_scopes}
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
            for w in self.widgets_by_id.values():
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
                for w in self.widgets_by_id.values()
            ]

        async def read_resource_handler(
            req: types.ReadResourceRequest,
        ) -> types.ServerResult:
            widget = self.widgets_by_uri.get(str(req.params.uri))
            if not widget:
                return types.ServerResult(
                    types.ReadResourceResult(
                        contents=[],
                        _meta={"error": f"Unknown resource: {req.params.uri}"},
                    )
                )

            contents = [
                types.TextResourceContents(
                    uri=widget.template_uri,
                    mimeType="text/html+skybridge",
                    text=widget.build_result.html,
                    _meta=widget.get_resource_meta(),
                )
            ]
            return types.ServerResult(types.ReadResourceResult(contents=contents))

        async def call_tool_handler(req: types.CallToolRequest) -> types.ServerResult:
            widget = self.widgets_by_id.get(req.params.name)
            if not widget:
                return types.ServerResult(
                    types.CallToolResult(
                        content=[
                            types.TextContent(
                                type="text", text=f"Unknown tool: {req.params.name}"
                            )
                        ],
                        isError=True,
                    )
                )

            try:
                # Extract verified access token
                # FastMCP verifies token before this handler if auth is enabled
                access_token = None
                if hasattr(req, "context") and hasattr(req.context, "access_token"):
                    access_token = req.context.access_token
                elif hasattr(req.params, "_meta"):
                    # Fallback: check _meta for token info
                    meta_token = req.params._meta.get("access_token")
                    if meta_token:
                        access_token = meta_token

                # Determine if auth is required for this widget
                widget_requires_auth = getattr(widget, "_auth_required", None)

                # Per MCP spec: Inheritance - widget without decorator inherits server policy
                if widget_requires_auth is None and self.server_requires_auth:
                    widget_requires_auth = True

                # Per MCP spec: "Servers must enforce regardless of client hints"
                if widget_requires_auth is True and not access_token:
                    return types.ServerResult(
                        types.CallToolResult(
                            content=[
                                types.TextContent(
                                    type="text",
                                    text="Authentication required for this tool",
                                )
                            ],
                            isError=True,
                        )
                    )

                # Enforce widget-specific scope requirements
                if (
                    access_token
                    and hasattr(widget, "_auth_scopes")
                    and widget._auth_scopes
                ):
                    user_scopes = getattr(access_token, "scopes", [])
                    missing_scopes = set(widget._auth_scopes) - set(user_scopes)

                    if missing_scopes:
                        return types.ServerResult(
                            types.CallToolResult(
                                content=[
                                    types.TextContent(
                                        type="text",
                                        text=f"Missing required scopes: {', '.join(missing_scopes)}",
                                    )
                                ],
                                isError=True,
                            )
                        )

                # Validate input
                arguments = req.params.arguments or {}
                input_data = widget.input_schema.model_validate(arguments)

                # Extract client context from request metadata
                meta = req.params._meta if hasattr(req.params, "_meta") else {}

                # Re-negotiate locale if provided in this request
                requested_locale = meta.get("openai/locale") or meta.get("webplus/i18n")
                if requested_locale:
                    widget.resolved_locale = widget.negotiate_locale(requested_locale)

                # Create contexts
                context = ClientContext(meta)
                user = UserContext(access_token)

                # Call execute with user context
                result_data = await widget.execute(input_data, context, user)
            except Exception as exc:
                return types.ServerResult(
                    types.CallToolResult(
                        content=[
                            types.TextContent(type="text", text=f"Error: {str(exc)}")
                        ],
                        isError=True,
                    )
                )

            widget_resource = widget.get_embedded_resource()
            meta: Dict[str, Any] = {
                "openai.com/widget": widget_resource.model_dump(mode="json"),
                "openai/outputTemplate": widget.template_uri,
                "openai/toolInvocation/invoking": widget.invoking,
                "openai/toolInvocation/invoked": widget.invoked,
                "openai/widgetAccessible": widget.widget_accessible,
                "openai/resultCanProduceWidget": True,
            }

            # Add resolved locale to response
            if widget.resolved_locale:
                meta["openai/locale"] = widget.resolved_locale

            return types.ServerResult(
                types.CallToolResult(
                    content=[types.TextContent(type="text", text=widget.invoked)],
                    structuredContent=result_data,
                    _meta=meta,
                )
            )

        server.request_handlers[types.ReadResourceRequest] = read_resource_handler
        server.request_handlers[types.CallToolRequest] = call_tool_handler

    def get_app(self):
        """Get FastAPI app with CORS enabled and /assets proxy."""
        app = self.mcp.http_app()

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

        # Add /assets proxy route to forward requests to local asset server
        # This eliminates CORS/PNA/mixed content issues by serving assets from the same origin
        try:
            import httpx
            from starlette.responses import Response
            from starlette.routing import Route

            async def proxy_assets(request):
                """Proxy asset requests to local asset server (port 4444)."""
                # Extract path from request
                path = request.path_params.get('path', '')
                upstream_url = f"http://127.0.0.1:4444/{path}"

                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        # Forward the request to the asset server
                        upstream_response = await client.get(upstream_url)

                        # Filter headers to only include content-related ones
                        allowed_headers = {
                            "content-type", "cache-control", "etag",
                            "last-modified", "content-length"
                        }
                        response_headers = {
                            k: v for k, v in upstream_response.headers.items()
                            if k.lower() in allowed_headers
                        }

                        # Ensure content-type is set
                        if "content-type" not in response_headers:
                            response_headers["content-type"] = "application/octet-stream"

                        # Add CORS headers for cross-origin access
                        response_headers["access-control-allow-origin"] = "*"
                        response_headers["access-control-allow-methods"] = "GET, OPTIONS"
                        response_headers["access-control-allow-headers"] = "*"

                        return Response(
                            content=upstream_response.content,
                            status_code=upstream_response.status_code,
                            headers=response_headers
                        )
                except httpx.RequestError:
                    return Response(
                        content=b"Asset server unavailable",
                        status_code=502,
                        headers={"content-type": "text/plain"}
                    )

            # Add route to Starlette app
            app.routes.append(
                Route("/assets/{path:path}", proxy_assets, methods=["GET"])
            )
        except Exception as e:
            # Log error but don't crash
            print(f"Warning: Could not register /assets proxy route: {e}")
            pass

        return app
