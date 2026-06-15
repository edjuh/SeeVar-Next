"""Postflight proof pipeline."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.time import Time
from astropy.visualization import PercentileInterval, SqrtStretch
from astropy.wcs import WCS
from photutils.aperture import CircularAperture, CircularAnnulus, aperture_photometry
from PIL import Image

from seevar_next.models import (
    PhotometryCatalog,
    PostflightProduct,
    ProofStep,
    StepStatus,
)
from seevar_next.proof.ledger import ProofLedger


SATURATION_ADU = 58000.0
MAX_SATURATED_FRACTION = 0.001
MIN_STD_ADU = 2.0
MAX_TRAIL_ELONGATION = 5.0
MIN_TRAIL_PIXELS = 8
APERTURE_RADIUS_PX = 4.0
ANNULUS_INNER_PX = 8.0
ANNULUS_OUTER_PX = 12.0


def discover_fits(input_dir: Path) -> list[Path]:
    """Return FITS files below an input directory."""
    return sorted(input_dir.rglob("*.fit")) + sorted(input_dir.rglob("*.fits"))


def require_frames(input_dir: Path, minimum: int = 1) -> list[Path]:
    """Return frames or raise a clear failure."""
    frames = discover_fits(input_dir)
    if len(frames) < minimum:
        raise ValueError(f"need {minimum} FITS frame(s), found {len(frames)}")
    return frames


def load_catalog(path: Path) -> PhotometryCatalog:
    """Load one target photometry catalog."""
    return PhotometryCatalog.model_validate(json.loads(path.read_text(encoding="utf-8")))


def read_fits_data(path: Path) -> tuple[np.ndarray, fits.Header]:
    """Read one FITS image and header."""
    with fits.open(path, memmap=False) as hdul:
        data = np.asarray(hdul[0].data, dtype=np.float64)
        header = hdul[0].header.copy()
    if data.ndim != 2:
        raise ValueError(f"{path.name}: expected 2D FITS image, got shape {data.shape}")
    return data, header


def _component_elongation(coords: np.ndarray) -> float:
    """Return major/minor axis ratio for one bright component."""
    if len(coords) < MIN_TRAIL_PIXELS:
        return 1.0
    centered = coords.astype(float) - coords.mean(axis=0)
    cov = np.cov(centered, rowvar=False)
    eig = np.linalg.eigvalsh(cov)
    minor = max(float(eig[0]), 1e-6)
    major = max(float(eig[-1]), minor)
    return math.sqrt(major / minor)


def trail_elongation(data: np.ndarray) -> float:
    """Estimate worst bright-source elongation."""
    finite = data[np.isfinite(data)]
    if finite.size == 0:
        return 1.0
    _, median, std = sigma_clipped_stats(finite, sigma=3.0)
    threshold = float(median + 6.0 * std)
    mask = data >= threshold
    seen = np.zeros(mask.shape, dtype=bool)
    worst = 1.0
    height, width = mask.shape
    for y, x in np.argwhere(mask):
        if seen[y, x]:
            continue
        stack = [(int(y), int(x))]
        coords = []
        seen[y, x] = True
        while stack:
            cy, cx = stack.pop()
            coords.append((cy, cx))
            for ny in range(max(0, cy - 1), min(height, cy + 2)):
                for nx in range(max(0, cx - 1), min(width, cx + 2)):
                    if mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        worst = max(worst, _component_elongation(np.asarray(coords)))
    return float(worst)


def qc_frame(path: Path) -> tuple[bool, str, dict]:
    """Return whether a frame is usable for stacking."""
    try:
        data, header = read_fits_data(path)
    except Exception as exc:
        return False, str(exc), {}

    finite = data[np.isfinite(data)]
    if finite.size == 0:
        return False, "no finite pixels", {}

    saturated_fraction = float(np.mean(finite >= SATURATION_ADU))
    mean, median, std = sigma_clipped_stats(finite, sigma=3.0)
    meta = {
        "mean": float(mean),
        "median": float(median),
        "std": float(std),
        "saturated_fraction": saturated_fraction,
        "date_obs": header.get("DATE-OBS"),
    }
    meta["trail_elongation"] = trail_elongation(data)

    if saturated_fraction > MAX_SATURATED_FRACTION:
        return False, "saturated frame", meta
    if float(std) < MIN_STD_ADU:
        return False, "low contrast frame", meta
    if meta["trail_elongation"] > MAX_TRAIL_ELONGATION:
        return False, "trailed frame", meta
    return True, "accepted", meta


def load_accepted_frames(paths: list[Path]) -> tuple[list[np.ndarray], list[Path], list[tuple[Path, str, dict]]]:
    """Load frames that pass QC."""
    accepted_data = []
    accepted_paths = []
    rejected = []
    for path in paths:
        ok, reason, meta = qc_frame(path)
        if not ok:
            rejected.append((path, reason, meta))
            continue
        data, _ = read_fits_data(path)
        accepted_data.append(data)
        accepted_paths.append(path)
    return accepted_data, accepted_paths, rejected


def median_stack(frames: list[np.ndarray]) -> np.ndarray:
    """Build a median stack from accepted frames."""
    if not frames:
        raise ValueError("no accepted frames to stack")
    shapes = {frame.shape for frame in frames}
    if len(shapes) != 1:
        raise ValueError(f"frame shapes differ: {sorted(shapes)}")
    return np.median(np.stack(frames, axis=0), axis=0)


def write_stack(stack: np.ndarray, reference_frame: Path, output_path: Path, target: str) -> None:
    """Write stacked FITS using the first accepted frame header."""
    _, header = read_fits_data(reference_frame)
    header["OBJECT"] = target
    header["SEEVCOMB"] = "MEDIAN"
    header["SEEVSTAK"] = True
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fits.PrimaryHDU(data=stack.astype(np.float32), header=header).writeto(output_path, overwrite=True)


def write_preview(stack: np.ndarray, output_path: Path) -> None:
    """Write a stretched JPEG preview."""
    interval = PercentileInterval(99.5)
    lo, hi = interval.get_limits(stack)
    if hi <= lo:
        hi = lo + 1.0
    scaled = np.clip((stack - lo) / (hi - lo), 0.0, 1.0)
    stretched = SqrtStretch()(scaled)
    preview = (stretched * 255.0).astype(np.uint8)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(preview).save(output_path, format="JPEG", quality=90)


def require_wcs(stack_fits: Path) -> WCS:
    """Return a valid celestial WCS or fail."""
    header = fits.getheader(stack_fits)
    wcs = WCS(header)
    if not wcs.has_celestial:
        raise ValueError("stack has no celestial WCS")
    return wcs


def aperture_flux(data: np.ndarray, x: float, y: float) -> tuple[float, float]:
    """Measure background-subtracted aperture flux."""
    aperture = CircularAperture((x, y), r=APERTURE_RADIUS_PX)
    annulus = CircularAnnulus((x, y), r_in=ANNULUS_INNER_PX, r_out=ANNULUS_OUTER_PX)
    phot = aperture_photometry(data, [aperture, annulus])
    aperture_sum = float(phot["aperture_sum_0"][0])
    annulus_sum = float(phot["aperture_sum_1"][0])
    annulus_area = float(annulus.area)
    aperture_area = float(aperture.area)
    background_per_px = annulus_sum / annulus_area
    flux = aperture_sum - background_per_px * aperture_area
    if flux <= 0:
        raise ValueError("non-positive aperture flux")
    flux_error = math.sqrt(max(aperture_sum, 1.0))
    return flux, flux_error


def instrumental_mag(flux: float) -> float:
    """Convert flux to instrumental magnitude."""
    return -2.5 * math.log10(flux)


def run_photometry(stack_fits: Path, catalog: PhotometryCatalog) -> dict:
    """Measure target and comparison stars with photutils."""
    data = np.asarray(fits.getdata(stack_fits), dtype=np.float64)
    wcs = require_wcs(stack_fits)

    target_x, target_y = wcs.world_to_pixel_values(catalog.ra_deg, catalog.dec_deg)
    target_flux, target_flux_error = aperture_flux(data, float(target_x), float(target_y))
    target_inst = instrumental_mag(target_flux)

    comp_rows = []
    zero_points = []
    for comp in catalog.comparison_stars:
        x, y = wcs.world_to_pixel_values(comp.ra_deg, comp.dec_deg)
        flux, flux_error = aperture_flux(data, float(x), float(y))
        inst = instrumental_mag(flux)
        zp = comp.mag - inst
        comp_rows.append(
            {
                "id": comp.id,
                "flux": flux,
                "flux_error": flux_error,
                "instrumental_mag": inst,
                "catalog_mag": comp.mag,
                "zero_point": zp,
            }
        )
        zero_points.append(zp)

    if not zero_points:
        raise ValueError("no comparison stars")

    zero_points_array = np.asarray(zero_points, dtype=float)
    _, zp_median, zp_std = sigma_clipped_stats(zero_points_array, sigma=2.5)
    calibrated_mag = float(target_inst + zp_median)
    mag_error = float(max(zp_std, 1.0857 * target_flux_error / target_flux))

    return {
        "target": catalog.target,
        "filter": catalog.filter_name,
        "observer_code": catalog.observer_code,
        "target_flux": target_flux,
        "instrumental_mag": target_inst,
        "calibrated_mag": calibrated_mag,
        "mag_error": mag_error,
        "comparison_stars": comp_rows,
    }


def write_photometry_csv(result: dict, output_path: Path) -> None:
    """Write a compact photometry CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["target", "filter", "instrumental_mag", "calibrated_mag", "mag_error", "comparison_count"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "target": result["target"],
                "filter": result["filter"],
                "instrumental_mag": f"{result['instrumental_mag']:.5f}",
                "calibrated_mag": f"{result['calibrated_mag']:.5f}",
                "mag_error": f"{result['mag_error']:.5f}",
                "comparison_count": len(result["comparison_stars"]),
            }
        )


