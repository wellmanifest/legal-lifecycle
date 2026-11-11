"""Adversarial hardening suite for legal-lifecycle file I/O, JSON bounds, and enum guards."""

from __future__ import annotations

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path

import conformance as legal
import legal_primitives as lp


class LegalLifecycleHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contracts = legal.Contracts()
        self.contracts.integrity()

    def test_read_regular_utf8_and_cli_reject_symlink_directory_and_fifo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            real = root / "request.json"
            real.write_text(json.dumps(legal.request_example()), encoding="utf-8")
            link = root / "link.json"
            link.symlink_to(real)

            with self.assertRaises(legal.ContractError):
                legal.read_regular_utf8(link)
            self.assertEqual(legal.main(["--file", str(link)]), 1)
            self.assertEqual(legal.main(["--file", str(root)]), 1)

            if hasattr(os, "mkfifo"):
                fifo = root / "pipe.json"
                os.mkfifo(fifo)
                with self.assertRaises(legal.ContractError):
                    legal.read_regular_utf8(fifo)
                self.assertEqual(legal.main(["--file", str(fifo)]), 1)

    def test_strict_loads_rejects_nan_infinity_overflow_and_deep_nesting(self) -> None:
        deep = ("[" * (lp.MAX_JSON_DEPTH + 2)) + "1" + ("]" * (lp.MAX_JSON_DEPTH + 2))
        extreme = ("[" * 1500) + "1" + ("]" * 1500)
        for raw in ("NaN", "Infinity", "-Infinity", "1e999", "-1e999", deep, extreme):
            with self.subTest(raw=raw[:20]):
                with self.assertRaises(legal.ContractError):
                    legal.strict_loads(raw)

    def test_unhashable_enums_and_non_string_keys_raise_contract_error(self) -> None:
        with self.assertRaises(legal.ContractError):
            legal.validate_document({"schema": ["unhashable"]})

        pack = copy.deepcopy(legal.pack_example())
        pack["jurisdictions"][0]["economicArea"] = ["eu"]
        with self.assertRaises(legal.ContractError):
            legal.validate_pack(self.contracts, pack)

        pack2 = copy.deepcopy(legal.pack_example())
        pack2["licenses"][0]["copyleft"] = {"bad": 1}
        with self.assertRaises(legal.ContractError):
            legal.validate_pack(self.contracts, pack2)

        req = copy.deepcopy(legal.request_example())
        req["operation"] = ["inspect"]
        with self.assertRaises(legal.ContractError):
            legal.validate_request(self.contracts, req)

        obl = copy.deepcopy(legal.obligation_example())
        obl["state"] = ["accepted"]
        with self.assertRaises(legal.ContractError):
            legal.validate_obligation(self.contracts, obl)

        rcpt = copy.deepcopy(legal.receipt_example())
        rcpt["outcome"] = {"bad": 1}
        with self.assertRaises(legal.ContractError):
            legal.validate_receipt(self.contracts, rcpt)

        bad_key_obj = copy.deepcopy(legal.request_example())
        bad_key_obj[99] = "invalid"  # type: ignore[index]
        with self.assertRaises(legal.ContractError):
            legal.validate_request(self.contracts, bad_key_obj)

        nested: object = "safe"
        for _ in range(lp.MAX_JSON_DEPTH + 4):
            nested = {"child": nested}
        with self.assertRaises(legal.ContractError):
            lp.reject_sensitive(nested)

    def test_int_overflow_surrogates_secret_keys_ancestor_symlinks_and_ref_bounds(self) -> None:
        for raw in (
            '{"x": ' + "9" * 500 + "}",
            '{"x": -' + "9" * 500 + "}",
            '{"x": ' + "9" * 5000 + "}",
            r'{"x": "\ud800"}',
            r'{"\udfff": 1}',
            '{"x": "\ud800"}',
            "{malformed",
        ):
            with self.subTest(raw=raw[:24]), self.assertRaises(legal.ContractError):
                legal.strict_loads(raw)

        for bad_val in ({"x": 10**400}, {"x": "\ud800"}, {"\ud800": 1}):
            with self.assertRaises(legal.ContractError):
                legal.canonical(bad_val)

        with self.assertRaises(legal.ContractError):
            legal.digest("\ud800")

        canary_key = "gh" + "p_" + ("X9y8Z7" * 5)
        for bad_sensitive in ({canary_key: "v"}, {"\ud800": "v"}, {"safe": "\udfff"}):
            with self.assertRaises(legal.ContractError):
                lp.reject_sensitive(bad_sensitive)

        for bad_ref in (
            ("identifier", "a" * 97),
            ("identifier", "pack-1\n"),
            ("packRef", "pack://./saas/v1"),
            ("packRef", "pack://../saas/v1"),
            ("packRef", "pack://example.test/../v1"),
            ("packRef", "pack://example.test/./v1"),
            ("packRef", "pack://example.test/a::b/v1"),
            ("packRef", "pack://example.test/a:..:b/v1"),
            ("accountRef", "account://example.test/" + "a" * 250),
        ):
            with self.subTest(ref=bad_ref[1][:32]), self.assertRaises(legal.ContractError):
                self.contracts.ref(bad_ref[0], bad_ref[1])

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            real_dir = base / "real" / "nested"
            real_dir.mkdir(parents=True)
            doc_path = real_dir / "req.json"
            doc_path.write_text(json.dumps(legal.request_example()), encoding="utf-8")

            for bad_max in (0, -1, True, False):
                with self.assertRaises(legal.ContractError):
                    legal.read_regular_utf8(doc_path, max_bytes=bad_max)  # type: ignore[arg-type]

            sym_dir = base / "sym_dir"
            sym_dir.symlink_to(base / "real")
            deep_sym = sym_dir / "nested" / "req.json"
            with self.assertRaises(legal.ContractError):
                legal.read_regular_utf8(deep_sym)
            with self.assertRaises(legal.ContractError):
                legal.file_digest(deep_sym)
            self.assertEqual(legal.main(["--file", str(deep_sym)]), 1)


if __name__ == "__main__":
    unittest.main()
