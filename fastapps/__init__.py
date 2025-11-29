"""
FastApps - ChatGPT Widget Framework

A zero-boilerplate framework for building interactive ChatGPT widgets.

Example:
    from fastapps import BaseWidget, Field
    from typing import Dict, Any

    class MyWidget(BaseWidget):
        identifier = "my_widget"
        title = "My Widget"

        async def execute(self, input_data) -> Dict[str, Any]:
            return {"message": "Hello from FastApps!"}
"""

__author__ = "FastApps Team"

from .builder.compiler import WidgetBuilder, WidgetBuildResult
from .core.protocol import ProtocolAdapter
from .core.adapters.openai_apps import OpenAIAppsAdapter
from .core.adapters.mcp_apps import MCPAppsAdapter
from .core.adapters.auto import AutoProtocolAdapter
from .core.server import WidgetMCPServer
from .core.widget import BaseWidget, ClientContext, UserContext
from .types.schema import ConfigDict, Field

# Auth exports (optional, graceful if not available)
try:
    from .auth import AccessToken, TokenVerifier
    from .auth.decorators import auth_required, no_auth, optional_auth
    from .auth.verifier import JWTVerifier

    _auth_exports = [
        "JWTVerifier",
        "TokenVerifier",
        "AccessToken",
        "auth_required",
        "no_auth",
        "optional_auth",
    ]
except ImportError:
    _auth_exports = []

__all__ = [
    # Core classes
    "BaseWidget",
    "ClientContext",
    "UserContext",
    "WidgetMCPServer",
    "ProtocolAdapter",
    "OpenAIAppsAdapter",
    "MCPAppsAdapter",
    "AutoProtocolAdapter",
    "WidgetBuilder",
    "WidgetBuildResult",
    "Field",
    "ConfigDict",
] + _auth_exports
