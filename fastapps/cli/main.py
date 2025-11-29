"""FastApps CLI - Command-line interface for the FastApps framework."""

import click
from rich.console import Console

from fastapps.core.utils import get_cli_version

from .commands.allow_csp import add_csp_domain, list_csp_domains, remove_csp_domain
from .commands.build import build_command
from .commands.create import create_widget
from .commands.dev import start_dev_server
from .commands.init import init_project
from .commands.use import use_integration

console = Console()


@click.group()
@click.version_option(version=get_cli_version(), prog_name="fastapps")
def cli():
    """FastApps - ChatGPT Widget Framework

    Build interactive ChatGPT widgets with zero boilerplate.
    Supports OAuth 2.1 authentication for secure widgets.
    """
    pass


@cli.command()
@click.argument("project_name")
@click.option("--python", help="Python version requirement (e.g., 3.8, 3.9)")
def init(project_name, python):
    """Initialize a new FastApps project.

    Example:
        fastapps init myproject

    Creates a complete project structure with:
    - server/main.py (auto-discovery)
    - server/tools/ (for widget backends)
    - widgets/ (for React components)
    - pyproject.toml (Python dependencies)
    - package.json

    Options:
        --python: Set Python version requirement (e.g., 3.8, 3.9)
    """
    init_project(project_name, python)


@cli.command()
@click.argument("widget_name")
@click.option("--auth", is_flag=True, help="Add auth_required decorator to widget")
@click.option("--public", is_flag=True, help="Add no_auth decorator (public widget)")
@click.option("--optional-auth", is_flag=True, help="Add optional_auth decorator")
@click.option("--scopes", help="OAuth scopes (comma-separated, e.g., 'user,read:data')")
@click.option("--template", type=click.Choice(['list', 'carousel', 'albums'], case_sensitive=False), help="Widget template to use (list, carousel, or albums)")
def create(widget_name, auth, public, optional_auth, scopes, template):
    """Create a new widget with tool and component files.

    Examples:
        fastapps create mywidget
        fastapps create mywidget --auth --scopes user,read:data
        fastapps create mywidget --public
        fastapps create mywidget --optional-auth --scopes user
        fastapps create mywidget --template list
        fastapps create mywidget --template carousel
        fastapps create mywidget --template albums

    Authentication options:
        --auth: Require OAuth authentication
        --public: Mark as public (no auth)
        --optional-auth: Support both authenticated and anonymous
        --scopes: OAuth scopes to require

    Template options:
        --template list: Use the list widget template (includes Tailwind CSS styling)
        --template carousel: Use the carousel widget template (includes Embla Carousel)
        --template albums: Use the albums widget template (includes fullscreen photo viewer)
    """
    # Parse scopes
    scope_list = scopes.split(",") if scopes else None

    # Validate options
    option_count = sum([auth, public, optional_auth])
    if option_count > 1:
        console.print(
            "[red]Error: Only one auth option allowed (--auth, --public, or --optional-auth)[/red]"
        )
        return

    # Determine auth type
    auth_type = None
    if auth:
        auth_type = "required"
    elif public:
        auth_type = "none"
    elif optional_auth:
        auth_type = "optional"

    create_widget(widget_name, auth_type=auth_type, scopes=scope_list, template=template)


@cli.command()
@click.option("--port", default=8001, help="Port to run the server on (default: 8001)")
@click.option(
    "--host", default="0.0.0.0", help="Host to bind the server to (default: 0.0.0.0)"
)
@click.option(
    "--mode",
    type=click.Choice(['inline', 'hosted'], case_sensitive=False),
    default='hosted',
    help="Widget build mode: 'hosted' (default, external JS/CSS on port 4444) or 'inline' (self-contained HTML)"
)
@click.option(
    "--protocol",
    type=click.Choice(['openai-apps', 'mcp-apps', 'auto'], case_sensitive=False),
    default='openai-apps',
    help="UI protocol adapter: OpenAI Apps SDK (default) or MCP Apps extension",
)
def dev(port, host, mode, protocol):
    """Start development server with Cloudflare Tunnel.

    This command will:
    1. Build widgets (inline or hosted mode)
    2. Install cloudflared if needed (automatic, no token required)
    3. Start a public Cloudflare Tunnel
    4. Launch the FastApps development server
    5. Display public and local URLs

    Build modes:
      --mode=hosted   : Widgets reference external JS/CSS from localhost:4444 (default, faster dev, ChatGPT compatible)
      --mode=inline   : Widgets built as self-contained HTML (production-ready)

    Examples:
        fastapps dev                    # Hosted mode (default)
        fastapps dev --mode=inline      # Inline mode (self-contained)
        fastapps dev --port 8080        # Custom port

    Note: Uses Cloudflare Tunnel (free, unlimited, no sign-up required)
    """
    start_dev_server(port=port, host=host, mode=mode, protocol=protocol)


