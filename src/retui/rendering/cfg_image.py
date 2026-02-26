"""CFG rendering pipeline: Mermaid -> PNG via mmdc."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def mermaid_to_png(
    mermaid_source: str, output_path: Path | None = None, scale: int = 2
) -> Path:
    """Render Mermaid source directly to PNG using mmdc via npx."""
    with tempfile.NamedTemporaryFile(suffix=".mmd", mode="w", delete=False) as mmd:
        mmd.write(mermaid_source)
        mmd_path = Path(mmd.name)

    if output_path is None:
        output_path = mmd_path.with_suffix(".png")

    try:
        result = subprocess.run(
            [
                "npx",
                "-y",
                "@mermaid-js/mermaid-cli",
                "-i",
                str(mmd_path),
                "-o",
                str(output_path),
                "-t",
                "dark",
                "-b",
                "#1a1b26",
                "-s",
                str(scale),
            ],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(f"mmdc error: {result.stderr.decode()}")
        return output_path
    finally:
        mmd_path.unlink(missing_ok=True)


def open_external(path: Path) -> None:
    """Open a file in system default viewer."""
    import sys

    if sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    elif sys.platform == "linux":
        subprocess.Popen(["xdg-open", str(path)])
    else:
        subprocess.Popen(["start", str(path)], shell=True)
