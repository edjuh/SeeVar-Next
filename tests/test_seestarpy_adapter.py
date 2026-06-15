import json
import sys
from types import SimpleNamespace

import pytest

from seevar_next.flight.seestarpy_adapter import SeestarpyAdapter, validate_plan_payload
from seevar_next.proof.ledger import ProofLedger


def plan_payload():
    return {
        "plan_name": "SeeVar",
        "update_time_seestar": "2026.06.15",
        "list": [
            {
                "target_id": 1,
                "target_name": "ST Boo",
                "target_ra_dec": [12.0, 40.0],
                "start_min": 1320,
                "duration_min": 10,
            }
        ],
    }


def test_validate_plan_payload_requires_targets():
    with pytest.raises(ValueError, match="plan list is empty"):
        validate_plan_payload({"plan_name": "x", "update_time_seestar": "2026.06.15", "list": []})


def test_submit_and_status_write_proof(tmp_path, monkeypatch):
    submitted = {}

    def set_view_plan(payload):
        submitted["payload"] = payload

    def get_running_plan():
        return {"state": "running", "plan": submitted["payload"]}

    monkeypatch.setitem(sys.modules, "seestarpy.plan", SimpleNamespace(set_view_plan=set_view_plan, get_running_plan=get_running_plan))
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan_payload()), encoding="utf-8")
    proof_path = tmp_path / "proof.jsonl"

    adapter = SeestarpyAdapter(proof_path, "test")
    adapter.submit_file(plan_path)
    status = adapter.status()

    assert status["state"] == "running"
    rows = ProofLedger(proof_path).read_all()
    assert [row.step for row in rows] == ["validate_plan", "submit_plan", "running_plan"]


def test_validate_does_not_require_seestarpy(tmp_path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan_payload()), encoding="utf-8")
    proof_path = tmp_path / "proof.jsonl"

    payload = SeestarpyAdapter(proof_path, "test").validate_file(plan_path)

    assert payload["plan_name"] == "SeeVar"
    assert ProofLedger(proof_path).read_all()[0].step == "validate_plan"
