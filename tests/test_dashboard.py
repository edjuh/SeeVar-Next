import json

from seevar_next.dashboard import render_dashboard


def test_dashboard_renders_human_status(tmp_path):
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    config_dir.mkdir()
    data_dir.mkdir()
    config_path = config_dir / "seevar-next.json"
    config_path.write_text(json.dumps({"latitude_deg": 52.39, "longitude_deg": 4.61}), encoding="utf-8")
    (data_dir / "readiness.txt").write_text("SeeVar Next readiness: GO\n", encoding="utf-8")
    (data_dir / "tonights_plan.json").write_text(
        json.dumps({"targets": [{"name": "ST Boo", "target_type": "UGSU", "max_alt_deg": 55.2}]}),
        encoding="utf-8",
    )
    (data_dir / "status.json").write_text(
        json.dumps({"targets": {"ST Boo": {"phase": "flight", "step": "track", "status": "pass"}}}),
        encoding="utf-8",
    )

    html = render_dashboard(config_path, data_dir)

    assert "SeeVar Next readiness: GO" in html
    assert "ST Boo" in html
    assert "readiness.txt" in html
