"""Provides the local files navigation pane."""

from __future__ import annotations

from os import getenv
from pathlib import Path
from typing import Iterable

from httpx import URL
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import DirectoryTree

from ...utility import maybe_markdown
from .navigation_pane import NavigationPane


class FilteredDirectoryTree(DirectoryTree):
    """A `DirectoryTree` filtered for the Markdown viewer."""

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        """Filter the directory tree for the Markdown viewer.

        Args:
            paths: The paths to be filtered.

        Returns:
            The parts filtered for the Markdown viewer.

        The filtered set will include all filesystem entries that aren't
        hidden (in a Unix sense of hidden) which are either a directory or a
        file that looks like it could be a Markdown document.
        """
        return [
            path
            for path in paths
            if not path.name.startswith(".")
            and path.is_dir()
            or (path.is_file() and maybe_markdown(path))
        ]


class LocalFiles(NavigationPane):
    """Local file picking navigation pane."""

    DEFAULT_CSS = """
    LocalFiles {
        height: 100%;
    }

    LocalFiles > DirectoryTree {
        background: $primary;
        width: 1fr;
    }
    """

    def __init__(self) -> None:
        """Initialise the local files navigation pane."""
        super().__init__("Local")

    def compose(self) -> ComposeResult:
        """Compose the child widgets."""
        yield FilteredDirectoryTree(getenv("HOME") or ".")

    async def chdir(self, path: Path) -> None:
        """Change the filesystem view to the given directory."""
        # At the moment Textual's DirectoryTree doesn't support changing
        # directory to a new root, so here we're going to remove it and
        # mount a fresh one with a new root.
        await self.query_one(FilteredDirectoryTree).remove()
        await self.mount(FilteredDirectoryTree(path))

    def set_focus_within(self) -> None:
        """Focus the directory tree.."""
        self.query_one(DirectoryTree).focus()

    class Goto(Message):
        """Message that requests the viewer goes to a given location."""

        def __init__(self, location: Path | URL) -> None:
            """Initialise the history goto message.

            Args:
                location: The location to go to.
            """
            super().__init__()
            self.location = location
            """The location to go to."""

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Handle a file being selected in the directory tree.

        Args:
            event: The direct tree selection event.
        """
        event.stop()
        self.post_message(self.Goto(Path(event.path)))