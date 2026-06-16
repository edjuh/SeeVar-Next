from datetime import datetime, timezone
import json

from seevar_next.models import TargetPlan
from seevar_next.flight.dryrun import run_dryrun
from seevar_next.monitor.status import build_status
from seevar_next.preflight.catalogs import load_catalog_paths
from seevar_next.preflight.planner import build_nightly_plan, write_plan
from seevar_next.preflight.seestarpy_plan import build_seestarpy_plan


def test_load_seevar_catalog_shape(tmp_path):
    path = tmp_path / "campaign_targets.json"
    path.write_text(
        json.dumps({"targets": [{"name": "ST Boo", "ra": 230.0, "dec": 45.0, "priority": 2}]}),
        encoding="utf-8",
    )

    targets = load_catalog_paths([path])

    assert targets[0].name == "ST Boo"
    assert targets[0].ra_deg == 230.0


def test_nightly_plan_filters_visible_dark_target():
    targets = [TargetPlan(name="Zenithish", ra_deg=270.0, dec_deg=52.0, priority=1)]

    plan = build_nightly_plan(
        targets,
        latitude_deg=52.39,
        longitude_deg=4.61,
        start_utc=datetime(2026, 6, 14, 20, 0, tzinfo=timezone.utc),
        hours=10,
        sun_alt_limit_deg=-6.0,
        min_alt_deg=15.0,
        limit=3,
        run_id="test",
    )

    assert [target.name for target in plan.targets] == ["Zenithish"]


def test_export_seestarpy_plan(tmp_path):
    plan_path = tmp_path / "plan.json"
    out_path = tmp_path / "seestarpy.json"
    plan_path.write_text(
        json.dumps(
            {
                "targets": [
                    {
                        "name": "ST Boo",
                        "ra_deg": 230.0,
                        "dec_deg": 45.0,
                        "duration_sec": 600,
                        "best_start_utc": "2026-06-14T22:00:00+00:00",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    payload = build_seestarpy_plan(plan_path, "Europe/Amsterdam", "SeeVar", "2026-06-14")
    out_path.write_text(json.dumps(payload), encoding="utf-8")

    assert payload["list"][0]["target_name"] == "ST Boo"


def test_dryrun_writes_three_target_proof_and_status(tmp_path):
    plan = build_nightly_plan(
        [
            TargetPlan(name="A", ra_deg=270.0, dec_deg=52.0, priority=1),
            TargetPlan(name="B", ra_deg=271.0, dec_deg=52.0, priority=2),
            TargetPlan(name="C", ra_deg=272.0, dec_deg=52.0, priority=3),
        ],
        latitude_deg=52.39,
        longitude_deg=4.61,
        start_utc=datetime(2026, 6, 14, 20, 0, tzinfo=timezone.utc),
        sun_alt_limit_deg=-6.0,
        min_alt_deg=15.0,
        run_id="dry",
    )
    plan_path = tmp_path / "plan.json"
    proof_path = tmp_path / "proof.jsonl"
    status_path = tmp_path / "status.json"
    write_plan(plan, plan_path)

    status = run_dryrun(plan_path, proof_path, status_path, limit=3)

    assert status["proof_rows"] == 27
    assert set(status["targets"]) == {"A", "B", "C"}
    assert build_status(proof_path, plan_path)["status_counts"]["pass"] == 27
