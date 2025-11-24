"""Create widget command."""

from pathlib import Path
import shutil
import json
import subprocess

from rich.console import Console

console = Console()

# Get templates directory (go up from cli/commands/ to fastapps/)
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


def create_widget(name: str, auth_type: str = None, scopes: list = None, template: str = None):
    """
    Create a new widget with tool and component files.

    Args:
        name: Widget name
        auth_type: Authentication type ('required', 'none', 'optional', or None)
        scopes: List of OAuth scopes
        template: Template type ('list', 'carousel', 'albums', or None for default)
    """

    # Convert name to proper formats
    identifier = name.lower().replace("-", "_").replace(" ", "_")
    class_name = "".join(word.capitalize() for word in identifier.split("_"))
    title = " ".join(word.capitalize() for word in identifier.split("_"))

    # Paths
    tool_dir = Path("server/tools")
    widget_dir = Path("widgets") / identifier

    tool_file = tool_dir / f"{identifier}_tool.py"
    widget_file = widget_dir / "index.jsx"

    # Check if already exists
    if tool_file.exists():
        console.print(f"[yellow][WARNING] Tool already exists: {tool_file}[/yellow]")
        return False

    if widget_file.exists():
        console.print(
            f"[yellow][WARNING] Widget already exists: {widget_file}[/yellow]"
        )
        return False

    # Create directories
    tool_dir.mkdir(parents=True, exist_ok=True)
    widget_dir.mkdir(parents=True, exist_ok=True)

    # Determine template to use
    template_name = template if template else "default"
    template_dir = TEMPLATES_DIR / template_name

    if not template_dir.exists():
        console.print(f"[red]Template directory not found: {template_dir}[/red]")
        return False

    # Copy and customize tool.py
    tool_template_file = template_dir / "tool.py"
    if tool_template_file.exists():
        tool_content = tool_template_file.read_text()
        tool_content = tool_content.replace("{ClassName}", class_name)
        tool_content = tool_content.replace("{identifier}", identifier)
        tool_content = tool_content.replace("{title}", title)

        # Handle auth configuration for default template
        if template_name == "default" and auth_type:
            # Add auth imports and decorators
            if auth_type == "required":
                tool_content = tool_content.replace(
                    "# from fastapps import auth_required, no_auth, optional_auth, UserContext",
                    "from fastapps import auth_required, UserContext"
                )
                scope_str = f"[{', '.join(repr(s) for s in scopes)}]" if scopes else "[]"
                tool_content = tool_content.replace(
                    "# @auth_required(scopes=[\"user\"])\n# Or make it explicitly public:\n# @no_auth\n# Or support both authenticated and anonymous:\n# @optional_auth(scopes=[\"user\"])",
                    f"@auth_required(scopes={scope_str})"
                )
            elif auth_type == "none":
                tool_content = tool_content.replace(
                    "# from fastapps import auth_required, no_auth, optional_auth, UserContext",
                    "from fastapps import no_auth"
                )
                tool_content = tool_content.replace(
                    "# @auth_required(scopes=[\"user\"])\n# Or make it explicitly public:\n# @no_auth\n# Or support both authenticated and anonymous:\n# @optional_auth(scopes=[\"user\"])",
                    "@no_auth"
                )
            elif auth_type == "optional":
                tool_content = tool_content.replace(
                    "# from fastapps import auth_required, no_auth, optional_auth, UserContext",
                    "from fastapps import optional_auth, UserContext"
                )
                scope_str = f"[{', '.join(repr(s) for s in scopes)}]" if scopes else "[]"
                tool_content = tool_content.replace(
                    "# @auth_required(scopes=[\"user\"])\n# Or make it explicitly public:\n# @no_auth\n# Or support both authenticated and anonymous:\n# @optional_auth(scopes=[\"user\"])",
                    f"@optional_auth(scopes={scope_str})"
                )

        tool_file.write_text(tool_content)

    # Copy widget files
    widget_template_dir = template_dir / "widget"
    if widget_template_dir.exists():
        for item in widget_template_dir.iterdir():
            if item.is_file():
                dest_file = widget_dir / item.name
                if item.suffix == ".jsx":
                    # Customize .jsx files with class name
                    content = item.read_text()
                    content = content.replace("{ClassName}", class_name)
                    dest_file.write_text(content)
                else:
                    # Copy other files as-is (like index.css)
                    shutil.copy2(item, dest_file)
            elif item.is_dir():
                # Copy subdirectories (like hooks folder) recursively
                dest_dir = widget_dir / item.name
                shutil.copytree(item, dest_dir, dirs_exist_ok=True)

    # Install dependencies for templates (Apps SDK UI + Tailwind + template extras)
    console.print(f"\n[green][OK] Widget '{name}' created from '{template_name}' template![/green]")

    dep_name = {"list": "List", "carousel": "Carousel", "albums": "Albums"}.get(template_name, "Widget")
    console.print(f"\n[cyan]Installing {dep_name} dependencies...[/cyan]")

    # Check if package.json exists
    package_json_path = Path("package.json")
    if package_json_path.exists():
        try:
            # Read current package.json
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)

            if 'devDependencies' not in package_data:
                package_data['devDependencies'] = {}
            if 'dependencies' not in package_data:
                package_data['dependencies'] = {}

            # Base deps shared across templates (Apps SDK UI + Tailwind 4)
            template_dev_deps = {
                "@tailwindcss/vite": "^4.1.11",
                "autoprefixer": "^10.4.21",
                "postcss": "^8.5.6",
                "tailwindcss": "^4.1.11"
            }
            template_deps = {
                "@openai/apps-sdk-ui": "^0.1.0"
            }

            # Template-specific runtime deps
            if template_name == "list":
                template_deps.update({
                    "lucide-react": "^0.552.0"
                })
            elif template_name == "carousel":
                template_deps.update({
                    "lucide-react": "^0.552.0",
                    "embla-carousel-react": "^8.6.0"
                })
            elif template_name == "albums":
                template_deps.update({
                    "lucide-react": "^0.552.0",
                    "embla-carousel-react": "^8.6.0"
                })

            # Check if dependencies already exist
            deps_to_install = []
            for dep, version in template_dev_deps.items():
                if dep not in package_data['devDependencies']:
                    package_data['devDependencies'][dep] = version
                    deps_to_install.append(dep)

            for dep, version in template_deps.items():
                if dep not in package_data['dependencies']:
                    package_data['dependencies'][dep] = version
                    deps_to_install.append(dep)

            # Write updated package.json
            if deps_to_install:
                with open(package_json_path, 'w') as f:
                    json.dump(package_data, f, indent=2)

                console.print(f"[cyan]Added {len(deps_to_install)} dependencies to package.json[/cyan]")

                # Run npm install
                console.print("[cyan]Running npm install...[/cyan]")
                try:
                    result = subprocess.run(
                        ["npm", "install"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    console.print(f"[green]✓ {dep_name} dependencies installed[/green]")
                except subprocess.CalledProcessError as e:
                    console.print("[yellow]⚠ npm install failed. Run 'npm install' manually[/yellow]")
                except FileNotFoundError:
                    console.print("[yellow]⚠ npm not found. Run 'npm install' manually[/yellow]")
            else:
                console.print(f"[green]✓ {dep_name} dependencies already installed[/green]")

        except Exception as e:
            console.print(f"[yellow]⚠ Could not update package.json: {e}[/yellow]")
            console.print("[yellow]Please install dependencies manually:[/yellow]")
            manual_deps = ["@openai/apps-sdk-ui"]
            if template_name in ["carousel", "albums"]:
                manual_deps.extend(["embla-carousel-react", "lucide-react"])
            elif template_name == "list":
                manual_deps.append("lucide-react")
            console.print(f"[dim]  npm install {' '.join(manual_deps)}[/dim]")
            console.print("[dim]  npm install -D @tailwindcss/vite tailwindcss autoprefixer postcss[/dim]")
    else:
        console.print("[yellow]⚠ package.json not found[/yellow]")
        manual_deps = ["@openai/apps-sdk-ui"]
        if template_name in ["carousel", "albums"]:
            manual_deps.extend(["embla-carousel-react", "lucide-react"])
        elif template_name == "list":
            manual_deps.append("lucide-react")
        console.print("[yellow]Please install dependencies manually:[/yellow]")
        console.print(f"[dim]  npm install {' '.join(manual_deps)}[/dim]")
        console.print("[dim]  npm install -D @tailwindcss/vite tailwindcss autoprefixer postcss[/dim]")

    console.print("\n[green][OK] Widget created successfully![/green]")
    console.print("\n[cyan]Created files:[/cyan]")
    console.print(f"  - {tool_file}")
    console.print(f"  - {widget_file}")
    console.print("\n[yellow]Next steps:[/yellow]")
    console.print("  1. fastapps dev")
    console.print(
        "\n[green]Your widget will be automatically discovered by FastApps![/green]"
    )

    console.print()

    return True
