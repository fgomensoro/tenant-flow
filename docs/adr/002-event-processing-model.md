# ADR 002 — Event Processing Model

- **Status:** Accepted
- **Date:** 2026-04-14
- **Deciders:** Francisco Gomensoro
- **Project:** tenant-flow
- **Tags:** data-modeling, events, idempotency, immutability, cqrs

---

## Context

tenant-flow ingests webhooks from external providers (Shopify, Stripe, and others) on behalf of multiple B2B tenants. Each incoming webhook represents a **fact about the past**: at a specific point in time, a specific provider sent specific data on behalf of a specific tenant. That fact does not change once it has happened.

What does change over time is the **state of how tenant-flow processes that fact**: it might be received and waiting, in the middle of being processed, successfully processed, or failed and pending retry. A single event may be processed multiple times due to transient failures, worker crashes, or explicit reprocessing.

I need to model the data layer in a way that:

1. Preserves the original webhook content **exactly as received**, so it can be audited, replayed, and used to verify HMAC signatures.
2. Tracks the full history of processing attempts for each event, so failures and retries are debuggable.
3. Allows fast queries for the most common operational read pattern (the worker polling for events that need processing).
4. Enforces idempotency at the database level, so duplicates from provider retries cannot create duplicate state.
5. Maintains tenant isolation throughout, consistent with the multi-tenancy strategy from ADR 001.

The naive approach — a single `events` table with a mutable `status` column — handles requirement 3 well but fails requirements 1, 2, and partially 4. A pure event-sourcing approach handles 1 and 2 well but makes requirement 3 expensive without additional caching layers.

---

## Decision

**I will use a hybrid model with two tables, plus a deliberate denormalization for read performance:**

### Table 1: `events` — append-only, immutable facts

Each row represents one webhook received from a provider for a specific tenant. Once inserted, the columns describing the event itself are never modified. This includes the raw HTTP body (for HMAC verification), the parsed JSON payload (for queries), the provider, the event type, the idempotency key supplied by the provider, a SHA-256 hash of the raw body, and the timestamp of reception.

Three additional columns on this table — `current_status`, `last_attempted_at`, and `attempt_count` — are **deliberate denormalizations** of the processing history. They exist purely for read performance (see below) and are derivable from `event_processing_attempts`. They are updated atomically with each new processing attempt, in the same transaction.

### Table 2: `event_processing_attempts` — append-only processing log

Each row represents one attempt by a worker to process a specific event. Every attempt produces a new row; rows are never updated or deleted. This table is the **source of truth for processing history**: status of the attempt, timestamp, error message if it failed, duration.

### Idempotency enforcement

Idempotency is enforced through defense in depth, mirroring the multi-tenancy strategy:

1. **Application-level early check (optimization).** Before processing a new webhook, the app does a quick `SELECT` by `(tenant_id, provider, idempotency_key)`. If the event already exists, the app returns 200 OK to the provider and skips processing. This is purely an optimization to avoid the cost of full processing for known duplicates — it provides no atomic guarantee.

2. **Database-level guarantee.** A `UNIQUE (tenant_id, provider, idempotency_key)` constraint on the `events` table is the atomic guarantee. Inserts use `INSERT ... ON CONFLICT DO NOTHING RETURNING id`, which is atomic and free of race conditions. If the returned id is `NULL`, the row already existed and processing is skipped.

3. **Body hash as tiebreaker.** A `body_hash` column stores a SHA-256 of the raw body. When a duplicate is detected by idempotency key, the application compares the new body's hash against the stored one. If they match, the duplicate is silently discarded (the 99% case — providers retrying). If they differ, this is logged at WARNING severity and surfaced as a metric, because it indicates the provider sent two different payloads under the same identifier — a situation that requires manual investigation rather than silent overwrite.

### Atomicity between events and attempts

When a worker processes an event, the insert into `event_processing_attempts` and the update to `events.current_status` (and `last_attempted_at`, `attempt_count`) happen **inside the same database transaction**. Either both succeed or both fail. This guarantees that the denormalized state on `events` is always consistent with the latest entry in the attempts log.

---

## Alternatives Considered

### Single `events` table with mutable `status` column

The simplest possible model: one table, with a `status` column that is updated in place as the event moves through processing.

**Rejected.** It conflates two distinct concepts — the event as a historical fact, and the state of processing that event — into a single mutable row. This loses processing history (if an event fails three times before succeeding, you cannot inspect the failure messages or timing). It makes the events table mutable, which complicates caching, increases lock contention, and breaks the conceptual model of events as immutable facts. It is acceptable for systems that do not need debugging or auditability, but tenant-flow explicitly does need both.

### Pure event sourcing with no denormalization

The events table is fully immutable, the processing attempts table is the only source of state, and `current_status` is computed on the fly via a query like `SELECT status FROM event_processing_attempts WHERE event_id = ? ORDER BY attempted_at DESC LIMIT 1`.

**Rejected for the read path.** The worker's polling query needs to fetch all events in `received` status for a given tenant, ordered by reception time, with high frequency. Computing `current_status` on the fly for every event in every poll would require a join or subquery on `event_processing_attempts` and would scale poorly. The cost of maintaining a denormalized status column (one extra UPDATE per attempt, in the same transaction) is far smaller than the cost of recomputing it on every read.

