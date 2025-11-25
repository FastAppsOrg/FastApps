"""Shared helper for protocol-specific HTML injections."""

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
