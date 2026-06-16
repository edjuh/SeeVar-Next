"""Weather gates for unattended runs."""

from __future__ import annotations

from typing import Any

import httpx

from seevar_next.config import SeeVarConfig

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather(config: SeeVarConfig) -> dict[str, Any]:
    """Fetch a compact Open-Meteo forecast."""
    if config.weather.provider != "open-meteo":
        raise ValueError(f"unsupported weather provider: {config.weather.provider}")
    params: dict[str, str | int | float] = {
        "latitude": config.latitude_deg,
        "longitude": config.longitude_deg,
        "timezone": config.timezone,
        "forecast_hours": config.weather.forecast_hours,
        "current": "temperature_2m,cloud_cover,precipitation,wind_speed_10m,wind_gusts_10m",
        "hourly": "cloud_cover,precipitation_probability,precipitation,wind_speed_10m,wind_gusts_10m,visibility",
        "wind_speed_unit": "kmh",
    }
    response = httpx.get(OPEN_METEO_URL, params=params, timeout=config.weather.timeout_sec)
    response.raise_for_status()
    return response.json()


def _numbers(values: list[Any] | None) -> list[float]:
    """Return finite numeric weather values."""
    return [float(value) for value in values or [] if value is not None]


def evaluate_weather(config: SeeVarConfig, payload: dict[str, Any]) -> dict[str, Any]:
    """Evaluate weather payload against configured gates."""
    if not config.weather.enabled:
        return {"ok": True, "disabled": True, "summary": "weather disabled", "reasons": []}

    hourly = payload.get("hourly") or {}
    current = payload.get("current") or {}
    cloud = _numbers(hourly.get("cloud_cover")) or _numbers([current.get("cloud_cover")])
    precip_prob = _numbers(hourly.get("precipitation_probability"))
    precip = _numbers(hourly.get("precipitation")) or _numbers([current.get("precipitation")])
    wind = _numbers(hourly.get("wind_speed_10m")) or _numbers([current.get("wind_speed_10m")])
    gust = _numbers(hourly.get("wind_gusts_10m")) or _numbers([current.get("wind_gusts_10m")])
    visibility = _numbers(hourly.get("visibility"))

    metrics = {
        "max_cloud_cover_pct": max(cloud) if cloud else None,
        "max_precip_probability_pct": max(precip_prob) if precip_prob else None,
        "max_precip_mm": max(precip) if precip else None,
        "max_wind_kmh": max(wind) if wind else None,
        "max_gust_kmh": max(gust) if gust else None,
        "min_visibility_m": min(visibility) if visibility else None,
        "temperature_c": current.get("temperature_2m"),
    }
    reasons = []
    if metrics["max_cloud_cover_pct"] is not None and metrics["max_cloud_cover_pct"] > config.weather.max_cloud_cover_pct:
        reasons.append(f"cloud {metrics['max_cloud_cover_pct']:.0f}% > {config.weather.max_cloud_cover_pct:.0f}%")
    if metrics["max_precip_probability_pct"] is not None and metrics["max_precip_probability_pct"] > config.weather.max_precip_probability_pct:
        reasons.append(f"precip probability {metrics['max_precip_probability_pct']:.0f}% > {config.weather.max_precip_probability_pct:.0f}%")
    if metrics["max_precip_mm"] is not None and metrics["max_precip_mm"] > config.weather.max_precip_mm:
        reasons.append(f"precip {metrics['max_precip_mm']:.1f} mm > {config.weather.max_precip_mm:.1f} mm")
    if metrics["max_wind_kmh"] is not None and metrics["max_wind_kmh"] > config.weather.max_wind_kmh:
        reasons.append(f"wind {metrics['max_wind_kmh']:.0f} km/h > {config.weather.max_wind_kmh:.0f} km/h")
    if metrics["max_gust_kmh"] is not None and metrics["max_gust_kmh"] > config.weather.max_gust_kmh:
        reasons.append(f"gust {metrics['max_gust_kmh']:.0f} km/h > {config.weather.max_gust_kmh:.0f} km/h")
    if metrics["min_visibility_m"] is not None and metrics["min_visibility_m"] < config.weather.min_visibility_m:
        reasons.append(f"visibility {metrics['min_visibility_m']:.0f} m < {config.weather.min_visibility_m:.0f} m")

    summary = (
        f"cloud {metrics['max_cloud_cover_pct']:.0f}%"
        if metrics["max_cloud_cover_pct"] is not None
        else "cloud unknown"
    )
    if metrics["max_precip_probability_pct"] is not None:
        summary += f", precip {metrics['max_precip_probability_pct']:.0f}%"
    if metrics["max_wind_kmh"] is not None:
        summary += f", wind {metrics['max_wind_kmh']:.0f} km/h"
    return {"ok": not reasons, "summary": summary, "reasons": reasons, "metrics": metrics, "source": OPEN_METEO_URL}
