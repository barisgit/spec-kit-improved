#!/usr/bin/env python3
"""
Comprehensive Template Permutation Audit Script

This script generates all possible AI assistant × template combinations for auditing
and testing. It helps ensure template consistency across different assistants and
provides detailed comparison reports.

Features:
- Uses the assistant registry to get all registered assistants
- Renders all templates with each assistant's injection values
- Generates comparison reports showing differences between assistants
- CLI interface with options for specific assistants or full audit
- Realistic project data for template rendering
- Performance tracking and error reporting

Usage:
    python scripts/audit_templates.py --all                    # Full audit
    python scripts/audit_templates.py --assistant claude       # Single assistant
    python scripts/audit_templates.py --assistant claude gemini # Multiple assistants
    python scripts/audit_templates.py --template specify.md    # Single template
    python scripts/audit_templates.py --clean                  # Clean output directory
"""

import argparse
import json
import logging
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from specify_cli.assistants import list_assistant_names, registry
from specify_cli.models.config import BranchNamingConfig
from specify_cli.models.project import TemplateContext
from specify_cli.services.template_service import JinjaTemplateService


class TemplateAuditor:
    """Main class for template auditing and comparison."""

    def __init__(self, output_dir: Path = Path("audit/templates")):
        """Initialize the auditor with output directory."""
        self.output_dir = output_dir
        self.console = Console()
        self.template_service = JinjaTemplateService()
        self.audit_results: Dict[str, Dict[str, str]] = {}
        self.errors: List[str] = []

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        logging.basicConfig(
            level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def get_realistic_test_context(self, ai_assistant: str) -> TemplateContext:
        """Create realistic test context for template rendering."""
        return TemplateContext(
            project_name="example-project",
            project_description="A sample project for testing SpecifyX templates",
            project_path=Path("/path/to/example-project"),
            branch_name="feature/user-authentication",
            feature_name="user-authentication",
            task_name="implement-login-system",
            author_name="Developer Name",
            author_email="developer@example.com",
            creation_date=datetime.now().strftime("%Y-%m-%d"),
            creation_year=str(datetime.now().year),
            ai_assistant=ai_assistant,
            branch_naming_config=BranchNamingConfig(
                patterns=["feature/{feature-name}", "hotfix/{bug-id}", "main"]
            ),
            config_directory=".specify",
            template_variables={
                "test_variable": "test_value",
                "example_data": "sample content",
            },
            custom_fields={"custom_field": "custom_value"},
        )

    def discover_assistants(
        self, assistant_names: Optional[List[str]] = None
    ) -> List[str]:
        """Discover available assistants."""
        all_assistants = list_assistant_names()

        if assistant_names:
            # Validate requested assistants
            invalid_assistants = set(assistant_names) - set(all_assistants)
            if invalid_assistants:
                raise ValueError(f"Unknown assistants: {', '.join(invalid_assistants)}")
            return assistant_names

        return all_assistants

    def discover_templates(
        self, template_names: Optional[List[str]] = None
    ) -> List[str]:
        """Discover available templates."""
        all_templates = self.template_service.discover_templates()
        template_name_list = [t.name for t in all_templates]

        if template_names:
            # Validate requested templates
            invalid_templates = set(template_names) - set(template_name_list)
            if invalid_templates:
                raise ValueError(f"Unknown templates: {', '.join(invalid_templates)}")
            return template_names

        return template_name_list

    def render_template_for_assistant(
        self, template_name: str, assistant_name: str, context: TemplateContext
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Render a single template for a specific assistant.

        Returns:
            (success, content, error_message)
        """
        try:
            rendered_content = self.template_service.render_template(
                template_name, context
            )
            return True, rendered_content, None
        except Exception as e:
            error_msg = (
                f"Failed to render {template_name} for {assistant_name}: {str(e)}"
            )
            self.errors.append(error_msg)
            return False, "", error_msg

    def audit_single_assistant(
        self, assistant_name: str, template_names: List[str]
    ) -> Dict[str, str]:
        """Audit all templates for a single assistant."""
        results = {}
        context = self.get_realistic_test_context(assistant_name)

        # Create assistant output directory
        assistant_dir = self.output_dir / assistant_name
        assistant_dir.mkdir(exist_ok=True)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                f"Auditing {assistant_name}...", total=len(template_names)
            )

            for template_name in template_names:
                success, content, error = self.render_template_for_assistant(
                    template_name, assistant_name, context
                )

                if success:
                    # Write rendered template to file
                    output_file = assistant_dir / f"{template_name}"
                    if not output_file.suffix:
                        output_file = assistant_dir / f"{template_name}.md"

                    output_file.write_text(content, encoding="utf-8")
                    results[template_name] = str(output_file)

                    self.console.print(
                        f"Rendered {assistant_name}/{template_name}", style="green"
                    )
                else:
                    self.console.print(
                        f"Failed {assistant_name}/{template_name}: {error}", style="red"
                    )
                    results[template_name] = f"ERROR: {error}"

                progress.advance(task)

        return results

    def generate_comparison_report(
        self,
        audit_results: Dict[str, Dict[str, str]],
        assistant_names: List[str],
        template_names: List[str],
    ) -> None:
        """Generate a comprehensive comparison report."""
        report_path = self.output_dir / "comparison-report.md"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Template Permutation Audit Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Assistants:** {', '.join(assistant_names)}\n")
            f.write(f"**Templates:** {len(template_names)}\n")
            f.write(
                f"**Total Combinations:** {len(assistant_names) * len(template_names)}\n\n"
            )

            # Summary table
            f.write("## Summary\n\n")
            f.write("| Assistant | Templates Rendered | Errors |\n")
            f.write("|-----------|-------------------|--------|\n")

            for assistant in assistant_names:
                if assistant in audit_results:
                    results = audit_results[assistant]
                    successful = sum(
                        1 for r in results.values() if not r.startswith("ERROR:")
                    )
                    errors = len(results) - successful
                    f.write(
                        f"| {assistant} | {successful}/{len(results)} | {errors} |\n"
                    )
                else:
                    f.write(f"| {assistant} | 0/0 | N/A |\n")

            f.write("\n")

            # Template analysis
            f.write("## Template Analysis\n\n")
            for template_name in template_names:
                f.write(f"### {template_name}\n\n")

                # Check which assistants successfully rendered this template
                successful_assistants = []
                failed_assistants = []

                for assistant in assistant_names:
                    if (
                        assistant in audit_results
                        and template_name in audit_results[assistant]
                    ):
                        result = audit_results[assistant][template_name]
                        if result.startswith("ERROR:"):
                            failed_assistants.append((assistant, result))
                        else:
                            successful_assistants.append(assistant)

                f.write(
                    f"**Successful renders:** {', '.join(successful_assistants) if successful_assistants else 'None'}\n\n"
                )

                if failed_assistants:
                    f.write("**Failed renders:**\n")
                    for assistant, error in failed_assistants:
                        f.write(f"- {assistant}: {error}\n")
                    f.write("\n")

                # Add injection point differences analysis
                if len(successful_assistants) > 1:
                    f.write("**Injection Point Differences:**\n")
                    self._analyze_injection_differences(
                        f, template_name, successful_assistants
                    )
                    f.write("\n")

            # Error summary
            if self.errors:
                f.write("## Errors\n\n")
                for error in self.errors:
                    f.write(f"- {error}\n")
                f.write("\n")

            # Files generated
            f.write("## Generated Files\n\n")
            for assistant in assistant_names:
                assistant_dir = self.output_dir / assistant
                if assistant_dir.exists():
                    f.write(f"### {assistant}\n\n")
                    for file_path in sorted(assistant_dir.glob("*")):
                        relative_path = file_path.relative_to(self.output_dir)
                        f.write(f"- `{relative_path}`\n")
                    f.write("\n")

        self.console.print(
            f"Comparison report generated: {report_path}", style="blue"
        )

    def _analyze_injection_differences(
        self, f, template_name: str, assistant_names: List[str]
    ) -> None:
        """Analyze injection point differences between assistants for a template."""
        _ = template_name
        
        # Get injection values for each assistant
        injection_data = {}
        for assistant_name in assistant_names:
            assistant = registry.get_assistant(assistant_name)
            if assistant:
                injection_data[assistant_name] = assistant.get_injection_values()

        if not injection_data:
            f.write("No injection data available.\n")
            return

        # Find all injection points used across assistants
        all_points = set()
        for injections in injection_data.values():
            all_points.update(injections.keys())

        # Compare values for each injection point
        differences_found = False
        for point in sorted(all_points, key=lambda x: x.value):
            values = {}
            for assistant_name in assistant_names:
                if assistant_name in injection_data:
                    injections = injection_data[assistant_name]
                    values[assistant_name] = injections.get(point, "NOT_SET")

            # Check if values differ
            unique_values = set(values.values())
            if len(unique_values) > 1:
                differences_found = True
                f.write(f"- **{point.value}:**\n")
                for assistant_name, value in values.items():
                    value_str = str(value)
                    if ("\n" in value_str) or ("`" in value_str):
                        f.write(f"  - {assistant_name}:\n")
                        f.write("``````\n")
                        f.write(value_str)
                        f.write("\n``````\n")
                    else:
                        f.write(f"  - {assistant_name}: `{value_str}`\n")

        if not differences_found:
            f.write("No significant differences in injection points.\n")

    def generate_json_report(self, audit_results: Dict[str, Dict[str, str]]) -> None:
        """Generate a machine-readable JSON report."""
        json_path = self.output_dir / "audit-results.json"

        # Prepare data for JSON export
        json_data = {
            "timestamp": datetime.now().isoformat(),
            "assistants": list(audit_results.keys()),
            "templates": list(
                set().union(*[results.keys() for results in audit_results.values()])
            ),
            "results": audit_results,
            "errors": self.errors,
            "summary": {
                "total_combinations": sum(
                    len(results) for results in audit_results.values()
                ),
                "successful_renders": sum(
                    1
                    for results in audit_results.values()
                    for result in results.values()
                    if not result.startswith("ERROR:")
                ),
                "failed_renders": len(self.errors),
            },
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        self.console.print(f"JSON report generated: {json_path}", style="blue")

    def run_audit(
        self,
        assistant_names: Optional[List[str]] = None,
        template_names: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, str]]:
        """Run the complete audit process."""
        start_time = time.time()

        try:
            # Discover assistants and templates
            assistants = self.discover_assistants(assistant_names)
            templates = self.discover_templates(template_names)

            # Ensure a clean output directory before starting
            if self.output_dir.exists():
                shutil.rmtree(self.output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)

            self.console.print(
                f"Starting audit with {len(assistants)} assistants and {len(templates)} templates"
            )

            audit_results = {}

            # Audit each assistant
            for assistant_name in assistants:
                results = self.audit_single_assistant(assistant_name, templates)
                audit_results[assistant_name] = results

            # Generate reports
            self.generate_comparison_report(audit_results, assistants, templates)
            self.generate_json_report(audit_results)

            # Summary
            elapsed_time = time.time() - start_time
            total_combinations = len(assistants) * len(templates)
            successful_renders = sum(
                1
                for results in audit_results.values()
                for result in results.values()
                if not result.startswith("ERROR:")
            )

            self.console.print(f"\nAudit completed in {elapsed_time:.2f} seconds")
            self.console.print(
                f"{successful_renders}/{total_combinations} templates rendered successfully"
            )

            if self.errors:
                self.console.print(
                    f"{len(self.errors)} errors encountered", style="yellow"
                )

            return audit_results

        except Exception as e:
            self.console.print(f"Audit failed: {str(e)}", style="red")
            raise


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Audit template permutations across AI assistants",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all                           # Full audit of all assistants and templates
  %(prog)s --assistant claude              # Audit only Claude assistant
  %(prog)s --assistant claude gemini       # Audit Claude and Gemini assistants
  %(prog)s --template specify.md tasks.md  # Audit specific templates only
  %(prog)s --clean                         # Clean output directory
  %(prog)s --list-assistants               # List available assistants
  %(prog)s --list-templates                # List available templates
        """,
    )

    parser.add_argument(
        "--all", action="store_true", help="Audit all assistants and templates"
    )

    parser.add_argument("--assistant", nargs="+", help="Specific assistant(s) to audit")

    parser.add_argument("--template", nargs="+", help="Specific template(s) to audit")

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("audit/templates"),
        help="Output directory for audit results (default: audit/templates)",
    )

    parser.add_argument(
        "--clean", action="store_true", help="Clean output directory before running"
    )

    parser.add_argument(
        "--list-assistants",
        action="store_true",
        help="List available assistants and exit",
    )

    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List available templates and exit",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    console = Console()

    # Handle list operations
    if args.list_assistants:
        assistants = list_assistant_names()
        console.print("Available assistants:", style="bold")
        for assistant in assistants:
            console.print(f"  - {assistant}")
        return

    if args.list_templates:
        service = JinjaTemplateService()
        templates = service.discover_templates()
        console.print("Available templates:", style="bold")
        for template in templates:
            console.print(f"  - {template.name} ({template.category})")
        return

    # Handle clean operation
    if args.clean:
        if args.output_dir.exists():
            shutil.rmtree(args.output_dir)
            console.print(f"Cleaned output directory: {args.output_dir}")
        else:
            console.print(f"Output directory doesn't exist: {args.output_dir}")

        if not (args.all or args.assistant or args.template):
            return

    # Validate arguments
    if not (args.all or args.assistant or args.template):
        parser.error("Must specify --all, --assistant, or --template")

    try:
        # Create auditor and run audit
        auditor = TemplateAuditor(args.output_dir)

        assistant_names = args.assistant if not args.all else None
        template_names = args.template if not args.all else None

        auditor.run_audit(assistant_names, template_names)

    except KeyboardInterrupt:
        console.print("\nAudit interrupted by user", style="yellow")
        sys.exit(1)
    except Exception as e:
        console.print(f"Error: {str(e)}", style="red")
        if args.verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
