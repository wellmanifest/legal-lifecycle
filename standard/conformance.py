#!/usr/bin/env python3
"""Dependency-free conformance checks for legal lifecycle v1."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "legal-lifecycle.schema.json"
GRAMMAR_PATH = ROOT / "legal-lifecycle.v1.gbnf"
SCHEMA_DIGEST = "e735dd3919139f48aac85a6dfa08e8182627b0be8e315804a6c1408bbc08644e"
GRAMMAR_DIGEST = "8b82c57b02e5754588a97f44699661dad3287ddd8b41df22dfa42122858e27ab"
SCHEMA_URI = "https://wellmanifest.dev/schemas/legal-lifecycle/v1"
SENSITIVE = re.compile(
    r"(?:password|passwd|token|secret|cookie|api[-_]?key|card|cvv|private[-_]?key|"
    r"email|address|phone|ssn|passport|legal[-_]?advice|court[-_]?filing|attorney)",
    re.I,
)
SAFE_ASSERTIONS = {"secretsRedacted", "personalDataStored"}


class ContractError(ValueError):
    """A bounded error that never repeats untrusted legal or personal data."""


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def exact(value: Any, required: set[str], optional: set[str] | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("expected object")
    optional = optional or set()
    if set(value) - required - optional:
        raise ContractError("undeclared field")
    if required - set(value):
        raise ContractError("missing field")
    return value


def time_value(value: Any) -> datetime:
    if not isinstance(value, str) or len(value) > 40:
        raise ContractError("invalid date-time")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ContractError("invalid date-time") from error
    if result.tzinfo is None:
        raise ContractError("timezone required")
    return result


def reject_sensitive(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if SENSITIVE.search(key) and key not in SAFE_ASSERTIONS:
                raise ContractError("sensitive data channel")
            reject_sensitive(child)
    elif isinstance(value, list):
        for child in value:
            reject_sensitive(child)


class Contracts:
    def __init__(self) -> None:
        self.schema = json.loads(SCHEMA_PATH.read_text("utf-8"))
        self.grammar = GRAMMAR_PATH.read_text("utf-8")
        defs = self.schema.get("$defs", {})
        names = (
            "identifier",
            "sha256",
            "accountRef",
            "productRef",
            "packRef",
            "policyRef",
            "licenseRef",
            "jurisdictionRef",
            "intentRef",
            "grantRef",
            "evidenceRef",
            "country",
            "language",
            "spdxId",
        )
        self.patterns = {name: re.compile(defs[name]["pattern"]) for name in names}

    def ref(self, name: str, value: Any) -> str:
        if not isinstance(value, str) or self.patterns[name].fullmatch(value) is None:
            raise ContractError(f"invalid {name}")
        return value

    def integrity(self) -> None:
        if self.schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema" or self.schema.get("$id") != SCHEMA_URI:
            raise ContractError("schema identity mismatch")
        if digest(canonical(self.schema)) != SCHEMA_DIGEST or digest(self.grammar) != GRAMMAR_DIGEST:
            raise ContractError("contract digest mismatch")
        if {x.get("$ref") for x in self.schema.get("oneOf", [])} != {
            "#/$defs/pack",
            "#/$defs/request",
            "#/$defs/obligation",
            "#/$defs/receipt",
        }:
            raise ContractError("document variants incomplete")
        for fragment in ("root ::= request", "legal prose", "jurisdiction-ref ::=", "pack-ref ::=", "sha256 ::="):
            if fragment not in self.grammar:
                raise ContractError("grammar incomplete")
        self._closed(self.schema)

    def _closed(self, value: Any) -> None:
        if isinstance(value, dict):
            if value.get("type") == "object" and value.get("additionalProperties") is not False:
                raise ContractError("open object schema")
            for child in value.values():
                self._closed(child)
        elif isinstance(value, list):
            for child in value:
                self._closed(child)


def pack_example() -> dict[str, Any]:
    eu = "jurisdiction://example.test/eu-pl/v1"
    return {
        "$schema": SCHEMA_URI,
        "schema": "wellmanifest.legal-pack/v1",
        "packId": "pack-saas-2026",
        "version": "1.0.0",
        "productRefs": ["product://example.test/subactor/v1"],
        "jurisdictions": [
            {
                "ref": eu,
                "country": "PL",
                "subdivision": "PL-14",
                "economicArea": "eu",
                "applicableLaw": "Poland / EU consumer law",
                "serviceAvailability": "offered",
                "productAvailability": "offered",
                "consumerWithdrawalDays": 14,
                "requiresExplicitConsent": True,
                "ageOfConsent": 16,
                "dataTransferAdequacy": "adequate",
            },
            {
                "ref": "jurisdiction://example.test/us-ca/v1",
                "country": "US",
                "subdivision": "US-CA",
                "economicArea": "none",
                "applicableLaw": "California",
                "serviceAvailability": "restricted",
                "productAvailability": "restricted",
                "consumerWithdrawalDays": 0,
                "requiresExplicitConsent": True,
                "ageOfConsent": 13,
                "dataTransferAdequacy": "scc-required",
            },
        ],
        "licenses": [
            {
                "ref": "license://example.test/proprietary/v1",
                "grant": ["use", "private"],
                "copyleft": "none",
                "attributionRequired": False,
                "sourceDisclosure": "none",
                "warranty": "none",
            }
        ],
        "policies": [
            {
                "ref": "policy://example.test/saas/terms/v1",
                "kind": "terms",
                "language": "en",
                "effectiveAt": "2026-08-13",
                "requiresAcceptance": True,
                "withdrawalDays": 14,
            }
        ],
        "defaultJurisdictionRef": eu,
    }


def request_example() -> dict[str, Any]:
    return {
        "$schema": SCHEMA_URI,
        "schema": "wellmanifest.legal-lifecycle-request/v1",
        "requestId": "request-001",
        "operation": "bind_jurisdiction",
        "accountRef": "account://example.test/account-001",
        "productRef": "product://example.test/subactor/v1",
        "packRef": "pack://example.test/saas/legal/v1",
        "jurisdictionRef": "jurisdiction://example.test/eu-pl/v1",
        "intentRef": "intent://example.test/legal/request-001",
        "grantRef": "grant://example.test/legal/request-001/g1",
        "planHash": "a" * 64,
    }


def obligation_example() -> dict[str, Any]:
    return {
        "$schema": SCHEMA_URI,
        "schema": "wellmanifest.legal-obligation-state/v1",
        "accountRef": "account://example.test/account-001",
        "productRef": "product://example.test/subactor/v1",
        "packRef": "pack://example.test/saas/legal/v1",
        "boundJurisdictionRef": "jurisdiction://example.test/eu-pl/v1",
        "state": "accepted",
        "version": 3,
        "updatedAt": "2026-08-13T12:00:00Z",
        "acceptedPolicies": ["policy://example.test/saas/terms/v1"],
        "grantedLicenses": ["license://example.test/proprietary/v1"],
    }


def receipt_example() -> dict[str, Any]:
    return {
        "$schema": SCHEMA_URI,
        "schema": "wellmanifest.legal-lifecycle-receipt/v1",
        "requestId": "request-001",
        "accountRef": "account://example.test/account-001",
        "productRef": "product://example.test/subactor/v1",
        "packRef": "pack://example.test/saas/legal/v1",
        "jurisdictionRef": "jurisdiction://example.test/eu-pl/v1",
        "inputHash": "c" * 64,
        "planHash": "a" * 64,
        "outcome": "bound",
        "startedAt": "2026-08-13T11:50:00Z",
        "completedAt": "2026-08-13T12:00:00Z",
        "evidenceRefs": ["evidence://example.test/legal/bind-001/r1"],
        "secretsRedacted": True,
        "personalDataStored": False,
    }


def validate_jurisdiction(c: Contracts, value: Any) -> str:
    value = exact(
        value,
        {
            "ref",
            "country",
            "economicArea",
            "applicableLaw",
            "serviceAvailability",
            "productAvailability",
            "consumerWithdrawalDays",
            "requiresExplicitConsent",
            "ageOfConsent",
            "dataTransferAdequacy",
        },
        {"subdivision"},
    )
    ref = c.ref("jurisdictionRef", value["ref"])
    c.ref("country", value["country"])
    if "subdivision" in value and (
        not isinstance(value["subdivision"], str)
        or not re.fullmatch(r"^[A-Z]{2}-[A-Z0-9]{1,3}$", value["subdivision"])
        or not value["subdivision"].startswith(value["country"] + "-")
    ):
        raise ContractError("invalid subdivision")
    if value["economicArea"] not in {"none", "eu", "eea", "uk", "other"}:
        raise ContractError("invalid economic area")
    if value["serviceAvailability"] not in {"offered", "restricted", "prohibited"}:
        raise ContractError("invalid service availability")
    if value["productAvailability"] not in {"offered", "restricted", "prohibited"}:
        raise ContractError("invalid product availability")
    if not isinstance(value["consumerWithdrawalDays"], int) or not 0 <= value["consumerWithdrawalDays"] <= 30:
        raise ContractError("invalid withdrawal days")
    if value["economicArea"] in {"eu", "eea"}:
        if value["consumerWithdrawalDays"] < 14:
            raise ContractError("eu withdrawal window too short")
        if value["requiresExplicitConsent"] is not True:
            raise ContractError("eu consent must be explicit")
    if not isinstance(value["ageOfConsent"], int) or not 13 <= value["ageOfConsent"] <= 21:
        raise ContractError("invalid age of consent")
    if value["dataTransferAdequacy"] not in {"adequate", "scc-required", "prohibited", "not-applicable"}:
        raise ContractError("invalid transfer adequacy")
    return ref


def validate_pack(c: Contracts, value: Any) -> None:
    reject_sensitive(value)
    value = exact(
        value,
        {
            "$schema",
            "schema",
            "packId",
            "version",
            "productRefs",
            "jurisdictions",
            "licenses",
            "policies",
            "defaultJurisdictionRef",
        },
    )
    if value["$schema"] != SCHEMA_URI or value["schema"] != "wellmanifest.legal-pack/v1":
        raise ContractError("unsupported pack")
    c.ref("identifier", value["packId"])
    if not value["productRefs"]:
        raise ContractError("pack without products")
    for product in value["productRefs"]:
        c.ref("productRef", product)
    jurisdictions: set[str] = set()
    countries: set[str] = set()
    offered = False
    for item in value["jurisdictions"]:
        ref = validate_jurisdiction(c, item)
        if ref in jurisdictions:
            raise ContractError("duplicate jurisdiction")
        jurisdictions.add(ref)
        country = item["country"]
        if country in countries:
            raise ContractError("duplicate country")
        countries.add(country)
        if item["productAvailability"] == "offered":
            offered = True
    default = c.ref("jurisdictionRef", value["defaultJurisdictionRef"])
    if default not in jurisdictions:
        raise ContractError("default jurisdiction missing")
    default_item = next(item for item in value["jurisdictions"] if item["ref"] == default)
    if default_item["productAvailability"] == "prohibited" or default_item["serviceAvailability"] == "prohibited":
        raise ContractError("default jurisdiction prohibited")
    if not offered:
        raise ContractError("pack offers no jurisdiction")
    licenses: set[str] = set()
    for item in value["licenses"]:
        item = exact(item, {"ref", "grant", "copyleft", "attributionRequired", "sourceDisclosure", "warranty"}, {"spdxId"})
        ref = c.ref("licenseRef", item["ref"])
        if ref in licenses:
            raise ContractError("duplicate license")
        licenses.add(ref)
        if "spdxId" in item:
            c.ref("spdxId", item["spdxId"])
        grants = item["grant"]
        if not isinstance(grants, list) or not grants or len(grants) != len(set(grants)):
            raise ContractError("invalid license grant")
        if item["copyleft"] not in {"none", "weak", "strong", "network"}:
            raise ContractError("invalid copyleft")
        if item["sourceDisclosure"] not in {"none", "on-distribution", "network"}:
            raise ContractError("invalid source disclosure")
        if item["copyleft"] in {"strong", "network"} and item["sourceDisclosure"] == "none":
            raise ContractError("copyleft without disclosure")
    policies: set[str] = set()
    for item in value["policies"]:
        item = exact(item, {"ref", "kind", "language", "effectiveAt", "requiresAcceptance", "withdrawalDays"})
        ref = c.ref("policyRef", item["ref"])
        if ref in policies:
            raise ContractError("duplicate policy")
        policies.add(ref)
        c.ref("language", item["language"])
        if item["kind"] not in {"terms", "privacy", "refund", "withdrawal", "cookie", "acceptable-use", "dpa"}:
            raise ContractError("invalid policy kind")
        try:
            date.fromisoformat(item["effectiveAt"])
        except (TypeError, ValueError) as error:
            raise ContractError("invalid policy date") from error
        if not isinstance(item["withdrawalDays"], int) or not 0 <= item["withdrawalDays"] <= 30:
            raise ContractError("invalid policy withdrawal")


def validate_request(c: Contracts, value: Any) -> None:
    reject_sensitive(value)
    value = exact(
        value,
        {
            "$schema",
            "schema",
            "requestId",
            "operation",
            "accountRef",
            "productRef",
            "packRef",
            "jurisdictionRef",
            "intentRef",
            "grantRef",
            "planHash",
        },
        {"policyRef", "licenseRef"},
    )
    if value["$schema"] != SCHEMA_URI or value["schema"] != "wellmanifest.legal-lifecycle-request/v1":
        raise ContractError("unsupported request")
    c.ref("identifier", value["requestId"])
    if value["operation"] not in {
        "inspect",
        "bind_jurisdiction",
        "accept_policy",
        "grant_license",
        "withdraw",
        "check_availability",
    }:
        raise ContractError("unsupported operation")
    for name in ("accountRef", "productRef", "packRef", "jurisdictionRef", "intentRef", "grantRef"):
        c.ref(name, value[name])
    c.ref("sha256", value["planHash"])
    if value["operation"] == "accept_policy":
        if "policyRef" not in value:
            raise ContractError("accept_policy lacks policy")
        c.ref("policyRef", value["policyRef"])
    if value["operation"] == "grant_license":
        if "licenseRef" not in value:
            raise ContractError("grant_license lacks license")
        c.ref("licenseRef", value["licenseRef"])
    if value["operation"] == "check_availability" and ("policyRef" in value or "licenseRef" in value):
        raise ContractError("availability check cannot grant")


def validate_obligation(c: Contracts, value: Any) -> None:
    reject_sensitive(value)
    value = exact(
        value,
        {
            "$schema",
            "schema",
            "accountRef",
            "productRef",
            "packRef",
            "boundJurisdictionRef",
            "state",
            "version",
            "updatedAt",
            "acceptedPolicies",
            "grantedLicenses",
        },
    )
    if value["$schema"] != SCHEMA_URI or value["schema"] != "wellmanifest.legal-obligation-state/v1":
        raise ContractError("unsupported obligation")
    for name in ("accountRef", "productRef", "packRef", "jurisdictionRef"):
        c.ref(name if name != "jurisdictionRef" else "jurisdictionRef", value[name if name != "jurisdictionRef" else "boundJurisdictionRef"])
    time_value(value["updatedAt"])
    if value["state"] not in {"unbound", "bound", "accepted", "restricted", "withdrawn", "expired", "denied"}:
        raise ContractError("invalid obligation state")
    if not isinstance(value["version"], int) or value["version"] < 1:
        raise ContractError("invalid version")
    if value["state"] == "accepted" and not value["acceptedPolicies"]:
        raise ContractError("accepted obligation lacks policy")
    for ref in value["acceptedPolicies"]:
        c.ref("policyRef", ref)
    for ref in value["grantedLicenses"]:
        c.ref("licenseRef", ref)
    if value["state"] == "unbound" and (value["acceptedPolicies"] or value["grantedLicenses"]):
        raise ContractError("unbound obligation has grants")


def validate_receipt(c: Contracts, value: Any) -> None:
    reject_sensitive(value)
    value = exact(
        value,
        {
            "$schema",
            "schema",
            "requestId",
            "accountRef",
            "productRef",
            "packRef",
            "jurisdictionRef",
            "inputHash",
            "planHash",
            "outcome",
            "startedAt",
            "completedAt",
            "evidenceRefs",
            "secretsRedacted",
            "personalDataStored",
        },
    )
    if value["$schema"] != SCHEMA_URI or value["schema"] != "wellmanifest.legal-lifecycle-receipt/v1":
        raise ContractError("unsupported receipt")
    c.ref("identifier", value["requestId"])
    for name in ("accountRef", "productRef", "packRef", "jurisdictionRef"):
        c.ref(name, value[name])
    c.ref("sha256", value["inputHash"])
    c.ref("sha256", value["planHash"])
    if time_value(value["completedAt"]) < time_value(value["startedAt"]):
        raise ContractError("receipt chronology")
    if not value["evidenceRefs"]:
        raise ContractError("receipt lacks evidence")
    for ref in value["evidenceRefs"]:
        c.ref("evidenceRef", ref)
    if value["secretsRedacted"] is not True or value["personalDataStored"] is not False:
        raise ContractError("unsafe receipt")


def run_all() -> dict[str, Any]:
    c = Contracts()
    c.integrity()
    pack, request, obligation, receipt = pack_example(), request_example(), obligation_example(), receipt_example()
    validate_pack(c, pack)
    validate_request(c, request)
    validate_obligation(c, obligation)
    validate_receipt(c, receipt)
    cases = []
    bad = copy.deepcopy(pack)
    bad["jurisdictions"][0]["consumerWithdrawalDays"] = 7
    cases.append(("eu-withdrawal-too-short", lambda: validate_pack(c, bad)))
    bad = copy.deepcopy(pack)
    bad["jurisdictions"][0]["requiresExplicitConsent"] = False
    cases.append(("eu-implied-consent", lambda: validate_pack(c, bad)))
    bad = copy.deepcopy(pack)
    bad["defaultJurisdictionRef"] = "jurisdiction://example.test/missing/v1"
    cases.append(("missing-default-jurisdiction", lambda: validate_pack(c, bad)))
    bad = copy.deepcopy(pack)
    bad["jurisdictions"][0]["productAvailability"] = "prohibited"
    bad["jurisdictions"][0]["serviceAvailability"] = "prohibited"
    bad["jurisdictions"][1]["productAvailability"] = "prohibited"
    cases.append(("pack-without-offered-jurisdiction", lambda: validate_pack(c, bad)))
    bad = copy.deepcopy(pack)
    bad["licenses"][0]["copyleft"] = "strong"
    cases.append(("copyleft-without-disclosure", lambda: validate_pack(c, bad)))
    bad = copy.deepcopy(request)
    bad["email"] = "user@example.test"
    cases.append(("personal-email", lambda: validate_request(c, bad)))
    bad = copy.deepcopy(request)
    bad["legalAdvice"] = "you should sue"
    cases.append(("inline-legal-advice", lambda: validate_request(c, bad)))
    bad = copy.deepcopy(request)
    bad["operation"] = "accept_policy"
    cases.append(("accept-without-policy", lambda: validate_request(c, bad)))
    bad = copy.deepcopy(request)
    bad["operation"] = "check_availability"
    bad["licenseRef"] = "license://example.test/proprietary/v1"
    cases.append(("availability-grants-license", lambda: validate_request(c, bad)))
    bad = copy.deepcopy(obligation)
    bad["state"] = "accepted"
    bad["acceptedPolicies"] = []
    cases.append(("accepted-without-policy", lambda: validate_obligation(c, bad)))
    bad = copy.deepcopy(obligation)
    bad["state"] = "unbound"
    cases.append(("unbound-with-grants", lambda: validate_obligation(c, bad)))
    bad = copy.deepcopy(receipt)
    bad["personalDataStored"] = True
    cases.append(("personal-data-receipt", lambda: validate_receipt(c, bad)))
    bad = copy.deepcopy(receipt)
    bad["courtFiling"] = "redacted"
    cases.append(("court-filing-receipt", lambda: validate_receipt(c, bad)))
    rejected = []
    for name, case in cases:
        try:
            case()
        except (ContractError, KeyError, TypeError):
            rejected.append(name)
        else:
            raise AssertionError(f"adversarial case accepted: {name}")
    return {
        "schema": "wellmanifest.legal-lifecycle-conformance/v1",
        "ok": True,
        "schemaDigest": "sha256:" + SCHEMA_DIGEST,
        "grammarDigest": "sha256:" + GRAMMAR_DIGEST,
        "positiveVariants": 4,
        "adversarialRejected": rejected,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if not args.all:
        parser.error("--all is required")
    print(json.dumps(run_all(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