@cli.command()
def build():
    """Build widgets for production."""
    build_command()

@cli.command()
def auth_info():
    """Show authentication setup information."""
    console.print("\n[bold cyan]FastApps Authentication Guide[/bold cyan]")
    console.print("\n[yellow]Server-Wide Auth:[/yellow]")
    console.print("  Configure in server/main.py:")
    console.print("  [dim]server = WidgetMCPServer([/dim]")
    console.print("  [dim]    name='my-widgets',[/dim]")
    console.print("  [dim]    widgets=tools,[/dim]")
    console.print("  [dim]    auth_issuer_url='https://tenant.auth0.com',[/dim]")
    console.print(
        "  [dim]    auth_resource_server_url='https://example.com/mcp',[/dim]"
    )
    console.print("  [dim]    auth_required_scopes=['user'],[/dim]")
    console.print("  [dim])[/dim]")

    console.print("\n[yellow]Per-Widget Auth:[/yellow]")
    console.print("  Create authenticated widget:")
    console.print(
        "  [dim]$ fastapps create mywidget --auth --scopes user,read:data[/dim]"
    )
    console.print("\n  Create public widget:")
    console.print("  [dim]$ fastapps create mywidget --public[/dim]")
    console.print("\n  Create optional auth widget:")
    console.print(
        "  [dim]$ fastapps create mywidget --optional-auth --scopes user[/dim]"
    )

    console.print("\n[yellow]Decorators:[/yellow]")
    console.print(
        "  [green]@auth_required[/green](scopes=['user']) - Require authentication"
    )
    console.print("  [green]@no_auth[/green] - Public widget (opt-out)")
    console.print("  [green]@optional_auth[/green](scopes=['user']) - Works both ways")

    console.print("\n[yellow]UserContext:[/yellow]")
    console.print("  Access authenticated user in execute():")
    console.print("  [dim]async def execute(self, input_data, context, user):[/dim]")
    console.print("  [dim]    if user.is_authenticated:[/dim]")
    console.print("  [dim]        return {'user_id': user.subject}[/dim]")
    console.print()


@cli.command()
@click.argument("integration_name")
def use(integration_name):
    """Add integrations to your FastApps project.

    Notes:
        • Run this from a FastApps project root containing pyproject.toml
        • Manage Python dependencies with uv (`uv add ...` followed by `uv sync`)

    Available integrations:
        metorial - Add Metorial MCP integration for querying data sources

    Example:
        fastapps use metorial

    This will create server/api/metorial_mcp.py with environment variable support.
    """
    use_integration(integration_name)


# CSP management command group
@cli.group()
def csp():
    """Manage Content Security Policy (CSP) for widgets.

    Configure domains allowed to load external resources (scripts, styles, images)
    and make API calls (fetch, XHR) from your widgets.

    All CSP configuration is stored in fastapps.json and automatically
    loaded when creating WidgetMCPServer.
    """
    pass


@csp.command("add")
@click.option("--url", help="Domain URL to allow (e.g., https://example.com)")
@click.option(
    "--type",
    "domain_type",
    type=click.Choice(["resource", "connect"], case_sensitive=False),
    help="Domain type: 'resource' for assets, 'connect' for APIs",
)
def csp_add(url, domain_type):
    """Add a domain to CSP allowlist.

    Examples:
        fastapps csp add --url https://pub-YOUR-ID.r2.dev --type resource
        fastapps csp add --url https://api.example.com --type connect
        fastapps csp add  # Interactive mode

    Domain types:
        resource - For scripts, styles, images, fonts (e.g., CDN, R2 buckets)
        connect  - For API calls via fetch/XHR (e.g., external APIs)
    """
    add_csp_domain(url=url, domain_type=domain_type)


@csp.command("remove")
@click.option("--url", help="Domain URL to remove")
@click.option(
    "--type",
    "domain_type",
    type=click.Choice(["resource", "connect"], case_sensitive=False),
    help="Domain type: 'resource' or 'connect'",
)
def csp_remove(url, domain_type):
    """Remove a domain from CSP allowlist.

    Examples:
        fastapps csp remove --url https://example.com --type resource
        fastapps csp remove  # Interactive mode
    """
    remove_csp_domain(url=url, domain_type=domain_type)


@csp.command("list")
def csp_list():
    """List all configured CSP domains.

    Shows currently configured resource and connect domains
    from fastapps.json.
    """
    list_csp_domains()


if __name__ == "__main__":
    cli()
