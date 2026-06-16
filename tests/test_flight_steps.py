import json

from seevar_next.flight.steps import render_step_summary, run_step_dryrun


def _plan(tmp_path):
    path = tmp_path / "plan.json"
    path.write_text(
        json.dumps(
            {
                "run_id": "run-1",
                "site_latitude_deg": 52.0,
                "site_longitude_deg": 4.0,
                "targets": [
                    {"name": "ST Boo", "ra_deg": 210.0, "dec_deg": 40.0},
                    {"name": "TT Boo", "ra_deg": 211.0, "dec_deg": 41.0},
                    {"name": "SS Cyg", "ra_deg": 320.0, "dec_deg": 43.0},
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_step_dryrun_success(tmp_path):
    result = run_step_dryrun(
        _plan(tmp_path),
        tmp_path / "steps.jsonl",
        tmp_path / "steps.json",
        tmp_path / "steps.txt",
        limit=2,
    )

    assert result["preflight_ok"] is True
    assert result["postflight_ok"] is True
    assert result["failed"] == 0
    assert result["proof_rows"] == 40
    assert "ST Boo" in (tmp_path / "steps.txt").read_text(encoding="utf-8")


def test_step_dryrun_preflight_failure_skips_target_chain(tmp_path):
    result = run_step_dryrun(
        _plan(tmp_path),
        tmp_path / "steps.jsonl",
        tmp_path / "steps.json",
        tmp_path / "steps.txt",
        limit=1,
        fail_code="P2",
    )

    assert result["preflight_ok"] is False
    assert result["postflight_ok"] is False
    assert result["failed"] == 1
    assert result["skipped"] > 0
    assert "Preflight: fail" in render_step_summary(result)
