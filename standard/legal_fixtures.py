#!/usr/bin/env python3
"""Reference positive and adversarial fixtures for Wellmanifest legal-lifecycle v1."""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

SCHEMA_URI = "https://wellmanifest.dev/schemas/legal-lifecycle/v1"


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


def build_adversarial_cases(
    *,
    validate_pack_fn: Callable[[dict[str, Any]], None],
    validate_request_fn: Callable[[dict[str, Any]], None],
    validate_obligation_fn: Callable[[dict[str, Any]], None],
    validate_receipt_fn: Callable[[dict[str, Any]], None],
    strict_loads_fn: Callable[[str], Any],
) -> list[tuple[str, Callable[[], Any]]]:
    pack = pack_example()
    request = request_example()
    obligation = obligation_example()
    receipt = receipt_example()
    canary = "gh" + "p_" + ("A1b2C3" * 5)
    cases: list[tuple[str, Callable[[], Any]]] = []

    def add_pack(name: str, mutate: Callable[[dict[str, Any]], None]) -> None:
        doc = copy.deepcopy(pack)
        mutate(doc)
        cases.append((name, lambda doc=doc: validate_pack_fn(doc)))

    def add_req(name: str, mutate: Callable[[dict[str, Any]], None]) -> None:
        doc = copy.deepcopy(request)
        mutate(doc)
        cases.append((name, lambda doc=doc: validate_request_fn(doc)))

    def add_obl(name: str, mutate: Callable[[dict[str, Any]], None]) -> None:
        doc = copy.deepcopy(obligation)
        mutate(doc)
        cases.append((name, lambda doc=doc: validate_obligation_fn(doc)))

    def add_rcpt(name: str, mutate: Callable[[dict[str, Any]], None]) -> None:
        doc = copy.deepcopy(receipt)
        mutate(doc)
        cases.append((name, lambda doc=doc: validate_receipt_fn(doc)))

    add_pack(
        "eu-withdrawal-too-short", lambda d: d["jurisdictions"][0].update(consumerWithdrawalDays=7)
    )
    add_pack(
        "eu-implied-consent", lambda d: d["jurisdictions"][0].update(requiresExplicitConsent=False)
    )
    add_pack(
        "missing-default-jurisdiction",
        lambda d: d.update(defaultJurisdictionRef="jurisdiction://example.test/missing/v1"),
    )
    add_pack(
        "pack-without-offered-jurisdiction",
        lambda d: (
            d["jurisdictions"][0].update(
                productAvailability="prohibited", serviceAvailability="prohibited"
            ),
            d["jurisdictions"][1].update(productAvailability="prohibited"),
        ),
    )
    add_pack("copyleft-without-disclosure", lambda d: d["licenses"][0].update(copyleft="strong"))
    add_pack("invalid-pack-semver", lambda d: d.update(version="v1"))
    add_pack(
        "bool-withdrawal-days", lambda d: d["jurisdictions"][1].update(consumerWithdrawalDays=True)
    )
    add_pack("non-bool-consent", lambda d: d["jurisdictions"][1].update(requiresExplicitConsent=1))
    add_pack("invalid-grant-enum", lambda d: d["licenses"][0].update(grant=["arbitrary"]))
    add_pack("unhashable-grant-item", lambda d: d["licenses"][0].update(grant=[{"bad": 1}]))
    add_pack("invalid-warranty-enum", lambda d: d["licenses"][0].update(warranty="forever"))
    add_pack("non-iso-policy-date", lambda d: d["policies"][0].update(effectiveAt="20260813"))

    add_req("personal-email", lambda d: d.update(email="user@example.test"))
    add_req("inline-legal-advice", lambda d: d.update(legalAdvice="you should sue"))
    add_req("accept-without-policy", lambda d: d.update(operation="accept_policy"))
    add_req(
        "availability-grants-license",
        lambda d: d.update(
            operation="check_availability", licenseRef="license://example.test/proprietary/v1"
        ),
    )
    add_req("inline-secret-material", lambda d: d.update(requestId=canary))

    add_obl("accepted-without-policy", lambda d: d.update(state="accepted", acceptedPolicies=[]))
    add_obl("unbound-with-grants", lambda d: d.update(state="unbound"))
    add_obl("bool-obligation-version", lambda d: d.update(version=True))
    add_obl("space-datetime-obligation", lambda d: d.update(updatedAt="2026-08-13 12:00:00Z"))
    add_obl(
        "duplicate-accepted-policies",
        lambda d: d.update(
            acceptedPolicies=[
                "policy://example.test/saas/terms/v1",
                "policy://example.test/saas/terms/v1",
            ]
        ),
    )

    add_rcpt("personal-data-receipt", lambda d: d.update(personalDataStored=True))
    add_rcpt("court-filing-receipt", lambda d: d.update(courtFiling="redacted"))
    add_rcpt("invalid-receipt-outcome", lambda d: d.update(outcome="unknown-outcome"))
    add_rcpt("non-list-evidence-refs", lambda d: d.update(evidenceRefs="not-a-list"))

    cases.append(("duplicate-json-keys", lambda: strict_loads_fn('{"schema":"a","schema":"b"}')))
    return cases
