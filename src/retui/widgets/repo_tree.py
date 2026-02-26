"""File/symbol tree widget built from CTags paths."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

from textual.widgets import Tree


class RepoTree(Tree):
    """Displays the file tree for a repository, built from CTags entries."""

    def __init__(self, repo_name: str, **kwargs: Any) -> None:
        super().__init__(repo_name, **kwargs)
        self._file_paths: list[str] = []

    def populate(self, file_paths: list[str]) -> None:
        """Build tree from a list of file paths."""
        self._file_paths = sorted(set(file_paths))
        self.clear()

        # Build tree structure from paths
        nodes: dict[str, Any] = {}
        for path_str in self._file_paths:
            parts = PurePosixPath(path_str).parts
            current = self.root
            accumulated = ""
            for i, part in enumerate(parts):
                accumulated = f"{accumulated}/{part}" if accumulated else part
                if accumulated not in nodes:
                    is_leaf = i == len(parts) - 1
                    if is_leaf:
                        node = current.add_leaf(f"[#c0caf5]{part}[/]", data=path_str)
                    else:
                        node = current.add(f"[#7dcfff]{part}/[/]", data=accumulated)
                    nodes[accumulated] = node
                current = nodes[accumulated]

        self.root.expand()
        # Expand single-child directories
        self._auto_expand(self.root)

    def _auto_expand(self, node: Any) -> None:
        """Auto-expand directories with only one child."""
        children = list(node.children)
        if len(children) == 1 and children[0].allow_expand:
            children[0].expand()
            self._auto_expand(children[0])

    def mark_file_has_signals(self, file_path: str) -> None:
        """Highlight files that have integration signals."""
        for node in self._walk(self.root):
            if node.data == file_path:
                parts = PurePosixPath(file_path).parts
                node.set_label(f"[#e0af68]{parts[-1]}[/]")
                break

    def _walk(self, node: Any):
        """Recursively yield all descendant nodes."""
        for child in node.children:
            yield child
            yield from self._walk(child)
