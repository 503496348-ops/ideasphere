#!/usr/bin/env python3
"""Unified CLI for ideasphere. Wraps imported main with type hints."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.pipeline import main  # noqa: E402


def cli_main() -> None:
    """Entry point for the CLI."""
    main()


if __name__ == '__main__':
    cli_main()
