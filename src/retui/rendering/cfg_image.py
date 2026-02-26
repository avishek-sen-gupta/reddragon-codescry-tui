"""CFG rendering pipeline: DOT -> SVG -> PNG -> terminal display."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def dot_to_svg(dot_source: str) -> str:
    """Render DOT source to SVG string using Graphviz dot command."""
    result = subprocess.run(
        ["dot", "-Tsvg"],
        input=dot_source.encode("utf-8"),
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Graphviz error: {result.stderr.decode()}")
    return result.stdout.decode("utf-8")


def svg_to_png(svg_content: str, output_path: Path | None = None, scale: float = 1.0) -> Path:
    """Convert SVG string to PNG file using cairosvg."""
    import cairosvg

    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        output_path = Path(tmp.name)
        tmp.close()

    cairosvg.svg2png(
        bytestring=svg_content.encode("utf-8"),
        write_to=str(output_path),
        scale=scale,
    )
    return output_path


def render_cfg_png(dot_source: str, scale: float = 1.5) -> Path:
    """Full pipeline: DOT -> SVG -> PNG file."""
    svg = dot_to_svg(dot_source)
    return svg_to_png(svg, scale=scale)


def save_cfg_svg(dot_source: str, output_path: Path) -> Path:
    """Save CFG as SVG for external viewing."""
    svg = dot_to_svg(dot_source)
    output_path.write_text(svg, encoding="utf-8")
    return output_path


def open_svg_external(svg_path: Path) -> None:
    """Open SVG in system default viewer."""
    import sys
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(svg_path)])
    elif sys.platform == "linux":
        subprocess.Popen(["xdg-open", str(svg_path)])
    else:
        subprocess.Popen(["start", str(svg_path)], shell=True)
