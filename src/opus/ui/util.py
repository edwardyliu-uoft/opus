from __future__ import annotations

from pathlib import Path


def read_markdown(path: Path):
    """Reads the content of a Markdown file."""
    try:
        with open(path, "r", encoding="utf-8") as markdown_file:
            markdown_content = markdown_file.read()
        return markdown_content
    except FileNotFoundError:
        return f"Error: file '{path}' not found."
    except Exception as err:
        return f"An error occurred: {err}"
