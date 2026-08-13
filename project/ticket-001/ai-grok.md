---
participant-id: agent:grok
participant: grok
role: agent
ticket: ticket-001
---
# Participant: grok (AI agent)

## Understanding

Existing Wellmanifest lifecycle repos already isolate billing, deployment,
accounts, Git and tickets. SaaS offers carry an opaque `legalPolicyRef` but
deliberately refuse to define tax, license or jurisdiction rules. The missing
module is a closed DSL for legal packs: licenses, policies and
location-dependent availability that product and SaaS catalogs can bind.

## Execution plan

1. Adopt published `wellmanifest/new-project` and create one local seed
   baseline before any standard file exists.
2. Define closed pack, request, obligation and receipt variants.
3. Constrain requests with matching GBNF and reject personal data, legal
   prose dumps, credentials and execution commands.
4. Document composition with `product-lifecycle` and `saas-lifecycle`.
5. Validate locally, through the governance gate and in networkless Docker.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to create and publish this repository.
- Adopted published `wellmanifest/new-project` v0.16.0 at
  `6800f0138bc9063eb2dacb0a8b797dedcafb7952`.

## Blockers

- The initial-baseline blocker is resolved by the authorized local seed
  commit once HEAD exists.
- New authority remains required for destructive action, secret access,
  material objective expansion and trusted merge.

## Risks and controls

- A legal pack can be mistaken for legal advice; the contract is a
  constraint language and never an opinion or authorization.
- Location data can become personal data; only ISO country/subdivision codes
  are allowed.
- An offer can leak into a prohibited jurisdiction; availability is explicit
  and fail-closed.
- License and policy versions can drift; every binding is a versioned ref.
