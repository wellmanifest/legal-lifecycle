# Ticket 004: Adopt wellmanifest/new-project v0.20.32 and host source links

- **ID**: ticket-004
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-15

## Goal and scope

Upgrade this adopter from `wellmanifest/new-project` 0.16.0 to the published
0.20.32 revision. The upgrade is performed only through the managed Goal
adoption transaction and installs the complete host-agnostic contract,
including the bounded-session anomaly checks and the source-links block in
`AGENTS.md` and every declared host projection.

The local adoption lock and managed-file digests remain authoritative. Remote
Wellmanifest URLs are navigation only. No domain files, legal lifecycle
semantics, human-owned input or unrelated workflow are changed.

## Acceptance criteria

- [x] AC-01: The user’s autonomous execution request is recorded as
  `SESSION_EXECUTION_AUTHORIZATION` and bounds this ticket to the declared
  adoption transaction.
- [ ] AC-02: The complete published 0.20.32 managed package is adopted from
  `b6ba9c21a65a6a5648ecf904b64c3b75295e136f`, with the lock and package map
  proving the exact source revision and managed digests.
- [ ] AC-03: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, Cursor, Aider and Copilot
  projections contain the standard source-links contract, including concrete
  local paths and remote Wellmanifest file links.
- [ ] AC-04: The governance gate, legal lifecycle conformance checks and
  `git diff --check` pass on the ticket HEAD; no domain or human-owned file is
  changed.
- [ ] AC-05: The exact ticket HEAD is published through the protected PR and
  trusted review process; no direct merge is performed by the agent.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-codex.md](ai-codex.md)

## Risks and boundaries

- Existing target-owned files are preserved unless the managed adoption
  transaction proves that the standard owns the exact path and digest.
- A dirty state, conflicting active ticket, invalid prerequisite or missing
  immutable source evidence blocks the transaction before writes.
- This ticket upgrades one repository only; fleet rollout remains serialized
  through separate adopter tickets.

SESSION_EXECUTION_AUTHORIZATION: the user requested continuation and
repository-wide standardization/testing. This ticket applies that authority to
this clean `legal-lifecycle` adopter only, within the declared intent and
protected publication boundary.
