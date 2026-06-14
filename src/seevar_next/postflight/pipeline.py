"""Postflight contract skeleton."""

from __future__ import annotations

from pathlib import Path


def discover_fits(input_dir: Path) -> list[Path]:
    """Return FITS files below an input directory."""
    return sorted(input_dir.glob("*.fit")) + sorted(input_dir.glob("*.fits"))


def require_frames(input_dir: Path, minimum: int = 1) -> list[Path]:
    """Return frames or raise a clear failure."""
    frames = discover_fits(input_dir)
    if len(frames) < minimum:
        raise ValueError(f"need {minimum} FITS frame(s), found {len(frames)}")
    return frames
