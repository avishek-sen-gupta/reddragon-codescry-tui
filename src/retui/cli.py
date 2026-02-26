"""CLI entry point: poetry run retui --config repos.json"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from retui.app import RevEngApp
from retui.session.config import AppConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Rev-Eng TUI — reverse engineering explorer")
    parser.add_argument(
        "--config",
        type=str,
        default="config/repos.json",
        help="Path to repos.json config file",
    )
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    if not config_path.exists():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = AppConfig.load(config_path)
    app = RevEngApp(config)
    app.run()


if __name__ == "__main__":
    main()
