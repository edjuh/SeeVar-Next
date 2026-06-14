"""Shared proof and pipeline models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class StepStatus(StrEnum):
    """Allowed proof status values."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"


class ProofStep(BaseModel):
    """One proof row for one target step."""

    run_id: str
    target: str
    phase: str
    step: str
    status: StepStatus
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_path: str | None = None
    reason: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class TargetPlan(BaseModel):
    """One planned target assignment."""

    name: str
    ra_deg: float
    dec_deg: float
    priority: int = 100
    exposure_sec: float = 10.0
    min_frames: int = 3
    scope: str | None = None


class PostflightProduct(BaseModel):
    """Accepted postflight output for one target."""

    target: str
    stack_fits: Path
    preview_jpeg: Path
    report_path: Path
    wcs_ok: bool
    photometry_ok: bool
