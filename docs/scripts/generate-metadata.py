#!/usr/bin/env python3
"""
Advanced metadata extraction for SpecifyX documentation generation.
Auto-discovers modules, extracts comprehensive docstrings, and generates rich JSON metadata.
"""

import importlib
import inspect
import json
import os
import pkgutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Type

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


@dataclass
class DocstringInfo:
    """Parsed docstring information"""

    summary: str = ""
    description: str = ""
    args: Dict[str, str] = field(default_factory=dict)
    returns: str = ""
    raises: Dict[str, str] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    raw: str = ""


@dataclass
class ParameterInfo:
    """Parameter metadata"""

    name: str
    type_annotation: str
    default_value: Optional[str]
    is_required: bool
    description: str = ""


@dataclass
class MethodInfo:
    """Method metadata"""

    name: str
    signature: str
    docstring: DocstringInfo
    parameters: List[ParameterInfo]
    return_type: str
    is_async: bool = False
    is_property: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False


@dataclass
class ClassInfo:
    """Class metadata"""

    name: str
    module_path: str
    docstring: DocstringInfo
    methods: List[MethodInfo]
    properties: List[str]
    inheritance: List[str]
    is_abstract: bool = False
    is_dataclass: bool = False
    is_enum: bool = False


class DocstringParser:
    """Advanced docstring parser supporting multiple formats"""

    @staticmethod
    def parse(docstring: Optional[str]) -> DocstringInfo:
        """Parse docstring into structured information"""
        if not docstring:
            return DocstringInfo()

        lines = docstring.strip().split("\n")
        if not lines:
            return DocstringInfo()

        info = DocstringInfo(raw=docstring)

        # Get summary (first non-empty line)
        description_lines: List[str] = []
        current_section: Optional[
            Literal["args", "examples", "notes", "raises", "returns"]
        ] = None

        i = 0
        # Extract summary
        while i < len(lines) and not lines[i].strip():
            i += 1

        if i < len(lines):
            info.summary = lines[i].strip()
            i += 1

        # Skip empty lines after summary
        while i < len(lines) and not lines[i].strip():
            i += 1

        # Parse rest of docstring
        current_section: Optional[
            Literal["args", "examples", "notes", "raises", "returns"]
        ] = None
        while i < len(lines):
            line = lines[i].strip()

            if line.lower().startswith("args:") or line.lower().startswith(
                "parameters:"
            ):
                current_section = "args"
            elif line.lower().startswith("returns:") or line.lower().startswith(
                "return:"
            ):
                current_section = "returns"
            elif line.lower().startswith("raises:") or line.lower().startswith(
                "except:"
            ):
                current_section = "raises"
            elif line.lower().startswith("example"):
                current_section = "examples"
            elif line.lower().startswith("note"):
                current_section = "notes"
            elif not line and current_section:
                current_section = None
            elif current_section == "args" and line and ":" in line:
                arg_name, arg_desc = line.split(":", 1)
                info.args[arg_name.strip()] = arg_desc.strip()
            elif current_section == "returns" and line:
                info.returns += line + " "
            elif current_section == "examples" and line:
                info.examples.append(line)
            elif current_section == "notes" and line:
                info.notes.append(line)
            elif not current_section and line:
                description_lines.append(line)

            i += 1

        info.description = " ".join(description_lines).strip()
        info.returns = info.returns.strip()

        return info


