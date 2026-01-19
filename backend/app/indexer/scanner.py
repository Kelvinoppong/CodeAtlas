"""
File Scanner - discovers files in a project with gitignore support
"""

import os
import hashlib
from pathlib import Path
from typing import List, Optional, Generator, Set
from dataclasses import dataclass
import pathspec


# Common binary extensions to skip
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".exe", ".dll", ".so", ".dylib",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".pyc", ".pyo", ".class", ".o", ".obj",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".db", ".sqlite", ".sqlite3",
}

# Directories to always ignore
ALWAYS_IGNORE = {
    ".git", ".svn", ".hg",
    "node_modules", "__pycache__", ".pytest_cache",
    ".venv", "venv", "env", ".env",
    ".next", ".nuxt", "dist", "build", "out",
    ".idea", ".vscode",
    "coverage", ".coverage", "htmlcov",
    ".tox", ".nox",
}

# Language detection by extension
EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".r": "r",
    ".R": "r",
    ".sql": "sql",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".md": "markdown",
    ".mdx": "markdown",
    ".rst": "rst",
    ".txt": "text",
    ".vue": "vue",
    ".svelte": "svelte",
}


@dataclass
class ScannedFile:
    """Represents a discovered file"""
    path: str  # Relative to project root
    absolute_path: str
    language: Optional[str]
    size_bytes: int
    is_binary: bool
    sha256: Optional[str] = None
    line_count: int = 0
    content: Optional[str] = None


class FileScanner:
    """Scans a project directory for source files"""

    def __init__(
        self,
        root_path: str,
        max_file_size: int = 1024 * 1024,  # 1MB default
        include_content: bool = True,
    ):
        self.root_path = Path(root_path).resolve()
        self.max_file_size = max_file_size
        self.include_content = include_content
        self._gitignore_spec: Optional[pathspec.PathSpec] = None
        self._load_gitignore()

    def _load_gitignore(self) -> None:
        """Load .gitignore patterns"""
        gitignore_path = self.root_path / ".gitignore"
        patterns = []

        if gitignore_path.exists():
            with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                patterns = f.read().splitlines()

        # Add always-ignore patterns
        for d in ALWAYS_IGNORE:
            patterns.append(f"{d}/")
            patterns.append(f"**/{d}/")

        if patterns:
            self._gitignore_spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)

    def _should_ignore(self, rel_path: str) -> bool:
        """Check if a path should be ignored"""
        # Check against gitignore
        if self._gitignore_spec and self._gitignore_spec.match_file(rel_path):
            return True

        # Check path components against always-ignore
        parts = Path(rel_path).parts
        for part in parts:
            if part in ALWAYS_IGNORE:
                return True

        return False

    def _is_binary(self, path: Path) -> bool:
        """Check if file is binary"""
        ext = path.suffix.lower()
        if ext in BINARY_EXTENSIONS:
            return True

        # Check first bytes for null characters
        try:
            with open(path, "rb") as f:
                chunk = f.read(8192)
                if b"\x00" in chunk:
                    return True
        except (IOError, OSError):
            return True

        return False

    def _detect_language(self, path: Path) -> Optional[str]:
        """Detect programming language from file extension"""
        ext = path.suffix.lower()
        return EXTENSION_TO_LANGUAGE.get(ext)

    def _compute_sha256(self, path: Path) -> str:
        """Compute SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def scan(self) -> Generator[ScannedFile, None, None]:
        """Scan the project and yield discovered files"""
        for root, dirs, files in os.walk(self.root_path):
            # Filter directories in-place to skip ignored ones
            dirs[:] = [
                d for d in dirs
                if not self._should_ignore(
                    str(Path(root).relative_to(self.root_path) / d)
                )
            ]

            for filename in files:
                abs_path = Path(root) / filename
                rel_path = str(abs_path.relative_to(self.root_path))

                # Skip ignored files
                if self._should_ignore(rel_path):
                    continue

                # Skip files that are too large
                try:
                    size = abs_path.stat().st_size
                except (IOError, OSError):
                    continue

                if size > self.max_file_size:
                    continue

                # Check if binary
                is_binary = self._is_binary(abs_path)

                # Get language
                language = self._detect_language(abs_path) if not is_binary else None

                # Read content if needed
                content = None
                line_count = 0
                sha256 = None

                if not is_binary:
                    try:
                        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            line_count = content.count("\n") + 1
                        sha256 = self._compute_sha256(abs_path)
                    except (IOError, OSError):
                        continue

                yield ScannedFile(
                    path=rel_path,
                    absolute_path=str(abs_path),
                    language=language,
                    size_bytes=size,
                    is_binary=is_binary,
                    sha256=sha256,
                    line_count=line_count,
                    content=content if self.include_content else None,
                )

    def scan_all(self) -> List[ScannedFile]:
        """Scan and return all files as a list"""
        return list(self.scan())

    def build_tree(self) -> dict:
        """Build a tree structure of the project"""
        tree = {"name": self.root_path.name, "path": "", "type": "folder", "children": []}
        path_to_node = {"": tree}

        for file in self.scan():
            parts = Path(file.path).parts
            current_path = ""

            # Create folder nodes
            for i, part in enumerate(parts[:-1]):
                parent_path = current_path
                current_path = str(Path(current_path) / part) if current_path else part

                if current_path not in path_to_node:
                    folder_node = {
                        "name": part,
                        "path": current_path,
                        "type": "folder",
                        "children": [],
                    }
                    path_to_node[parent_path]["children"].append(folder_node)
                    path_to_node[current_path] = folder_node

            # Add file node
            parent_path = str(Path(file.path).parent) if "/" in file.path or "\\" in file.path else ""
            if parent_path == ".":
                parent_path = ""

            file_node = {
                "name": parts[-1],
                "path": file.path,
                "type": "file",
                "language": file.language,
            }
            path_to_node[parent_path]["children"].append(file_node)

        # Sort children: folders first, then files, alphabetically
        def sort_children(node: dict) -> None:
            if "children" in node:
                node["children"].sort(
                    key=lambda x: (0 if x["type"] == "folder" else 1, x["name"].lower())
                )
                for child in node["children"]:
                    sort_children(child)

        sort_children(tree)
        return tree
