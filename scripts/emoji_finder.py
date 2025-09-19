#!/usr/bin/env python3
"""emoji_finder.py

Find and report emoji characters in files recursively.

Usage examples:
  - Scan current directory:
      python scripts/emoji_finder.py
  - Scan a specific path and exclude common build dirs:
      python scripts/emoji_finder.py --path src --exclude dist build node_modules
  - Only scan specific extensions:
      python scripts/emoji_finder.py --extensions .py .md .ts

Exit codes:
  0 - No emojis found or successful run
  1 - Emojis found (useful for CI checks with --fail-on-find)
  2 - Error occurred
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional, Pattern, Sequence, Tuple


def build_emoji_regex() -> Pattern[str]:
    """Return a compiled regex that matches most emoji characters.

    Note: Comprehensive emoji detection is complex (ZWJ sequences, modifiers, etc.).
    This pattern covers the vast majority of standalone emoji code points and common sequences.
    """
    import re

    # Match either a single emoji from common ranges, or a flag pair (two RIS)
    pattern = (
        r"(?:["
        r"\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
        r"\U0001F600-\U0001F64F"  # Emoticons
        r"\U0001F680-\U0001F6FF"  # Transport and Map
        r"\U0001F700-\U0001F77F"  # Alchemical Symbols
        r"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        r"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        r"\U0001FA00-\U0001FA6F"  # Chess etc.
        r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        r"\u2600-\u26FF"  # Misc symbols (BMP)
        r"\u2700-\u27BF"  # Dingbats (BMP)
        r"\u2300-\u23FF"  # Misc technical (BMP)
        r"\U0001F3FB-\U0001F3FF"  # Skin tone modifiers
        r"\uFE0F"  # VS16
        r"\u200D"  # ZWJ
        r"]|(?:[\U0001F1E6-\U0001F1FF]{2}))"
    )

    return re.compile(pattern)


@dataclass
class Match:
    path: Path
    line_number: int
    column_number: int
    line_text: str
    emoji: str


DEFAULT_EXCLUDES = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
}


def iter_files(
    root: Path,
    include_hidden: bool,
    excludes: Sequence[str],
    extensions: Optional[Sequence[str]],
) -> Iterator[Path]:
    exclude_set = set(excludes)
    ext_set = {e.lower() for e in extensions} if extensions else None

    for dirpath, dirnames, filenames in os.walk(root):
        # Filter directories in-place for os.walk pruning
        pruned_dirnames = []
        for d in dirnames:
            if (not include_hidden and d.startswith(".")) or d in exclude_set:
                continue
            pruned_dirnames.append(d)
        dirnames[:] = pruned_dirnames

        for filename in filenames:
            if not include_hidden and filename.startswith("."):
                continue
            if ext_set is not None:
                _, ext = os.path.splitext(filename)
                if ext.lower() not in ext_set:
                    continue
            yield Path(dirpath) / filename


def _is_probably_binary(path: Path, probe_size: int = 4096) -> bool:
    try:
        with path.open("rb") as f:
            data = f.read(probe_size)
        if b"\x00" in data:
            return True
        # Heuristic: if many bytes are non-text (outside common printable ranges), assume binary
        if not data:
            return False
        text_like = sum(
            1
            for b in data
            if 32 <= b <= 126 or b in (9, 10, 13)  # printable ASCII + whitespace
        )
        return (text_like / len(data)) < 0.6
    except OSError:
        return True


def _isolation_false_positive(emoji: str) -> bool:
    # Ignore isolated ZWJ and VS-16 and skin tone modifiers
    # Only treat as isolated when the match is a single codepoint
    if len(emoji) != 1:
        return False
    if emoji == "\u200d" or emoji == "\ufe0f":
        return True
    codepoint = ord(emoji)
    return 0x1F3FB <= codepoint <= 0x1F3FF


def find_emojis_in_file(
    path: Path, emoji_regex: Pattern[str], max_line_length: int = 20000
) -> Iterator[Match]:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for line_number, raw_line in enumerate(f, start=1):
                # Avoid pathological memory if a single line is massive
                line = raw_line.rstrip("\n")
                if len(line) > max_line_length:
                    line = line[:max_line_length]

                for m in emoji_regex.finditer(line):
                    e = m.group(0)
                    if _isolation_false_positive(e):
                        continue
                    yield Match(
                        path=path,
                        line_number=line_number,
                        column_number=m.start() + 1,
                        line_text=line,
                        emoji=e,
                    )
    except (UnicodeDecodeError, OSError):
        return


def format_match(match: Match, show_line: bool) -> str:
    location = f"{match.path}:{match.line_number}:{match.column_number}"
    if show_line:
        return f"{location} {match.emoji} | {match.line_text}"
    return f"{location} {match.emoji}"


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find emoji characters in files recursively"
    )
    parser.add_argument(
        "--path", type=str, default=".", help="Root path to scan (default: .)"
    )
    parser.add_argument(
        "--extensions",
        nargs="*",
        default=None,
        help="Only include files with these extensions (e.g. .py .md)",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=sorted(DEFAULT_EXCLUDES),
        help="Directories to exclude",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and directories (dot-prefixed)",
    )
    parser.add_argument(
        "--no-line",
        action="store_true",
        help="Do not print the full line text, only location and emoji",
    )
    parser.add_argument(
        "--tree",
        action="store_true",
        help="Summarize results as a directory tree (default)",
    )
    parser.add_argument(
        "--flat",
        action="store_true",
        help="Print each match on its own line (override --tree)",
    )
    parser.add_argument(
        "--max-emojis-per-file",
        type=int,
        default=6,
        help="Max unique emojis to display per file in tree output",
    )
    parser.add_argument(
        "--fail-on-find",
        action="store_true",
        help="Exit with code 1 if any emoji is found (useful in CI)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    root = Path(args.path).resolve()
    if not root.exists():
        print(f"Path not found: {root}", file=sys.stderr)
        return 2

    emoji_regex = build_emoji_regex()
    total_matches = 0

    # Decide output mode
    tree_mode = True
    if args.flat:
        tree_mode = False
    elif args.tree:
        tree_mode = True

    per_file_emojis: dict[Path, List[Match]] = {}

    for file_path in iter_files(
        root,
        include_hidden=args.include_hidden,
        excludes=args.exclude,
        extensions=args.extensions,
    ):
        if _is_probably_binary(file_path):
            continue
        for match in find_emojis_in_file(file_path, emoji_regex):
            if tree_mode:
                per_file_emojis.setdefault(file_path, []).append(match)
            else:
                try:
                    print(format_match(match, show_line=not args.no_line))
                except BrokenPipeError:
                    return 0
            total_matches += 1

    if tree_mode:
        # Build a filtered directory tree that only contains files with matches
        from collections import Counter, defaultdict

        # Map of directory -> list of files in that directory
        dir_to_files: dict[Path, List[Path]] = defaultdict(list)
        for file_path in per_file_emojis:
            dir_to_files[file_path.parent].append(file_path)

        def rel(p: Path) -> str:
            try:
                return str(p.relative_to(root))
            except Exception:
                return str(p)

        def print_tree(dir_path: Path, prefix: str = "") -> None:
            entries: List[Tuple[str, Path, bool]] = []
            # Directories with content
            child_dirs = sorted(
                {p.parent for p in per_file_emojis if p.parent.parent == dir_path}
            )
            for d in child_dirs:
                entries.append((d.name + "/", d, True))
            # Files directly in this dir
            for f in sorted(dir_to_files.get(dir_path, []), key=lambda p: p.name):
                entries.append((f.name, f, False))

            for idx, (name, path_obj, is_dir) in enumerate(entries):
                is_last = idx == len(entries) - 1
                branch = "└── " if is_last else "├── "
                continuation = "    " if is_last else "│   "
                if is_dir:
                    print(f"{prefix}{branch}{name}")
                    print_tree(path_obj, prefix + continuation)
                else:
                    matches = per_file_emojis.get(path_obj, [])
                    counter = Counter(m.emoji for m in matches)
                    unique = list(counter.items())
                    unique.sort(key=lambda kv: (-kv[1], kv[0]))
                    shown = unique[: max(0, args.max_emojis_per_file)]
                    summary = " ".join(f"{e}×{c}" for e, c in shown)
                    extra = len(unique) - len(shown)
                    extra_str = f" (+{extra} more)" if extra > 0 else ""
                    print(
                        f"{prefix}{branch}{name} [{len(matches)}] {summary}{extra_str}"
                    )

        # Start from root, but only print subtrees containing matches
        # Build a set of unique top-level Path objects
        printed_any = False
        # If all files are directly under root, just print files
        if any(fp.parent == root for fp in per_file_emojis):
            print_tree(root)
            printed_any = True
        # Also print subdirectories that contain matches
        subdirs = sorted({fp.parent for fp in per_file_emojis if fp.parent != root})
        top_level_subdirs = sorted(
            {Path(*d.parts[: len(root.parts) + 1]) for d in subdirs}
        )
        for d in top_level_subdirs:
            print(f"{d.name}/")
            print_tree(d, prefix="")
            printed_any = True
        if not printed_any and total_matches == 0:
            print("No emojis found.")

    if args.fail_on_find and total_matches > 0:
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        # As a last resort, avoid flushing at shutdown on broken pipe
        import os

        os._exit(0)
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        sys.exit(130)
