# Ticket 001: Define standalone legal lifecycle standard

- **ID**: ticket-001
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-08-13

## Goal and scope

Define a reusable, modular legal-lifecycle standard for projects that sell or
operate products and services. The contract covers versioned legal packs,
licenses, jurisdiction-dependent availability, policy acceptance, withdrawal
and secret-free receipts. It is a machine-readable constraint language, not
legal advice.

The standard composes with `wellmanifest/product-lifecycle` and can be bound
from `wellmanifest/saas-lifecycle` through the existing `legalPolicyRef`
without absorbing billing, identity or deployment authority.

## Acceptance criteria

- [ ] AC-01: The repository has an immutable published governance adoption and
  a real local seed baseline created before implementation.
- [ ] AC-02: A closed Draft 2020-12 schema defines pack, request, obligation
  state and receipt variants.
- [ ] AC-03: Request-only GBNF excludes legal prose, personal data, payment
  credentials and execution commands.
- [ ] AC-04: Documentation defines the state machine, location/license
  boundaries, composition with product and SaaS lifecycles, and fail-closed
  behavior.
- [ ] AC-05: Positive and adversarial conformance passes locally and in
  networkless, read-only Docker.
- [ ] AC-06: Governance and diff hygiene pass against the exact baseline.

## Authorization

The request to review existing manifests and create this repository as a
governed DSL project creates `SESSION_EXECUTION_AUTHORIZATION` and the
narrow autonomous seed-baseline authorization. It allows exactly one local
governance-only baseline commit while `HEAD` is unborn and implementation is
absent. It does not authorize a remote, push, PR, merge, tag or release.

The same request separately authorizes later public repository creation,
committing the bounded implementation, pushing its ticket branch and opening
a pull request. It does not authorize a direct push to `main`, merge, tag,
release creation or legal advice.

## Baseline

To be written after the seed transaction.

## Participants

- Human participant: unresolved; no `user-*` file was created.
- Agent participant: [ai-grok.md](ai-grok.md)