def write_aavso_report(result: dict, stack_fits: Path, output_path: Path) -> None:
    """Write a minimal AAVSO Extended-format staging report."""
    header = fits.getheader(stack_fits)
    date_obs = header.get("DATE-OBS")
    if date_obs:
        jd = Time(date_obs, format="isot", scale="utc").jd
    else:
        jd = Time.now().jd

    lines = [
        "#TYPE=Extended",
        f"#OBSCODE={result['observer_code']}",
        "#SOFTWARE=SeeVar Next",
        "#DELIM=,",
        "#DATE=JD",
        "#OBSTYPE=CCD",
        "#NAME,DATE,MAG,MERR,FILTER,TRANS,MTYPE,CNAME,CMAG,KNAME,KMAG,AMASS,GROUP,CHART,NOTES",
        (
            f"{result['target']},{jd:.6f},{result['calibrated_mag']:.4f},"
            f"{result['mag_error']:.4f},{result['filter']},NO,STD,ENSEMBLE,na,na,na,na,na,na,"
            f"Stack={stack_fits.name}; comps={len(result['comparison_stars'])}"
        ),
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def postflight_target(input_dir: Path, output_dir: Path, catalog_path: Path, run_id: str = "manual") -> PostflightProduct:
    """Run strict postflight for one target folder."""
    catalog = load_catalog(catalog_path)
    ledger = ProofLedger(output_dir / "proof.jsonl")

    def proof(step: str, status: StepStatus, evidence: Path | None = None, reason: str | None = None, meta: dict | None = None) -> None:
        ledger.append(
            ProofStep(
                run_id=run_id,
                target=catalog.target,
                phase="postflight",
                step=step,
                status=status,
                evidence_path=str(evidence) if evidence else None,
                reason=reason,
                meta=meta or {},
            )
        )

    try:
        frames = require_frames(input_dir)
        proof("ingest", StepStatus.PASS, meta={"frames": len(frames)})

        accepted, accepted_paths, rejected = load_accepted_frames(frames)
        if not accepted:
            proof("frame_qc", StepStatus.FAIL, reason="no accepted frames", meta={"rejected": len(rejected)})
            raise ValueError("no accepted frames")
        proof("frame_qc", StepStatus.PASS, meta={"accepted": len(accepted), "rejected": len(rejected)})

        try:
            stack = median_stack(accepted)
            stack_fits = output_dir / f"{catalog.target.replace(' ', '_')}_stack.fits"
            write_stack(stack, accepted_paths[0], stack_fits, catalog.target)
            proof("stack", StepStatus.PASS, evidence=stack_fits, meta={"accepted": len(accepted)})
        except Exception as exc:
            proof("stack", StepStatus.FAIL, reason=str(exc))
            raise

        try:
            preview_jpeg = output_dir / f"{catalog.target.replace(' ', '_')}_stack.jpg"
            write_preview(stack, preview_jpeg)
            proof("preview", StepStatus.PASS, evidence=preview_jpeg)
        except Exception as exc:
            proof("preview", StepStatus.FAIL, reason=str(exc))
            raise

        try:
            require_wcs(stack_fits)
            proof("wcs", StepStatus.PASS, evidence=stack_fits)
        except Exception as exc:
            proof("wcs", StepStatus.FAIL, evidence=stack_fits, reason=str(exc))
            raise

        try:
            photometry = run_photometry(stack_fits, catalog)
            photometry_csv = output_dir / f"{catalog.target.replace(' ', '_')}_photometry.csv"
            write_photometry_csv(photometry, photometry_csv)
            proof("photometry", StepStatus.PASS, evidence=photometry_csv)
        except Exception as exc:
            proof("photometry", StepStatus.FAIL, reason=str(exc))
            raise

        try:
            report_path = output_dir / f"{catalog.target.replace(' ', '_')}_aavso.txt"
            write_aavso_report(photometry, stack_fits, report_path)
            proof("report", StepStatus.PASS, evidence=report_path)
        except Exception as exc:
            proof("report", StepStatus.FAIL, reason=str(exc))
            raise

        return PostflightProduct(
            target=catalog.target,
            stack_fits=stack_fits,
            preview_jpeg=preview_jpeg,
            report_path=report_path,
            wcs_ok=True,
            photometry_ok=True,
            accepted_frames=len(accepted),
            rejected_frames=len(rejected),
            instrumental_mag=float(photometry["instrumental_mag"]),
            calibrated_mag=float(photometry["calibrated_mag"]),
            mag_error=float(photometry["mag_error"]),
        )
    except Exception as exc:
        proof("complete", StepStatus.FAIL, reason=str(exc))
        raise


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run SeeVar Next postflight for one target folder.")
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("data/postflight"))
    parser.add_argument("--run-id", default="manual")
    return parser.parse_args()


def main() -> int:
    """CLI entry point."""
    args = parse_args()
    product = postflight_target(args.input_dir, args.output_dir, args.catalog, run_id=args.run_id)
    print(product.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
