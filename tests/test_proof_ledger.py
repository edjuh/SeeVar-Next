from seevar_next.models import ProofStep, StepStatus
from seevar_next.proof.ledger import ProofLedger


def test_proof_ledger_roundtrip(tmp_path):
    ledger = ProofLedger(tmp_path / "proof.jsonl")
    row = ProofStep(
        run_id="run-1",
        target="ST Boo",
        phase="postflight",
        step="stack",
        status=StepStatus.PASS,
        evidence_path="stack.fits",
    )

    ledger.append(row)

    rows = ledger.read_all()
    assert len(rows) == 1
    assert rows[0].target == "ST Boo"
    assert rows[0].status == StepStatus.PASS
