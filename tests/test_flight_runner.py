from seevar_next.flight import runner


def test_runner_status_returns_json_error(monkeypatch, tmp_path, capsys):
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

    assert rc == 1
    assert '"running": false' in out
    assert "offline" in out
    assert "SeeVar Next flight: ERROR" in (tmp_path / "flight.txt").read_text(encoding="utf-8")
