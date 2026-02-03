#!/usr/bin/env python3
"""Create or restore repository snapshots in a deterministic, text-only format."""

from __future__ import annotations

import argparse
import datetime as dt
import os
from pathlib import Path
import subprocess
from typing import Iterable, List, Optional


BINARY_EXTENSIONS = {
    ".class",
    ".jar",
    ".apk",
    ".aar",
    ".so",
    ".dll",
    ".dylib",
    ".exe",
    ".bin",
    ".o",
    ".a",
    ".pyc",
    ".pyo",
    ".whl",
    ".zip",
    ".tar",
    ".gz",
    ".tgz",
    ".7z",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".mp3",
    ".mp4",
    ".wav",
    ".ogg",
    ".mov",
    ".avi",
    ".mkv",
}


def get_repo_root() -> Path:
    """Return the git repo root if available; otherwise use current working dir."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()
    return Path(result.stdout.strip())


def has_dot_component(path: Path) -> bool:
    """Return True if any path component starts with a dot."""
    return any(part.startswith(".") for part in path.parts)


def is_binary_file(path: Path) -> bool:
    """Heuristic binary detection using extension and null-byte scan."""
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    try:
        with path.open("rb") as handle:
            chunk = handle.read(4096)
            return b"\x00" in chunk
    except OSError:
        return True


def list_files_with_git(repo_root: Path) -> Optional[List[Path]]:
    """List tracked and untracked (non-ignored) files via git."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "--cached", "--others", "--exclude-standard"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    files: List[Path] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        files.append(Path(line.strip()))
    return files


def list_files_fallback(repo_root: Path) -> List[Path]:
    """Fallback file listing if git is unavailable."""
    files: List[Path] = []
    for root, dirs, filenames in os.walk(repo_root):
        root_path = Path(root)
        dirs[:] = [
            d
            for d in dirs
            if d != "book" and not d.startswith(".")
        ]
        for filename in filenames:
            rel_path = root_path.joinpath(filename).relative_to(repo_root)
            files.append(rel_path)
    return files


def filter_files(repo_root: Path, files: Iterable[Path]) -> List[Path]:
    """Apply exclusions: book folder, dotfiles, and binaries."""
    filtered: List[Path] = []
    for rel_path in files:
        if rel_path.parts and rel_path.parts[0] == "book":
            continue
        if has_dot_component(rel_path):
            continue
        full_path = repo_root / rel_path
        if not full_path.is_file():
            continue
        if is_binary_file(full_path):
            continue
        filtered.append(rel_path)
    return sorted(filtered)


def build_tree(paths: Iterable[Path]) -> str:
    """Build a simple directory tree string from relative paths."""
    tree: dict = {}
    for path in paths:
        current = tree
        for part in path.parts:
            current = current.setdefault(part, {})
    lines: List[str] = []

    def walk(node: dict, prefix: str = "") -> None:
        for index, name in enumerate(sorted(node.keys())):
            is_last = index == len(node) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{name}")
            child = node[name]
            if child:
                extension = "    " if is_last else "│   "
                walk(child, prefix + extension)

    walk(tree)
    return "\n".join(lines)


def write_snapshot(repo_root: Path, output_path: Path) -> None:
    """Write a god.txt snapshot with directory tree and file contents."""
    files = list_files_with_git(repo_root)
    if files is None:
        files = list_files_fallback(repo_root)
    filtered = filter_files(repo_root, files)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()

    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("# Repository Snapshot\n")
        handle.write(f"# Generated (UTC): {generated_at}\n")
        handle.write(f"# Root: {repo_root}\n")
        handle.write("# Excludes: book/, dotfiles, git-ignored, binary extensions/binary bytes\n\n")

        handle.write("## Directory Tree\n")
        handle.write(build_tree(filtered))
        handle.write("\n\n")

        handle.write("## Files\n")
        for rel_path in filtered:
            handle.write(f"--- BEGIN FILE: {rel_path} ---\n")
            file_path = repo_root / rel_path
            content = file_path.read_text(encoding="utf-8")
            handle.write(content)
            if not content.endswith("\n"):
                handle.write("\n")
            handle.write(f"--- END FILE: {rel_path} ---\n\n")


def restore_snapshot(repo_root: Path, snapshot_path: Path) -> None:
    """Restore files from a god.txt snapshot into the repo root."""
    lines = snapshot_path.read_text(encoding="utf-8").splitlines()
    current_path: Optional[Path] = None
    buffer: List[str] = []

    def flush_file() -> None:
        nonlocal buffer, current_path
        if current_path is None:
            return
        safe_path = Path(current_path)
        if safe_path.is_absolute() or ".." in safe_path.parts:
            raise ValueError(f"Refusing to write unsafe path: {safe_path}")
        target = repo_root / safe_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(buffer) + "\n", encoding="utf-8")
        buffer = []
        current_path = None

    for line in lines:
        if line.startswith("--- BEGIN FILE: "):
            flush_file()
            current_path = Path(line.replace("--- BEGIN FILE: ", "").replace(" ---", "").strip())
            buffer = []
            continue
        if line.startswith("--- END FILE: "):
            flush_file()
            continue
        if current_path is not None:
            buffer.append(line)

    flush_file()


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Create or restore god.txt snapshots.")
    parser.add_argument(
        "snapshot",
        nargs="?",
        help="Path to an existing god.txt to restore from (optional).",
    )
    parser.add_argument(
        "--output",
        help="Optional output path for new snapshots (defaults to book/<timestamp>/god.txt).",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for snapshot creation or restore."""
    args = parse_args()
    repo_root = get_repo_root()

    if args.snapshot and Path(args.snapshot).is_file():
        restore_snapshot(repo_root, Path(args.snapshot))
        return

    if args.snapshot and not Path(args.snapshot).is_file():
        raise FileNotFoundError(f"Snapshot file not found: {args.snapshot}")

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = repo_root / "book" / timestamp / "god.txt"

    write_snapshot(repo_root, output_path)


if __name__ == "__main__":
    main()
