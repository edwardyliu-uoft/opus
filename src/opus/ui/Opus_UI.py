from __future__ import annotations

import base64
import re
import subprocess
import sys
import zlib

import streamlit as st

from opus.ui.constants import DEFAULT_MARKDOWN_FILE
from opus.ui.util import read_markdown


def render_mermaid(code: str):
    """Renders mermaid code dynamically utilizing an image API for auto-height."""
    compressed = zlib.compress(code.strip().encode("utf-8"), 9)
    b64 = base64.urlsafe_b64encode(compressed).decode("utf-8")
    img_url = f"https://kroki.io/mermaid/svg/{b64}"

    st.markdown(
        f'<img src="{img_url}" style="max-width: 100%; height: auto;" />',
        unsafe_allow_html=True,
    )


def main():
    """The Streamlit UI application."""

    st.set_page_config(page_title="Opus UI", page_icon=":rocket:", layout="wide")
    readme_content = read_markdown(DEFAULT_MARKDOWN_FILE)

    # Split the content to identify mermaid blocks
    sections = re.split(r"```mermaid\n(.*?)\n```", readme_content, flags=re.DOTALL)

    for idx, section in enumerate(sections):
        if idx % 2 == 0:
            st.markdown(section, unsafe_allow_html=False)
        else:
            render_mermaid(section)


def ui_app(port: int, address: str):
    """Entry point for the Streamlit UI application via opus CLI."""
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            __file__,
            "--server.port",
            str(port),
            "--server.address",
            address,
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
