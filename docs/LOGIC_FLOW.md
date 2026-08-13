# Legal Lifecycle logic flow

## Bind, accept and withdraw

```mermaid
stateDiagram-v2
    [*] --> Unbound
    Unbound --> Bound: bind_jurisdiction under offered or restricted rule
    Unbound --> Denied: jurisdiction prohibited
    Bound --> Accepted: accept_policy for a pack policy
    Bound --> Restricted: location becomes restricted
    Accepted --> Restricted: later pack version restricts location
    Accepted --> Withdrawn: withdraw before or after grant
    Restricted --> Withdrawn: withdraw
    Bound --> Expired: pack version superseded without rebind
    Accepted --> Expired: pack version superseded without re-accept
    Denied --> [*]
    Withdrawn --> [*]
    Expired --> Bound: bind newer pack version
```

`check_availability` never changes obligation state. It is a read of the
named pack and jurisdiction.

## Location and license checks

```mermaid
sequenceDiagram
    participant U as Account or catalog
    participant L as Legal pack
    participant P as Product lifecycle
    participant S as SaaS offer
    U->>L: inspect or check_availability
    L-->>U: offered, restricted or prohibited
    alt prohibited
        L-->>U: unavailable receipt
    else offered or restricted
        U->>L: bind_jurisdiction
        L-->>U: bound obligation
        U->>L: accept_policy
        L-->>U: accepted obligation
        P->>L: bind legalPackRef
        S->>L: bind legalPolicyRef
    end
```

A SaaS signup may start only after the selected plan's `legalPolicyRef`
resolves to a pack policy that is accepted for the bound jurisdiction.

## Failure routing

| Failure | Required state/outcome | Safe next action |
| --- | --- | --- |
| EU pack with fewer than 14 withdrawal days | `denied` | publish a new pack version |
| Default jurisdiction prohibited | `denied` | choose an offered default |
| `accept_policy` without `policyRef` | `denied` | include a pack policy ref |
| `check_availability` with a license grant | `denied` | inspect only |
| Personal email or address in a request | `denied` | use opaque account and location refs |
| Inline legal advice or court filing | `denied` | keep counsel artifacts in a governed store |
| `accepted` without policies | `failed` | require acceptance evidence |
| Receipt with personal data | `failed` | redact and re-issue |

No failure path stores personal data or turns a transport-level success into
an accepted obligation.
