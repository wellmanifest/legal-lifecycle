"""Pytest/unittest conformance suite for legal-lifecycle v1."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STANDARD_DIR = ROOT / "standard"
if str(STANDARD_DIR) not in sys.path:
    sys.path.insert(0, str(STANDARD_DIR))

import conformance as legal  # noqa: E402


class LegalLifecycleConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contracts = legal.Contracts()
        self.contracts.integrity()

    def test_run_all_conformance_and_lifecycle_profile(self) -> None:
        report = legal.run_all()
        self.assertTrue(report["ok"])
        self.assertEqual(report["schema"], "wellmanifest.legal-lifecycle-conformance/v1")
        self.assertEqual(report["positiveVariants"], 4)
        self.assertGreaterEqual(len(report["adversarialRejected"]), 25)

    def test_strict_loads_rejects_duplicate_json_keys(self) -> None:
        with self.assertRaises(legal.ContractError):
            legal.strict_loads('{"schema":"a","schema":"b"}')

    def test_pack_schema_parity_semver_bool_grants_and_iso_date(self) -> None:
        pack = copy.deepcopy(legal.pack_example())
        pack["version"] = "not-semver"
        with self.assertRaises(legal.ContractError):
            legal.validate_pack(self.contracts, pack)

        pack = copy.deepcopy(legal.pack_example())
        pack["jurisdictions"][0]["consumerWithdrawalDays"] = True
        with self.assertRaises(legal.ContractError):
            legal.validate_pack(self.contracts, pack)

        pack = copy.deepcopy(legal.pack_example())
        pack["licenses"][0]["grant"] = [{"unhashable": 1}]
        with self.assertRaises(legal.ContractError):
            legal.validate_pack(self.contracts, pack)

        pack = copy.deepcopy(legal.pack_example())
        pack["policies"][0]["effectiveAt"] = "20260801"
        with self.assertRaises(legal.ContractError):
            legal.validate_pack(self.contracts, pack)

    def test_obligation_receipt_and_secret_scanning(self) -> None:
        obligation = copy.deepcopy(legal.obligation_example())
        obligation["version"] = False
        with self.assertRaises(legal.ContractError):
            legal.validate_obligation(self.contracts, obligation)

        receipt = copy.deepcopy(legal.receipt_example())
        receipt["outcome"] = "unknown"
        with self.assertRaises(legal.ContractError):
            legal.validate_receipt(self.contracts, receipt)

        req = copy.deepcopy(legal.request_example())
        req["intentRef"] = "gh" + "p_" + ("A" * 26)
        with self.assertRaises(legal.ContractError):
            legal.validate_request(self.contracts, req)

    def test_cli_file_validation_and_duplicate_key_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            valid_path = Path(tmp) / "request.json"
            valid_path.write_text(json.dumps(legal.request_example()), encoding="utf-8")
            self.assertEqual(legal.main(["--file", str(valid_path)]), 0)

            dup_path = Path(tmp) / "dup.json"
            dup_path.write_text('{"schema":"x","schema":"y"}', encoding="utf-8")
            self.assertEqual(legal.main(["--file", str(dup_path)]), 1)


if __name__ == "__main__":
    unittest.main()