class CodeIntrospector:
    """Advanced code introspection and metadata extraction"""

    def __init__(self):
        self.parser = DocstringParser()

    def get_type_string(self, annotation: Any) -> str:
        """Convert type annotation to string"""
        if annotation is inspect.Parameter.empty:
            return "Any"

        if hasattr(annotation, "__name__"):
            return annotation.__name__

        return (
            str(annotation)
            .replace("typing.", "")
            .replace("<class '", "")
            .replace("'>", "")
        )

    def extract_parameter_info(
        self, param: inspect.Parameter, docstring_args: Dict[str, str]
    ) -> ParameterInfo:
        """Extract detailed parameter information"""
        return ParameterInfo(
            name=param.name,
            type_annotation=self.get_type_string(param.annotation),
            default_value=str(param.default)
            if param.default != inspect.Parameter.empty
            else None,
            is_required=param.default == inspect.Parameter.empty,
            description=docstring_args.get(param.name, ""),
        )

    def extract_method_info(self, method: Any, method_name: str) -> MethodInfo:
        """Extract comprehensive method information"""
        docstring_info = self.parser.parse(method.__doc__)

        try:
            sig = inspect.signature(method)
            parameters = []

            for param_name, param in sig.parameters.items():
                if param_name != "self":
                    param_info = self.extract_parameter_info(param, docstring_info.args)
                    parameters.append(param_info)

            return_annotation = sig.return_annotation
            return_type = self.get_type_string(return_annotation)

        except (ValueError, TypeError):
            parameters = []
            return_type = "Any"

        return MethodInfo(
            name=method_name,
            signature=f"{method_name}{inspect.signature(method) if callable(method) else '()'}",
            docstring=docstring_info,
            parameters=parameters,
            return_type=return_type,
            is_async=inspect.iscoroutinefunction(method),
            is_property=isinstance(
                inspect.getattr_static(
                    method.__class__ if hasattr(method, "__class__") else object,
                    method_name,
                    None,
                ),
                property,
            ),
            is_classmethod=isinstance(
                inspect.getattr_static(
                    method.__class__ if hasattr(method, "__class__") else object,
                    method_name,
                    None,
                ),
                classmethod,
            ),
            is_staticmethod=isinstance(
                inspect.getattr_static(
                    method.__class__ if hasattr(method, "__class__") else object,
                    method_name,
                    None,
                ),
                staticmethod,
            ),
        )

    def extract_class_info(self, cls: Type, module_path: str) -> ClassInfo:
        """Extract comprehensive class information"""
        docstring_info = self.parser.parse(cls.__doc__)

        # Extract methods
        methods = []
        properties = []

        for name, method in inspect.getmembers(cls):
            if name.startswith("_"):
                continue

            if inspect.ismethod(method) or inspect.isfunction(method):
                try:
                    method_info = self.extract_method_info(method, name)
                    methods.append(method_info)
                except Exception:
                    continue
            elif isinstance(inspect.getattr_static(cls, name, None), property):
                properties.append(name)

        # Get inheritance info
        inheritance = [base.__name__ for base in cls.__bases__ if base is not object]

        return ClassInfo(
            name=cls.__name__,
            module_path=module_path,
            docstring=docstring_info,
            methods=methods,
            properties=properties,
            inheritance=inheritance,
            is_abstract=inspect.isabstract(cls),
            is_dataclass=hasattr(cls, "__dataclass_fields__"),
            is_enum=issubclass(cls, Enum),
        )


