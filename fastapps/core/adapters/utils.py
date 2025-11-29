"""Shared helpers for protocol-specific behavior."""

from __future__ import annotations

from typing import Any, Optional, Union

from mcp import types

from fastapps.core.widget import BaseWidget, ClientContext, UserContext


def _inject_protocol_hint(html: str, protocol: str) -> str:
    """
    Inject a small script that exposes the chosen protocol to the UI runtime.

    Args:
        html: Original HTML string
        protocol: One of "openai-apps" or "mcp-apps"

    Returns:
        HTML string with protocol hint injected before </head> or at top.
    """
    hint = f'<script>window.__FASTAPPS_PROTOCOL="{protocol}";</script>'
    if "</head>" in html:
        return html.replace("</head>", f"{hint}</head>", 1)
    return hint + html


def _error_call_tool(message: str) -> types.ServerResult:
    """Create a standardized error response for call_tool failures."""
    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text=message)],
            isError=True,
        )
    )


async def _execute_widget_call(
    widget_server: "WidgetMCPServer",
    widget: Optional[BaseWidget],
    req: types.CallToolRequest,
) -> Union[types.ServerResult, Any]:
    """
    Shared call_tool execution pipeline:
    - Lookup widget
    - Auth inheritance + scope checks
    - Input validation
    - Locale negotiation
    - Context construction
    - Widget execution

    Returns:
        - types.ServerResult on error, or
        - widget.execute(...) result on success
    """
    if not widget:
        return _error_call_tool(f"Unknown tool: {req.params.name}")

    try:
        access_token = None
        if hasattr(req, "context") and hasattr(req.context, "access_token"):
            access_token = req.context.access_token
        elif hasattr(req.params, "_meta"):
            meta_token = req.params._meta.get("access_token")
            if meta_token:
                access_token = meta_token

        widget_requires_auth = getattr(widget, "_auth_required", None)

        if widget_requires_auth is None and widget_server.server_requires_auth:
            widget_requires_auth = True

        if widget_requires_auth is True and not access_token:
            return _error_call_tool("Authentication required for this tool")

        if access_token and hasattr(widget, "_auth_scopes") and widget._auth_scopes:
            user_scopes = getattr(access_token, "scopes", [])
            missing_scopes = set(widget._auth_scopes) - set(user_scopes)

            if missing_scopes:
                return _error_call_tool(
                    f"Missing required scopes: {', '.join(missing_scopes)}"
                )

        arguments = req.params.arguments or {}
        input_data = widget.input_schema.model_validate(arguments)

        meta = req.params._meta if hasattr(req.params, "_meta") else {}
        requested_locale = meta.get("openai/locale") or meta.get("webplus/i18n")
        if requested_locale:
            widget.resolved_locale = widget.negotiate_locale(requested_locale)

        context = ClientContext(meta)
        user = UserContext(access_token)

        return await widget.execute(input_data, context, user)
    except Exception as exc:
        return _error_call_tool(f"Error: {str(exc)}")
