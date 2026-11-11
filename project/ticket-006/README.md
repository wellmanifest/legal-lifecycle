# Ticket 006: Modularize legal-lifecycle under 500 lines and harden strict contract validation

- **ID**: ticket-006
- **Owner**: tom
- **Status**: DONE
- **Workflow state**: PUBLICATION
- **Created**: 2026-11-11

## Goal and scope

Sync the modularized `< 500`-line Lifecycle DSL validator
(`wellmanifest/lifecycle@12bdc4c899bd6119cc30fca51d00a62b8582fa79`:
`lifecycle.py`, `lifecycle_audit.py`, `lifecycle_catalog.py`), split
`standard/conformance.py` under 500 lines by extracting
`standard/legal_fixtures.py`, harden schema-complete validation across legal
packs, requests, obligations, and receipts, remove `(KeyError, TypeError)`
exception masking in `run_all()`, add `--file` validation and `pyproject.toml`,
and close merged `ticket-004` and `ticket-005`.

## Acceptance criteria

- [x] AC-01: Keep every Python module in `standard/` strictly under 500 lines
      and verify SHA-256 digests of all 3 pinned Lifecycle DSL validator modules.
- [x] AC-02: Enforce duplicate-key-rejecting `strict_loads`, `bool`-safe integer
      bounds, strict booleans (`requiresExplicitConsent`, `attributionRequired`,
      `requiresAcceptance`), semver `pack.version`, `applicableLaw` pattern,
      `grant` / `warranty` / `outcome` enums, `YYYY-MM-DD` policy dates, strict
      RFC3339 timestamps, unique bounded lists, inline secret scanning, and
      pure `ContractError` catching in `run_all()`.
- [x] AC-03: Add `pyproject.toml`, close `ticket-004` and `ticket-005`, and pass
      `ruff check standard`, `python3 standard/conformance.py --all`,
      `./project/governance-check.sh --base origin/main`, and `wellman check`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