### Versioned events table (insert-on-conflict)

Each new arrival of a webhook with the same idempotency key inserts a new row, distinguished by a version column. The "current" version is marked by a flag.

**Rejected.** This solves a problem tenant-flow does not have: it assumes that legitimately different versions of the same event need to be preserved separately. In practice, the only reason a duplicate by idempotency key would have a different body is provider error, and the correct response to that is a loud warning and manual investigation — not silent versioning. The complexity cost of versioning (every read must filter to current version, every UNIQUE constraint must include version) is not justified by the use case.

### Update-in-place with `INSERT ... ON CONFLICT DO UPDATE`

When a duplicate is detected by idempotency key, the existing row is updated with the new payload.

**Rejected.** This breaks the immutability of events and creates downstream consistency problems: if processing of the original payload has already started or completed, the update silently changes the data the system was working with, leading to inconsistent state. Update-in-place is appropriate for "current state" entities (like `users.email`) but not for "log of facts" entities like `events`.

---

## Consequences

### Positive

- **Events are immutable in their essential content.** This makes them easy to reason about, easy to cache, safe to replay, and aligned with the conceptual model of webhooks as historical facts.
- **Full processing history is preserved.** Every retry, every failure, every success is recorded. Debugging a stuck event is possible without log spelunking.
- **Read performance is excellent for the worker's polling query.** The denormalized `current_status` column is indexed alongside `tenant_id` and `received_at`, making the most common operational query a fast index scan.
- **Idempotency is guaranteed at the database level**, not at the application level. The defense-in-depth approach means race conditions between concurrent workers cannot cause duplicates.
- **The `body_hash` column gives early warning of provider bugs**, surfacing cases where the same idempotency key carries different content. These cases would otherwise be invisible.
- **Tenant isolation is consistent across both tables.** RLS policies apply to both `events` and `event_processing_attempts`, with the same tenant context propagated through the application stack.
- **The model maps cleanly to a recognized industry pattern (CQRS lite)**, which is valuable both for clarity and for communication with future maintainers and reviewers.

### Negative / Accepted trade-offs

- **Two tables instead of one.** More schema, more migrations, more code paths in the worker. The added complexity is justified by the gains above, but it is real.
- **Denormalization requires discipline.** The `current_status`, `last_attempted_at`, and `attempt_count` columns on `events` must be updated in the same transaction as each new attempt. If application code ever bypasses this discipline, the denormalized state can drift from the log. This is mitigated by routing all attempt inserts through a single helper function in the application layer, but the risk exists.
- **Recovery from denormalization drift requires a script.** If the denormalized columns ever become inconsistent with the attempts log, they can be reconstructed from the log, but this requires a deliberate maintenance operation. The system should ideally include a periodic reconciliation job in production.
- **Storage cost is higher.** Storing both `raw_body` (BYTEA, exact bytes) and `payload` (JSONB, parsed) duplicates the event content. This is a deliberate trade-off: the raw body is required for HMAC verification and forensic auditing, the parsed JSONB is required for efficient queries. Storage is cheap; lost data and impossible queries are expensive.
- **Joins between `events` and `event_processing_attempts` are required for some queries** (e.g., "show me the full history of event X"). These are simple foreign-key joins and are not expected to be hot paths, but they are an additional consideration when designing API responses.

---

## When this decision should be revisited

The hybrid model is appropriate for the expected scale and use cases of tenant-flow today. Specific signals that would justify revisiting:

1. **`event_processing_attempts` grows to billions of rows.** If a single tenant accumulates an extreme volume of attempts, the table may benefit from partitioning (by tenant, by time, or both). The table is append-only, which makes partitioning straightforward, but it should not be added before there is concrete evidence that the unpartitioned table is becoming a bottleneck.

2. **Denormalization drift becomes a recurring problem.** If reconciliation between the attempts log and the denormalized columns on `events` is needed frequently in production, the synchronization mechanism should be revisited — perhaps moved to a database trigger rather than application-level discipline, or the denormalization eliminated entirely in favor of a materialized view that is refreshed on a schedule.

3. **A new read pattern emerges that requires querying inside the JSON payload at high frequency.** At that point, a GIN index on `payload` becomes justified. Today there is no such use case in Phase 1, so the index does not exist.

4. **Cross-tenant analytics or aggregation queries become a primary use case.** If reporting needs to aggregate events across tenants frequently, the RLS-enforced model may need to be supplemented with a separate analytics layer that bypasses tenant isolation under controlled conditions.

5. **A specific tenant's processing volume becomes high enough to dominate the shared tables**, in line with the noisy-neighbor signal from ADR 001. In that case, that tenant's events and attempts may need to be moved to dedicated infrastructure.

---

## References

- ADR 001 — Multi-tenancy Strategy
- [Martin Fowler — Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
- [Martin Fowler — CQRS](https://martinfowler.com/bliki/CQRS.html)
- [Stripe API — Idempotent Requests](https://stripe.com/docs/api/idempotent_requests)
- [Shopify Webhooks — Best Practices](https://shopify.dev/docs/apps/webhooks/best-practices)