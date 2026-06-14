import json
from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits
from astropy.wcs import WCS

from seevar_next.models import StepStatus
from seevar_next.postflight.pipeline import postflight_target
from seevar_next.proof.ledger import ProofLedger


def make_wcs_header() -> fits.Header:
    wcs = WCS(naxis=2)
    wcs.wcs.crpix = [50.0, 50.0]
    wcs.wcs.cdelt = np.array([-0.001, 0.001])
    wcs.wcs.crval = [210.0, 40.0]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    header = wcs.to_header()
    header["DATE-OBS"] = "2026-06-14T22:00:00"
    return header


def add_star(data: np.ndarray, x: int, y: int, peak: float) -> None:
    yy, xx = np.indices(data.shape)
    data += peak * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * 1.5**2))


def write_frame(path: Path, header: fits.Header, saturated: bool = False) -> None:
    rng = np.random.default_rng(42)
    data = rng.normal(1000.0, 8.0, size=(100, 100))
    add_star(data, 50, 50, 12000)
    add_star(data, 40, 50, 9000)
    add_star(data, 60, 50, 7000)
    if saturated:
        data[10:20, 10:20] = 65000
    fits.PrimaryHDU(data=data.astype(np.float32), header=header).writeto(path)


def write_catalog(path: Path) -> None:
    payload = {
        "target": "ST Boo",
        "ra_deg": 210.0,
        "dec_deg": 40.0,
        "filter_name": "TG",
        "observer_code": "TST",
        "comparison_stars": [
            {"id": "C1", "ra_deg": 210.01, "dec_deg": 40.0, "mag": 12.1},
            {"id": "C2", "ra_deg": 209.99, "dec_deg": 40.0, "mag": 12.4},
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_catalog_without_comps(path: Path) -> None:
    payload = {
        "target": "ST Boo",
        "ra_deg": 210.0,
        "dec_deg": 40.0,
        "filter_name": "TG",
        "observer_code": "TST",
        "comparison_stars": [],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_postflight_success_creates_one_product_set(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    header = make_wcs_header()
    for idx in range(3):
        write_frame(input_dir / f"frame_{idx}.fits", header)
    write_frame(input_dir / "bad_saturated.fits", header, saturated=True)
    catalog_path = tmp_path / "catalog.json"
    write_catalog(catalog_path)

    product = postflight_target(input_dir, output_dir, catalog_path, run_id="test-run")

    assert product.accepted_frames == 3
    assert product.rejected_frames == 1
    assert product.stack_fits.exists()
    assert product.preview_jpeg.exists()
    assert product.report_path.exists()
    assert product.wcs_ok is True
    assert product.photometry_ok is True

    rows = ProofLedger(output_dir / "proof.jsonl").read_all()
    passed_steps = {row.step for row in rows if row.status == StepStatus.PASS}
    assert {"ingest", "frame_qc", "stack", "preview", "wcs", "photometry", "report"} <= passed_steps


def test_postflight_blocks_missing_wcs(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    header = fits.Header()
    header["DATE-OBS"] = "2026-06-14T22:00:00"
    for idx in range(3):
        write_frame(input_dir / f"frame_{idx}.fits", header)
    catalog_path = tmp_path / "catalog.json"
    write_catalog(catalog_path)

    with pytest.raises(ValueError, match="no celestial WCS"):
        postflight_target(input_dir, output_dir, catalog_path, run_id="test-run")

    rows = ProofLedger(output_dir / "proof.jsonl").read_all()
    assert rows[-1].step == "complete"
    assert rows[-1].status == StepStatus.FAIL


def test_postflight_blocks_missing_comparison_stars(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    header = make_wcs_header()
    for idx in range(3):
        write_frame(input_dir / f"frame_{idx}.fits", header)
    catalog_path = tmp_path / "catalog.json"
    write_catalog_without_comps(catalog_path)

    with pytest.raises(ValueError, match="no comparison stars"):
        postflight_target(input_dir, output_dir, catalog_path, run_id="test-run")

    rows = ProofLedger(output_dir / "proof.jsonl").read_all()
    assert any(row.step == "photometry" and row.status == StepStatus.FAIL for row in rows)
