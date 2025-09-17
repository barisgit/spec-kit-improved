#!/usr/bin/env python3
"""
Audit script that generates real projects using `specifyx init` directly for each AI assistant.

This tests the actual user workflow and generates authentic project structures
that users would get when running `specifyx init --ai claude` etc.

Usage:
    python scripts/audit_projects.py                    # Generate all
    python scripts/audit_projects.py --assistant claude # Generate just Claude
    python scripts/audit_projects.py --clean           # Clean audit directory
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class ProjectAuditor:
    """Audits SpecifyX by generating real projects for each AI assistant."""

    def __init__(self, audit_dir: Path = Path("audit/projects")):
        self.audit_dir = audit_dir
        self.available_assistants = ["claude", "gemini", "copilot", "cursor"]

    def clean_audit_directory(self) -> None:
        """Clean up and recreate the audit directory."""
        print(f"Cleaning audit directory: {self.audit_dir}")
        if self.audit_dir.exists():
            shutil.rmtree(self.audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        print("Audit directory cleaned")

    def get_assistant_names(self) -> List[str]:
        """Get available assistant names from the actual SpecifyX implementation."""
        try:
            # Try to get assistants from the actual CLI
            result = subprocess.run(
                ["specifyx", "init", "--help"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                # Parse help output to find assistant options
                help_text = result.stdout
                if "--ai" in help_text:
                    # Extract assistant names from help text
                    # This is a fallback - we'll use the hardcoded list for reliability
                    pass

            # For now, use the known assistants from the codebase analysis
            return self.available_assistants

        except (subprocess.SubprocessError, FileNotFoundError):
            print("Could not query SpecifyX CLI, using default assistant list")
            return self.available_assistants

    def generate_project_for_assistant(self, assistant: str) -> bool:
        """Generate a project for a specific AI assistant."""
        project_name = f"{assistant}"
        project_path = self.audit_dir / project_name

        print(f"\nGenerating project for {assistant}...")
        print(f"   Project: {project_name}")
        print(f"   Path: {project_path}")

        # Remove existing project if it exists
        if project_path.exists():
            shutil.rmtree(project_path)

        # Change to audit directory to run the command
        Path.cwd()
        try:
            self.audit_dir.parent.mkdir(parents=True, exist_ok=True)
            self.audit_dir.mkdir(parents=True, exist_ok=True)

            # Run specifyx init command
            cmd = [
                "specifyx",
                "init",
                project_name,
                "--ai",
                assistant,
                "--yes",  # Use defaults, skip interactive prompts
            ]

            print(f"   Command: {' '.join(cmd)}")
            print(f"   Working directory: {self.audit_dir}")

            result = subprocess.run(
                cmd,
                cwd=self.audit_dir,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minutes timeout
            )

            if result.returncode == 0:
                print(f"Successfully generated {assistant} project")
                if result.stdout:
                    # Save command output for debugging
                    output_file = project_path / "audit_generation.log"
                    with open(output_file, "w") as f:
                        f.write(f"Command: {' '.join(cmd)}\n")
                        f.write(f"Return code: {result.returncode}\n")
                        f.write("STDOUT:\n")
                        f.write(result.stdout)
                        f.write("\nSTDERR:\n")
                        f.write(result.stderr)
                return True
            else:
                print(f"Failed to generate {assistant} project")
                print(f"   Return code: {result.returncode}")
                if result.stderr:
                    print(f"   Error: {result.stderr[:200]}...")
                if result.stdout:
                    print(f"   Output: {result.stdout[:200]}...")
                return False

        except subprocess.TimeoutExpired:
            print(f"Timeout generating {assistant} project")
            return False
        except Exception as e:
            print(f"Exception generating {assistant} project: {e}")
            return False

    def analyze_project_structure(self, project_path: Path) -> Dict:
        """Analyze the structure of a generated project."""
        if not project_path.exists():
            return {"error": "Project directory does not exist"}

        structure: Dict[str, Any] = {
            "files": [],
            "directories": [],
            "file_count": 0,
            "directory_count": 0,
            "total_size": 0,
        }

        try:
            for item in project_path.rglob("*"):
                relative_path = item.relative_to(project_path)

                if item.is_file():
                    structure["files"].append(
                        {
                            "path": str(relative_path),
                            "size": item.stat().st_size,
                            "extension": item.suffix,
                        }
                    )
                    structure["file_count"] += 1
                    structure["total_size"] += item.stat().st_size
                elif item.is_dir():
                    structure["directories"].append(str(relative_path))
                    structure["directory_count"] += 1

            # Sort for consistent comparison
            structure["files"].sort(key=lambda x: x["path"])
            structure["directories"].sort()

        except Exception as e:
            structure["error"] = str(e)

        return structure

    def compare_project_structures(self, projects: Dict[str, Dict]) -> Dict:
        """Compare structures between different assistant projects."""
        if not projects:
            return {"error": "No projects to compare"}

        comparison: Dict[str, Any] = {
            "summary": {},
            "unique_files": {},
            "unique_directories": {},
            "common_files": set(),
            "common_directories": set(),
            "file_differences": {},
            "size_comparison": {},
        }

        # Get all file paths from all projects
        all_files: Dict[str, Set[str]] = {}
        all_directories = {}

        for assistant, structure in projects.items():
            if "error" in structure:
                continue

            files = [f["path"] for f in structure.get("files", [])]
            dirs = structure.get("directories", [])

            all_files[assistant] = set(files)
            all_directories[assistant] = set(dirs)

            comparison["summary"][assistant] = {
                "file_count": structure.get("file_count", 0),
                "directory_count": structure.get("directory_count", 0),
                "total_size": structure.get("total_size", 0),
            }

        if not all_files:
            return {"error": "No valid projects to compare"}

        # Find common and unique files
        all_file_sets = list(all_files.values())
        all_dir_sets = list(all_directories.values())

        if all_file_sets:
            comparison["common_files"] = list(set.intersection(*all_file_sets))
            comparison["common_directories"] = list(set.intersection(*all_dir_sets))

        # Find unique files for each assistant
        for assistant, file_set in all_files.items():
            other_files = set()
            for other_assistant, other_file_set in all_files.items():
                if other_assistant != assistant:
                    other_files.update(other_file_set)

            unique_files = file_set - other_files
            comparison["unique_files"][assistant] = list(unique_files)

        # Find unique directories for each assistant
        for assistant, dir_set in all_directories.items():
            other_dirs = set()
            for other_assistant, other_dir_set in all_directories.items():
                if other_assistant != assistant:
                    other_dirs.update(other_dir_set)

            unique_dirs = dir_set - other_dirs
            comparison["unique_directories"][assistant] = list(unique_dirs)

        return comparison

    def generate_comparison_report(
        self, projects: Dict[str, Dict], comparison: Dict
    ) -> str:
        """Generate a markdown comparison report."""
        report_lines = [
            "# SpecifyX AI Assistant Project Audit Report",
            "",
            f"Generated on: {Path.cwd()}",
            f"Audit directory: {self.audit_dir}",
            "",
            "## Summary",
            "",
        ]

        # Summary table
        if "summary" in comparison:
            report_lines.extend(
                [
                    "| Assistant | Files | Directories | Total Size |",
                    "|-----------|-------|-------------|------------|",
                ]
            )

            for assistant, stats in comparison["summary"].items():
                files = stats.get("file_count", 0)
                dirs = stats.get("directory_count", 0)
                size = stats.get("total_size", 0)
                size_str = f"{size:,} bytes" if size > 0 else "0 bytes"

                report_lines.append(f"| {assistant} | {files} | {dirs} | {size_str} |")

        report_lines.extend(["", "## Common Files", ""])

        # Common files
        common_files = comparison.get("common_files", [])
        if common_files:
            report_lines.append("Files present in all assistant projects:")
            report_lines.append("")
            for file_path in sorted(common_files):
                report_lines.append(f"- `{file_path}`")
        else:
            report_lines.append("No files are common to all assistant projects.")

        report_lines.extend(["", "## Common Directories", ""])

        # Common directories
        common_dirs = comparison.get("common_directories", [])
        if common_dirs:
            report_lines.append("Directories present in all assistant projects:")
            report_lines.append("")
            for dir_path in sorted(common_dirs):
                report_lines.append(f"- `{dir_path}/`")
        else:
            report_lines.append("No directories are common to all assistant projects.")

        # Unique files per assistant
        report_lines.extend(["", "## Unique Files by Assistant", ""])

        unique_files = comparison.get("unique_files", {})
        for assistant in sorted(unique_files.keys()):
            files = unique_files[assistant]
            report_lines.extend([f"### {assistant.title()} Unique Files", ""])

            if files:
                for file_path in sorted(files):
                    report_lines.append(f"- `{file_path}`")
            else:
                report_lines.append("No unique files.")

            report_lines.append("")

        # Unique directories per assistant
        report_lines.extend(["## Unique Directories by Assistant", ""])

        unique_dirs = comparison.get("unique_directories", {})
        for assistant in sorted(unique_dirs.keys()):
            dirs = unique_dirs[assistant]
            report_lines.extend([f"### {assistant.title()} Unique Directories", ""])

            if dirs:
                for dir_path in sorted(dirs):
                    report_lines.append(f"- `{dir_path}/`")
            else:
                report_lines.append("No unique directories.")

            report_lines.append("")

        # Project details
        report_lines.extend(["## Detailed Project Structures", ""])

        for assistant, structure in projects.items():
            report_lines.extend([f"### {assistant.title()} Project Structure", ""])

            if "error" in structure:
                report_lines.append(f"Error: {structure['error']}")
                report_lines.append("")
                continue

            files = structure.get("files", [])
            dirs = structure.get("directories", [])

            if dirs:
                report_lines.append("Directories:")
                for dir_path in sorted(dirs):
                    report_lines.append(f"- `{dir_path}/`")
                report_lines.append("")

            if files:
                report_lines.append("Files:")
                for file_info in sorted(files, key=lambda x: x["path"]):
                    path = file_info["path"]
                    size = file_info["size"]
                    size_str = f" ({size:,} bytes)" if size > 0 else ""
                    report_lines.append(f"- `{path}`{size_str}")

            report_lines.append("")

        return "\n".join(report_lines)

    def run_audit(self, specific_assistant: Optional[str] = None) -> None:
        """Run the complete audit process."""
        print("Starting SpecifyX AI Assistant Audit")
        print("=" * 50)

        # Clean audit directory
        self.clean_audit_directory()

        # Determine which assistants to audit
        assistants_to_test = (
            [specific_assistant] if specific_assistant else self.get_assistant_names()
        )

        if specific_assistant and specific_assistant not in self.available_assistants:
            print(f"❌ Unknown assistant: {specific_assistant}")
            print(f"Available assistants: {', '.join(self.available_assistants)}")
            return

        print(f"\nTesting assistants: {', '.join(assistants_to_test)}")

        # Generate projects
        successful_projects: List[str] = []
        failed_projects: List[str] = []

        for assistant in assistants_to_test:
            success = self.generate_project_for_assistant(assistant)
            if success:
                successful_projects.append(assistant)
            else:
                failed_projects.append(assistant)

        print("\nResults Summary:")
        print(
            f"   Successful: {len(successful_projects)} ({', '.join(successful_projects)})"
        )
        print(f"   Failed: {len(failed_projects)} ({', '.join(failed_projects)})")

        if not successful_projects:
            print(
                "\nNo projects were generated successfully. Cannot create comparison report."
            )
            return

        # Analyze project structures
        print("\nAnalyzing project structures...")
        projects = {}

        for assistant in successful_projects:
            project_path = self.audit_dir / f"{assistant}"
            structure = self.analyze_project_structure(project_path)
            projects[assistant] = structure
            print(f"   Analyzed {assistant} project")

        # Compare structures
        print("\nComparing project structures...")
        comparison = self.compare_project_structures(projects)

        # Generate report
        print("\nGenerating comparison report...")
        report_content = self.generate_comparison_report(projects, comparison)

        report_path = self.audit_dir / "comparison-report.md"
        with open(report_path, "w") as f:
            f.write(report_content)

        print(f"Report saved: {report_path}")

        # Save raw data as JSON for further analysis
        data_path = self.audit_dir / "audit-data.json"
        audit_data = {
            "successful_projects": successful_projects,
            "failed_projects": failed_projects,
            "project_structures": projects,
            "comparison": comparison,
        }

        with open(data_path, "w") as f:
            json.dump(audit_data, f, indent=2, default=str)

        print(f"Raw data saved: {data_path}")

        print("\nAudit complete!")
        print(f"Results in: {self.audit_dir}")
        print(f"Report: {report_path}")


def main():
    """Main entry point for the audit script."""
    parser = argparse.ArgumentParser(
        description="Audit SpecifyX by generating real projects for each AI assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/audit_projects.py                    # Generate all projects
  python scripts/audit_projects.py --assistant claude # Generate just Claude
  python scripts/audit_projects.py --clean           # Clean audit directory
        """,
    )

    parser.add_argument(
        "--assistant",
        choices=["claude", "gemini", "copilot", "cursor"],
        help="Generate project for specific AI assistant only",
    )

    parser.add_argument(
        "--clean", action="store_true", help="Clean audit directory and exit"
    )

    parser.add_argument(
        "--audit-dir",
        type=Path,
        default=Path("audit/projects"),
        help="Directory for audit results (default: audit/projects)",
    )

    args = parser.parse_args()

    # Initialize auditor
    auditor = ProjectAuditor(audit_dir=args.audit_dir)

    # Handle clean option
    if args.clean:
        auditor.clean_audit_directory()
        print("Audit directory cleaned")
        return

    # Check if specifyx is available
    try:
        result = subprocess.run(
            ["specifyx", "--version"], capture_output=True, timeout=10
        )
        if result.returncode != 0:
            print("SpecifyX CLI not found or not working")
            print("   Make sure to install SpecifyX first: pip install .")
            sys.exit(1)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("SpecifyX CLI not found in PATH")
        print("   Make sure to install SpecifyX first: pip install .")
        sys.exit(1)

    # Run audit
    try:
        auditor.run_audit(specific_assistant=args.assistant)
    except KeyboardInterrupt:
        print("\nAudit interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nAudit failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
