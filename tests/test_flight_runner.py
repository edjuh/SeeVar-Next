from seevar_next.flight import runner


def test_runner_status_reports_idle_when_default_scope_offline(monkeypatch, tmp_path, capsys):
    class BrokenAdapter:
        def __init__(self, *_args, **_kwargs):
            pass

        def status(self):
            raise RuntimeError("offline")

    monkeypatch.setattr(runner, "SeestarpyAdapter", BrokenAdapter)
    monkeypatch.setattr(
        "sys.argv",
        [
            "seevar-next-flight",
            "status",
            "--proof",
            str(tmp_path / "proof.jsonl"),
            "--json-output",
            str(tmp_path / "flight.json"),
            "--text-output",
            str(tmp_path / "flight.txt"),
        ],
    )

    rc = runner.main()
    out = capsys.readouterr().out

    assert rc == 0
    assert '"running": false' in out
    assert '"state": "idle"' in out
    assert "SeeVar Next flight: IDLE" in (tmp_path / "flight.txt").read_text(encoding="utf-8")


def test_runner_status_does_not_call_seestarpy_when_scopes_offline(monkeypatch, tmp_path, capsys):
    class BrokenAdapter:
        def __init__(self, *_args, **_kwargs):
            pass

        def status(self):
            raise AssertionError("should not call seestarpy")

    config = tmp_path / "config.json"
    config.write_text(
        '{"latitude_deg": 52.0, "longitude_deg": 4.0, "scopes": [{"name": "W", "host": "192.0.2.1", "enabled": true}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "SeestarpyAdapter", BrokenAdapter)
    monkeypatch.setattr(runner, "probe_status", lambda *_args, **_kwargs: {"host": "192.0.2.1", "ok": False, "errors": ["offline"]})
    monkeypatch.setattr(
        "sys.argv",
        [
            "seevar-next-flight",
            "status",
            "--config",
            str(config),
            "--proof",
            str(tmp_path / "proof.jsonl"),
            "--json-output",
            str(tmp_path / "flight.json"),
            "--text-output",
            str(tmp_path / "flight.txt"),
            "--human",
        ],
    )

    rc = runner.main()
    out = capsys.readouterr().out

    assert rc == 0
    assert "SeeVar Next flight: IDLE" in out
    assert "W 192.0.2.1: offline" in out


def test_runner_status_returns_error_when_online_scope_status_fails(monkeypatch, tmp_path, capsys):
    class BrokenAdapter:
        def __init__(self, *_args, **_kwargs):
            pass

        def status(self):
            raise RuntimeError("plan api failed")

    config = tmp_path / "config.json"
    config.write_text(
        '{"latitude_deg": 52.0, "longitude_deg": 4.0, "scopes": [{"name": "W", "host": "192.0.2.1", "enabled": true}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "SeestarpyAdapter", BrokenAdapter)
    monkeypatch.setattr(runner, "probe_status", lambda *_args, **_kwargs: {"host": "192.0.2.1", "ok": True, "summary": "rpc ok"})
    monkeypatch.setattr(
        "sys.argv",
        [
            "seevar-next-flight",
            "status",
            "--config",
            str(config),
            "--proof",
            str(tmp_path / "proof.jsonl"),
            "--json-output",
            str(tmp_path / "flight.json"),
            "--text-output",
            str(tmp_path / "flight.txt"),
            "--human",
        ],
    )

    rc = runner.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert "SeeVar Next flight: ERROR" in out
    assert "plan api failed" in out
