#!/usr/bin/env python3
"""Dependency-free conformance checks for legal lifecycle v1."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import legal_fixtures as _fx  # noqa: E402
from legal_primitives import (  # noqa: E402
    ALLOWED_GRANTS,
    APPLICABLE_LAW_RE,
    GRAMMAR_DIGEST,
    LIFECYCLE_PROFILE_DIGEST,
    LIFECYCLE_SOURCE_REVISION,
    LIFECYCLE_TRANSITIONS,
    LIFECYCLE_VALIDATOR_DIGESTS,
    SCHEMA_DIGEST,
    SCHEMA_URI,
    SEMVER_RE,
    ContractError,
    Contracts,
    bounded_int,
    bounded_list,
    canonical,
    digest,
    exact,
    file_digest,
    iso_date_value,
    reject_sensitive,
    strict_bool,
    strict_loads,
    time_value,
    unique_list,
    validate_lifecycle_profile,
)

pack_example, request_example = _fx.pack_example, _fx.request_example
obligation_example, receipt_example = _fx.obligation_example, _fx.receipt_example

__all__ = [
    "ContractError",
    "Contracts",
    "GRAMMAR_DIGEST",
    "LIFECYCLE_PROFILE_DIGEST",
    "LIFECYCLE_SOURCE_REVISION",
    "LIFECYCLE_TRANSITIONS",
    "LIFECYCLE_VALIDATOR_DIGESTS",
    "SCHEMA_DIGEST",
    "SCHEMA_URI",
    "canonical",
    "digest",
    "file_digest",
    "main",
    "obligation_example",
    "pack_example",
    "receipt_example",
    "request_example",
    "run_all",
    "strict_loads",
    "validate_document",
    "validate_jurisdiction",
    "validate_lifecycle_profile",
    "validate_obligation",
    "validate_pack",
    "validate_receipt",
    "validate_request",
]


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
    if not isinstance(value["applicableLaw"], str) or not APPLICABLE_LAW_RE.fullmatch(
        value["applicableLaw"]
    ):
        raise ContractError("invalid applicableLaw")
    if value["economicArea"] not in {"none", "eu", "eea", "uk", "other"}:
        raise ContractError("invalid economic area")
    if value["serviceAvailability"] not in {"offered", "restricted", "prohibited"}:
        raise ContractError("invalid service availability")
    if value["productAvailability"] not in {"offered", "restricted", "prohibited"}:
        raise ContractError("invalid product availability")
    withdrawal = bounded_int(value["consumerWithdrawalDays"], 0, 30, "invalid withdrawal days")
    explicit = strict_bool(value["requiresExplicitConsent"], "invalid explicit consent flag")
    if value["economicArea"] in {"eu", "eea"}:
        if withdrawal < 14:
            raise ContractError("eu withdrawal window too short")
        if explicit is not True:
            raise ContractError("eu consent must be explicit")
    bounded_int(value["ageOfConsent"], 13, 21, "invalid age of consent")
    if value["dataTransferAdequacy"] not in {
        "adequate",
        "scc-required",
        "prohibited",
        "not-applicable",
    }:
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
    if not isinstance(value["version"], str) or SEMVER_RE.fullmatch(value["version"]) is None:
        raise ContractError("invalid pack version")
    for product in unique_list(value["productRefs"], "invalid productRefs", minimum=1, maximum=32):
        c.ref("productRef", product)
    jurisdictions: set[str] = set()
    countries: set[str] = set()
    offered = False
    for item in bounded_list(
        value["jurisdictions"], "invalid jurisdictions", minimum=1, maximum=64
    ):
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
    if (
        default_item["productAvailability"] == "prohibited"
        or default_item["serviceAvailability"] == "prohibited"
    ):
        raise ContractError("default jurisdiction prohibited")
    if not offered:
        raise ContractError("pack offers no jurisdiction")
    licenses: set[str] = set()
    for item in bounded_list(value["licenses"], "invalid licenses", minimum=1, maximum=16):
        item = exact(
            item,
            {"ref", "grant", "copyleft", "attributionRequired", "sourceDisclosure", "warranty"},
            {"spdxId"},
        )
        ref = c.ref("licenseRef", item["ref"])
        if ref in licenses:
            raise ContractError("duplicate license")
        licenses.add(ref)
        if "spdxId" in item:
            c.ref("spdxId", item["spdxId"])
        grants = unique_list(item["grant"], "invalid license grant", minimum=1, maximum=8)
        if any(g not in ALLOWED_GRANTS for g in grants):
            raise ContractError("invalid license grant")
        strict_bool(item["attributionRequired"], "invalid attributionRequired")
        if item["copyleft"] not in {"none", "weak", "strong", "network"}:
            raise ContractError("invalid copyleft")
        if item["sourceDisclosure"] not in {"none", "on-distribution", "network"}:
            raise ContractError("invalid source disclosure")
        if item["warranty"] not in {"none", "limited", "as-declared"}:
            raise ContractError("invalid warranty")
        if item["copyleft"] in {"strong", "network"} and item["sourceDisclosure"] == "none":
            raise ContractError("copyleft without disclosure")
    policies: set[str] = set()
    for item in bounded_list(value["policies"], "invalid policies", minimum=1, maximum=16):
        item = exact(
            item,
            {"ref", "kind", "language", "effectiveAt", "requiresAcceptance", "withdrawalDays"},
        )
        ref = c.ref("policyRef", item["ref"])
        if ref in policies:
            raise ContractError("duplicate policy")
        policies.add(ref)
        c.ref("language", item["language"])
        if item["kind"] not in {
            "terms",
            "privacy",
            "refund",
            "withdrawal",
            "cookie",
            "acceptable-use",
            "dpa",
        }:
            raise ContractError("invalid policy kind")
        iso_date_value(item["effectiveAt"])
        strict_bool(item["requiresAcceptance"], "invalid requiresAcceptance")
        bounded_int(item["withdrawalDays"], 0, 30, "invalid policy withdrawal")


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
    if (
        value["$schema"] != SCHEMA_URI
        or value["schema"] != "wellmanifest.legal-lifecycle-request/v1"
    ):
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
    for name in (
        "accountRef",
        "productRef",
        "packRef",
        "jurisdictionRef",
        "intentRef",
        "grantRef",
    ):
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
    if value["operation"] == "check_availability" and (
        "policyRef" in value or "licenseRef" in value
    ):
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
    if (
        value["$schema"] != SCHEMA_URI
        or value["schema"] != "wellmanifest.legal-obligation-state/v1"
    ):
        raise ContractError("unsupported obligation")
    c.ref("accountRef", value["accountRef"])
    c.ref("productRef", value["productRef"])
    c.ref("packRef", value["packRef"])
    c.ref("jurisdictionRef", value["boundJurisdictionRef"])
    time_value(value["updatedAt"])
    if value["state"] not in {
        "unbound",
        "bound",
        "accepted",
        "restricted",
        "withdrawn",
        "expired",
        "denied",
    }:
        raise ContractError("invalid obligation state")
    bounded_int(value["version"], 1, 2_147_483_647, "invalid version")
    policies = unique_list(value["acceptedPolicies"], "invalid acceptedPolicies", maximum=16)
    licenses = unique_list(value["grantedLicenses"], "invalid grantedLicenses", maximum=16)
    if value["state"] == "accepted" and not policies:
        raise ContractError("accepted obligation lacks policy")
    for ref in policies:
        c.ref("policyRef", ref)
    for ref in licenses:
        c.ref("licenseRef", ref)
    if value["state"] == "unbound" and (policies or licenses):
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
    if (
        value["$schema"] != SCHEMA_URI
        or value["schema"] != "wellmanifest.legal-lifecycle-receipt/v1"
    ):
        raise ContractError("unsupported receipt")
    c.ref("identifier", value["requestId"])
    for name in ("accountRef", "productRef", "packRef", "jurisdictionRef"):
        c.ref(name, value[name])
    c.ref("sha256", value["inputHash"])
    c.ref("sha256", value["planHash"])
    if value["outcome"] not in {
        "denied",
        "accepted",
        "bound",
        "withdrawn",
        "unavailable",
        "failed",
    }:
        raise ContractError("invalid outcome")
    if time_value(value["completedAt"]) < time_value(value["startedAt"]):
        raise ContractError("receipt chronology")
    for ref in unique_list(value["evidenceRefs"], "invalid evidenceRefs", minimum=1, maximum=64):
        c.ref("evidenceRef", ref)
    if value["secretsRedacted"] is not True or value["personalDataStored"] is not False:
        raise ContractError("unsafe receipt")


def validate_document(value: Any) -> None:
    if not isinstance(value, dict):
        raise ContractError("expected object")
    c = Contracts()
    c.integrity()
    dispatch = {
        "wellmanifest.legal-pack/v1": validate_pack,
        "wellmanifest.legal-lifecycle-request/v1": validate_request,
        "wellmanifest.legal-obligation-state/v1": validate_obligation,
        "wellmanifest.legal-lifecycle-receipt/v1": validate_receipt,
    }
    validator = dispatch.get(value.get("schema"))
    if validator is None:
        raise ContractError("unsupported document schema")
    validator(c, value)


def run_all() -> dict[str, Any]:
    c = Contracts()
    c.integrity()
    validate_lifecycle_profile(c.schema)
    validate_pack(c, pack_example())
    validate_request(c, request_example())
    validate_obligation(c, obligation_example())
    validate_receipt(c, receipt_example())
    cases = _fx.build_adversarial_cases(
        validate_pack_fn=lambda d: validate_pack(c, d),
        validate_request_fn=lambda d: validate_request(c, d),
        validate_obligation_fn=lambda d: validate_obligation(c, d),
        validate_receipt_fn=lambda d: validate_receipt(c, d),
        strict_loads_fn=strict_loads,
    )
    rejected: list[str] = []
    for name, case in cases:
        try:
            case()
        except ContractError:
            rejected.append(name)
        else:
            raise AssertionError(f"adversarial case accepted: {name}")
    return {
        "schema": "wellmanifest.legal-lifecycle-conformance/v1",
        "ok": True,
        "schemaDigest": "sha256:" + SCHEMA_DIGEST,
        "grammarDigest": "sha256:" + GRAMMAR_DIGEST,
        "lifecycleSourceRevision": LIFECYCLE_SOURCE_REVISION,
        "positiveVariants": 4,
        "adversarialRejected": rejected,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--file", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.all:
            print(json.dumps(run_all(), indent=2, sort_keys=True))
        elif args.file:
            validate_document(strict_loads(args.file.read_text("utf-8")))
            print(f"PASS: {args.file}")
        else:
            parser.error("choose --all or --file")
    except (ContractError, json.JSONDecodeError, OSError) as error:
        print(f"FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
