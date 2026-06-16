#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filename: src/seevar_next/proof/ledger.py
Version: 0.1.0
Objective: JSONL proof ledger.
"""
from __future__ import annotations

import json
from pathlib import Path

from seevar_next.models import ProofStep


class ProofLedger:
    """Append-only JSONL proof ledger."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, step: ProofStep) -> None:
        """Append one proof step."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(step.model_dump_json() + "\n")

    def read_all(self) -> list[ProofStep]:
        """Read all proof steps."""
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(ProofStep.model_validate(json.loads(line)))
        return rows
