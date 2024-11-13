#!/usr/bin/env python3
"""
Dependency Management Script for Document Processing Platform.

This script helps manage dependencies, check for updates, and maintain compatibility
across different processors.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pkg_resources
from rich.console import Console
from rich.table import Table

console = Console()

def get_installed_packages() -> Dict[str, str]:
    """Get all installed packages and their versions."""
    return {
        pkg.key: pkg.version
        for pkg in pkg_resources.working_set
    }

def check_updates() -> List[Tuple[str, str, str]]:
    """Check for available package updates."""
    result = subprocess.run(
        ["poetry", "show", "--outdated", "--json"],
        capture_output=True,
        text=True
    )
    updates = []
    try:
        packages = json.loads(result.stdout)
        for pkg in packages:
            updates.append((
                pkg["name"],
                pkg["version"],
                pkg["latest"]
            ))
    except json.JSONDecodeError:
        console.print("[red]Error parsing poetry output[/red]")
    return updates

def check_compatibility(package: str, version: str) -> bool:
    """Check if a package version is compatible with current setup."""
    result = subprocess.run(
        ["poetry", "add", f"{package}@{version}", "--dry-run"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def generate_dependency_report(output_file: Optional[Path] = None) -> None:
    """Generate a detailed dependency report."""
    # Get current state
    installed = get_installed_packages()
    updates = check_updates()
    
    # Create report table
    table = Table(title="Dependency Status Report")
    table.add_column("Package")
    table.add_column("Current Version")
    table.add_column("Latest Version")
    table.add_column("Status")
    
    for name, current, latest in updates:
        status = "✓ Up to date" if current == latest else "⟳ Update available"
        color = "green" if current == latest else "yellow"
        table.add_row(name, current, latest, f"[{color}]{status}[/{color}]")
    
    # Display report
    console.print(table)
    
    if output_file:
        # Save report
        report = {
            "timestamp": datetime.now().isoformat(),
            "packages": [
                {
                    "name": name,
                    "current": current,
                    "latest": latest,
                    "needs_update": current != latest
                }
                for name, current, latest in updates
            ]
        }
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        console.print(f"\nReport saved to: {output_file}")

def update_readme_status() -> None:
    """Update dependency status in README.md."""
    readme_path = Path("README.md")
    if not readme_path.exists():
        console.print("[red]README.md not found[/red]")
        return
    
    # Get current status
    installed = get_installed_packages()
    updates = check_updates()
    
    # Create status section
    status_section = [
        "## Dependency Status (Updated: {})".format(
            datetime.now().strftime("%Y-%m-%d")
        ),
        "",
        "### Core Dependencies",
        "| Package | Version | Status |",
        "|---------|---------|--------|",
    ]
    
    for name, current, latest in updates:
        status = "✓ Up to date" if current == latest else "⟳ Update available"
        status_section.append(f"| {name} | {current} | {status} |")
    
    # Read current README
    content = readme_path.read_text()
    
    # Find status section
    start_marker = "## Dependency Status"
    end_marker = "##"
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        # Add at the end
        content += "\n\n" + "\n".join(status_section)
    else:
        # Find next section
        end_idx = content.find(end_marker, start_idx + len(start_marker))
        if end_idx == -1:
            end_idx = len(content)
        
        # Replace section
        content = (
            content[:start_idx] +
            "\n".join(status_section) +
            "\n\n" +
            content[end_idx:]
        )
    
    # Save updated README
    readme_path.write_text(content)
    console.print("[green]Updated dependency status in README.md[/green]")

def main() -> None:
    """Run dependency management tasks."""
    console.print("\n[bold]Document Processing Platform - Dependency Management[/bold]\n")
    
    # Generate report
    report_path = Path("reports/dependencies") / f"dependency_report_{datetime.now().strftime('%Y%m%d')}.json"
    generate_dependency_report(report_path)
    
    # Update README
    update_readme_status()
    
    # Show summary
    console.print("\n[green]Dependency management tasks completed:[/green]")
    console.print(f"1. Generated dependency report: {report_path}")
    console.print("2. Updated README.md with current status")

if __name__ == "__main__":
    main()