---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-004
---
# Participant: codex (AI agent)

## Understanding

The clean adopter is pinned to new-project 0.16.0 and has no active ticket.
The published 0.20.32 package is the accepted source for this bounded upgrade.
The user explicitly requested continuation and repository-wide standardization;
that authority is recorded for this adopter only.

## Execution plan

1. Validate the exact base, old lock, immutable 0.20.32 source and adoption
   preflight.
2. Run Goal's provenance-bound upgrade in this canonical linked worktree.
3. Verify host source links, governance, legal conformance and clean diff.
4. Publish through the protected PR/validator process and preserve exact-head
   approval evidence; never merge directly.

## Actual changes

- Initialized the bounded ticket and recorded
  `SESSION_EXECUTION_AUTHORIZATION` from the request to continue the
  repository-wide rollout.
- Bound the adoption to `6800f0138bc9063eb2dacb0a8b797dedcafb7952` →
  `b6ba9c21a65a6a5648ecf904b64c3b75295e136f`.

## Blockers

- No blocker inside the recorded intent; proceed without a redundant chat
  confirmation.
- Trusted review and protected merge remain external controls, not granted by
  this file.
