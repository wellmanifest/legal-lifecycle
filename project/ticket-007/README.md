# Ticket 007: Add pytest conformance suite for legal-lifecycle v1

- **ID**: ticket-007
- **Owner**: tom
- **Status**: DONE
- **Workflow state**: PUBLICATION
- **Created**: 2026-11-11

## Goal and scope

Add a standalone `pytest` / `unittest` conformance suite under
`tests/test_legal_lifecycle.py` exercising `legal-lifecycle` v1 conformance
reports, strict JSON duplicate-key rejection, `bool`-for-`int` rejection,
unhashable grant list handling, ISO-8601 policy date validation, receipt outcome
validation, inline credential scanning, and `--file` CLI exit codes, and close
merged `ticket-006`.

## Acceptance criteria

- [x] AC-01: Add `tests/test_legal_lifecycle.py` exercising `legal-lifecycle` v1
      validators and `--file` CLI under both `pytest` and `unittest`.
- [x] AC-02: Reconcile merged `project/ticket-006/README.md` to `DONE` /
      `PUBLICATION` and pass `ruff check tests`, `pytest -q`,
      `./project/governance-check.sh --base origin/main`, and `wellman check`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
