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
    target_type: str | None = None
    max_mag: float | None = None
    min_mag: float | None = None
    cadence_days: float | None = None
    duration_sec: int = 600
    best_start_utc: datetime | None = None
    best_end_utc: datetime | None = None
    max_alt_deg: float | None = None
    source: str | None = None
    notes: dict[str, Any] = Field(default_factory=dict)


class NightlyPlan(BaseModel):
    """A strict preflight target handoff."""

    run_id: str
    created_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    site_latitude_deg: float
    site_longitude_deg: float
    targets: list[TargetPlan] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PostflightProduct(BaseModel):
    """Accepted postflight output for one target."""

    target: str
    stack_fits: Path
    preview_jpeg: Path
    report_path: Path
    wcs_ok: bool
    photometry_ok: bool
    accepted_frames: int
    rejected_frames: int
    instrumental_mag: float
    calibrated_mag: float | None = None
    mag_error: float | None = None


class ComparisonStar(BaseModel):
    """One comparison star used for postflight calibration."""

    id: str
    ra_deg: float
    dec_deg: float
    mag: float


class PhotometryCatalog(BaseModel):
    """Minimal target and comparison-star catalog for one object."""

    target: str
    ra_deg: float
    dec_deg: float
    filter_name: str = "TG"
    observer_code: str = "UNKNOWN"
    comparison_stars: list[ComparisonStar] = Field(default_factory=list)