class ModuleDiscovery:
    """Auto-discovery of modules and their components"""

    def __init__(self, package_name: str = "specify_cli"):
        self.package_name = package_name
        self.introspector = CodeIntrospector()

    def discover_all_modules(self) -> Dict[str, Any]:
        """Auto-discover all modules in the package"""
        discovered = {
            "commands": {},
            "services": {},
            "models": {},
            "assistants": {},
            "utils": {},
            "core": {},
            "other": {},
        }

        try:
            package = importlib.import_module(self.package_name)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Discovering modules...", total=None)

                for _finder, module_name, _ispkg in pkgutil.walk_packages(
                    package.__path__, prefix=f"{self.package_name}."
                ):
                    try:
                        progress.update(task, description=f"Processing {module_name}")
                        module_info = self._process_module(module_name)
                        if module_info:
                            category = self._categorize_module(module_name)
                            discovered[category][module_name] = module_info
                    except Exception as e:
                        console.print(
                            f"[yellow]Warning: Could not process {module_name}: {e}[/yellow]"
                        )
                        continue

        except Exception as e:
            console.print(f"[red]Error discovering modules: {e}[/red]")

        return discovered

    def _process_module(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Process a single module and extract its metadata"""
        try:
            module = importlib.import_module(module_name)

            module_info: Dict[str, Any] = {
                "name": module_name,
                "file_path": getattr(module, "__file__", ""),
                "docstring": self.introspector.parser.parse(module.__doc__).__dict__,
                "classes": {},
                "functions": {},
                "constants": {},
                "imports": [],
            }

            # Extract classes
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ == module_name:  # Only classes defined in this module
                    try:
                        class_info = self.introspector.extract_class_info(
                            obj, module_name
                        )
                        module_info["classes"][name] = self._serialize_class_info(
                            class_info
                        )
                    except Exception:
                        continue

            # Extract functions
            for name, obj in inspect.getmembers(module, inspect.isfunction):
                if (
                    obj.__module__ == module_name
                ):  # Only functions defined in this module
                    try:
                        func_info = self.introspector.extract_method_info(obj, name)
                        module_info["functions"][name] = self._serialize_method_info(
                            func_info
                        )
                    except Exception:
                        continue

            # Extract constants
            for name, obj in inspect.getmembers(module):
                if (
                    not name.startswith("_")
                    and not inspect.isclass(obj)
                    and not inspect.isfunction(obj)
                    and not inspect.ismodule(obj)
                    and isinstance(obj, (str, int, float, bool, list, dict, tuple))
                ):
                    module_info["constants"][name] = {
                        "value": str(obj),
                        "type": type(obj).__name__,
                    }

            return (
                module_info
                if any(
                    [
                        module_info["classes"],
                        module_info["functions"],
                        module_info["constants"],
                    ]
                )
                else None
            )

        except Exception:
            return None

    def _categorize_module(self, module_name: str) -> str:
        """Categorize module based on its name/path"""
        parts = module_name.split(".")

        if "commands" in parts:
            return "commands"
        elif "services" in parts:
            return "services"
        elif "models" in parts:
            return "models"
        elif "assistants" in parts:
            return "assistants"
        elif "utils" in parts:
            return "utils"
        elif "core" in parts:
            return "core"
        else:
            return "other"

    def _serialize_class_info(self, class_info: ClassInfo) -> Dict[str, Any]:
        """Serialize ClassInfo to dict"""
        return {
            "name": class_info.name,
            "module_path": class_info.module_path,
            "docstring": class_info.docstring.__dict__,
            "methods": [self._serialize_method_info(m) for m in class_info.methods],
            "properties": class_info.properties,
            "inheritance": class_info.inheritance,
            "is_abstract": class_info.is_abstract,
            "is_dataclass": class_info.is_dataclass,
            "is_enum": class_info.is_enum,
        }

    def _serialize_method_info(self, method_info: MethodInfo) -> Dict[str, Any]:
        """Serialize MethodInfo to dict"""
        return {
            "name": method_info.name,
            "signature": method_info.signature,
            "docstring": method_info.docstring.__dict__,
            "parameters": [p.__dict__ for p in method_info.parameters],
            "return_type": method_info.return_type,
            "is_async": method_info.is_async,
            "is_property": method_info.is_property,
            "is_classmethod": method_info.is_classmethod,
            "is_staticmethod": method_info.is_staticmethod,
        }


def main():
    """Generate comprehensive metadata JSON"""
    console.print(
        "[bold blue]Extracting comprehensive SpecifyX metadata...[/bold blue]"
    )

    # Change to project root
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    sys.path.insert(0, str(project_root / "src"))

    # Initialize extractors
    module_discovery = ModuleDiscovery()

    # Extract all metadata
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Extract modules
        task1 = progress.add_task("Extracting module metadata...", total=None)
        modules = module_discovery.discover_all_modules()

        progress.update(task1, description="Finalizing metadata...")

    # Build final metadata structure
    metadata: Dict[str, Any] = {
        "project": {
            "name": "SpecifyX",
            "version": "0.3.0",  # FIXME: Replace with actual version (dynamic)
            "description": "Enhanced spec-driven development CLI with modern architecture",
        },
        "generated_at": str(project_root),
        "generation_timestamp": str(Path().stat().st_mtime),
        "modules": modules,
        "stats": {
            "total_modules": sum(len(category) for category in modules.values()),
            "total_classes": sum(
                len(module.get("classes", {}))
                for category in modules.values()
                for module in category.values()
            ),
            "total_functions": sum(
                len(module.get("functions", {}))
                for category in modules.values()
                for module in category.values()
            ),
        },
    }

    # Write output
    output_file = Path("docs/metadata.json")
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # Print summary
    console.print(f"[green]Generated comprehensive metadata: {output_file}[/green]")
    console.print("[dim]Statistics:[/dim]")
    stats = metadata["stats"]
    total_modules = stats["total_modules"]
    total_classes = stats["total_classes"]
    total_functions = stats["total_functions"]
    console.print(f"[dim]  Modules: {total_modules}[/dim]")
    console.print(f"[dim]  Classes: {total_classes}[/dim]")
    console.print(f"[dim]  Functions: {total_functions}[/dim]")


if __name__ == "__main__":
    main()
