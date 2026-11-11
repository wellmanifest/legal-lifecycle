# Ticket 010: Modularize legal_io and harden CLI symlink traversal, JSON int bounds, schema depth, and applicableLaw

- **ID**: ticket-010
- **Owner**: tom
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-11

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: On 2026-11-11 user authorized auditing, fixing security and conformance bugs, modularizing, and optimizing across `wellmanifest/*` standard repositories.

Extract `standard/legal_io.py` so regular-file I/O, symlink-ancestor detection, and bounded strict JSON parsing live in a dedicated SSOT module (`legal_primitives.py` reduced well below 500 lines); fix the CLI `os.path.abspath` symlink-traversal bypass in `conformance.main` (`sym_dir/../real`) and relative (`../sym_dir`) symlink-parent traversal; bound JSON integer digit lengths before `int()` conversion; replace recursive `Contracts._closed` with an iterative depth-bounded stack; reject whitespace-only `applicableLaw`; expand `standard/test_legal_hardening.py`; and mark merged `project/ticket-009/README.md` `DONE`.

## Acceptance criteria

- [x] AC-01: Extract `standard/legal_io.py`, reject CLI and relative `sym_dir/..` symlink-traversal paths, bound JSON integer digits before `int()`, make `Contracts._closed` iterative with depth bounds, and reject whitespace-only `applicableLaw`, keeping all Python files strictly `< 500` lines.
- [x] AC-02: Expand `standard/test_legal_hardening.py`, mark merged `project/ticket-009/README.md` `DONE`, and pass `conformance.py --all`, `ruff check`, `pytest`, `governance-check.sh`, and `wellman check`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
