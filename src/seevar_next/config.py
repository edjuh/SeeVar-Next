"""SeeVar Next configuration."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class ScopeConfig(BaseModel):
    """One Seestar telescope."""

    name: str
    host: str
    model: str = "S30-Pro"
    mount: str = "eq"
    enabled: bool = True
    status_ports: list[int] = Field(default_factory=lambda: [22, 4700, 11111, 80])


class StorageConfig(BaseModel):
    """Local and NAS paths."""

    work_dir: str = "data"
    raw_dir: str = "data/raw"
    postflight_dir: str = "data/postflight"
    nas_dir: str | None = None


class AavsoConfig(BaseModel):
    """AAVSO operator settings."""

    observer_code: str = "UNKNOWN"
    target_tool_api_key_env: str = "AAVSO_TARGET_TOOL_API_KEY"


class WeatherConfig(BaseModel):
    """Weather gate settings."""

    enabled: bool = True
    provider: str = "open-meteo"
    forecast_hours: int = 8
    timeout_sec: float = 8.0
    max_cloud_cover_pct: float = 70.0
    max_precip_probability_pct: float = 20.0
    max_precip_mm: float = 0.1
    max_wind_kmh: float = 30.0
    max_gust_kmh: float = 45.0
    min_visibility_m: float = 5000.0


class SeeVarConfig(BaseModel):
    """Top-level operator config."""

    latitude_deg: float
    longitude_deg: float
    catalog: str = "campaign_targets"
    limit: int = 20
    hours: float = 24.0
    sun_alt_limit_deg: float = -12.0
    min_alt_deg: float = 25.0
    timezone: str = "Europe/Amsterdam"
    scopes: list[ScopeConfig] = Field(default_factory=list)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    aavso: AavsoConfig = Field(default_factory=AavsoConfig)
    weather: WeatherConfig = Field(default_factory=WeatherConfig)
    seestarpy_plan_path: str = "data/seestarpy_plan.json"


def default_config() -> SeeVarConfig:
    """Return a usable default config."""
    return SeeVarConfig(
        latitude_deg=52.39,
        longitude_deg=4.61,
        scopes=[
            ScopeConfig(name="Wilhelmina", host="192.168.178.251"),
            ScopeConfig(name="Anna", host="192.168.178.252", enabled=False),
        ],
    )


def load_config(path: Path) -> SeeVarConfig:
    """Load config from JSON, or return defaults."""
    if not path.exists():
        return default_config()
    return SeeVarConfig.model_validate(json.loads(path.read_text(encoding="utf-8")))
