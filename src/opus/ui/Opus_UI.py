from __future__ import annotations

import subprocess
import sys

import streamlit as st

from opus.ui.constants import DEFAULT_MARKDOWN_FILE
from opus.ui.util import read_markdown


def main():
    """The Streamlit UI application."""

    st.set_page_config(page_title="Opus UI", page_icon=":rocket:", layout="wide")

    readme_content = read_markdown(DEFAULT_MARKDOWN_FILE)
    st.markdown(readme_content, unsafe_allow_html=False)


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
