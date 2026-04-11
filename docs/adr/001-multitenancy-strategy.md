# ADR 001 — Multi-tenancy Strategy

- **Status:** Accepted
- **Date:** 2026-04-09
- **Deciders:** Francisco Gomensoro
- **Project:** tenant-flow
- **Tags:** multi-tenancy, postgres, security, architecture

---

## Context

tenant-flow is a multi-tenant SaaS platform that ingests, processes and serves data from external sources (Shopify, Stripe, and others) on behalf of multiple B2B customers. Every piece of data in the system belongs to exactly one tenant, and tenants must never be able to see each other's data — directly or indirectly.

Three canonical models exist for multi-tenant data isolation in PostgreSQL:

1. **Shared schema with Row-Level Security (RLS)** — one set of tables, every row carries a `tenant_id`, and Postgres enforces isolation via RLS policies.
2. **Schema-per-tenant** — one PostgreSQL schema per tenant, with the same table structure replicated in each.
3. **Database-per-tenant** — one entire database per tenant.

I need to choose one as the default model for the platform, knowing that the choice will shape how I write every query, every migration, every test, and every operational procedure for the lifetime of the project.

---

## Decision

**I will use shared schema with Row-Level Security as the default multi-tenancy model.**

Tenant context will be propagated from the HTTP request down to PostgreSQL via a `SET LOCAL app.current_tenant` statement executed at the beginning of every transaction. RLS policies on every tenant-scoped table will filter rows based on `current_setting('app.current_tenant')`.

Tenant context enforcement will follow a **defense-in-depth** approach with four independent layers:

1. **FastAPI middleware** — extracts the tenant identifier from the authenticated request (JWT or API key) and stores it in `request.state.tenant_id`. Runs on every request, no exceptions. If no valid tenant can be resolved, the request is rejected with 401.
2. **FastAPI `Depends` (`get_tenant_session`)** — provides handlers with a SQLAlchemy `AsyncSession` that already has `SET LOCAL app.current_tenant` executed. Handlers never set the context manually.
3. **SQLAlchemy event listener** — intercepts every connection checked out from the pool and verifies that the tenant context is set. If it isn't, raises an explicit exception with a stack trace. This catches sessions created outside the normal request flow (background jobs, scripts, future code).
4. **PostgreSQL `FORCE ROW LEVEL SECURITY`** — final safety net. If everything above fails, the database itself refuses to return rows from other tenants.

Layers 1–3 must **fail loudly** when the tenant context is missing — raising explicit exceptions, logging at ERROR severity, and triggering alerts in production. Layer 4 is intended as a backstop, not as a primary control: if it ever activates in production, it must be treated as a high-severity incident, because it means the application layers failed.

---

## Alternatives Considered

### Schema-per-tenant

**Rejected for the default case.** The maintenance cost grows linearly with the number of tenants: every schema change must be applied N times, partial failures leave the database in inconsistent states, and cross-tenant analytical queries require UNIONs across N schemas. Postgres's system catalog also degrades in performance as the total number of tables grows into the thousands, which is a hard ceiling on this approach.

The intuition that schema-per-tenant is "more secure" than RLS is misleading. Both models depend on the application correctly setting tenant context (`SET search_path` in one case, `SET LOCAL app.current_tenant` in the other). A bug in either is equally catastrophic. RLS actually has a stronger guarantee in practice, because the policy is enforced inside the query planner regardless of how the query is written, while `search_path` only affects unqualified table references.

Schema-per-tenant remains a viable option for *specific* tenants whose requirements justify it (see "When this decision should be revisited" below), but it is not the right default.

### Database-per-tenant

**Rejected.** Operationally untenable for a platform that expects to scale beyond a handful of customers. Each database is an independent unit for backups, migrations, monitoring, connection pooling, and version upgrades. The operational overhead does not pay for itself unless individual tenants justify it contractually or financially (six-figure ACV or hard regulatory isolation requirements). At the current scale and target market, this would consume engineering time without delivering proportional value.

---

## Consequences

### Positive

- **Lowest operational cost** of the three models. One database, one set of migrations, one backup pipeline.
- **Simple cross-tenant analytics.** Aggregate queries across the whole platform are trivial and fast.
- **Strong isolation guarantee** when defense-in-depth is correctly implemented, enforced by Postgres at the query planner level.
- **Easy to onboard new tenants** — no schema provisioning, no migration pipeline per tenant, just an `INSERT` into the `tenants` table.

### Negative / Accepted trade-offs

- **The tenant context mechanism is critical infrastructure.** A bug in the middleware, the dependency, or the event listener can produce silent data leakage if defenses fail simultaneously. This is mitigated but not eliminated by the four-layer approach.
- **Connection pooling requires care.** PgBouncer in transaction or statement mode is compatible with `SET LOCAL` but not with session-level `SET`. This must be verified in every deployment configuration and documented as a known footgun.
- **Indexing strategy must account for the tenant predicate.** Single-column indexes on `(created_at)` will be ignored by the planner in favor of `(tenant_id, created_at)` composite indexes. All indexes on tenant-scoped tables must lead with `tenant_id` or include it explicitly.
- **A single noisy tenant can degrade performance for the entire platform.** Mitigation requires query monitoring, per-tenant rate limiting, and the willingness to migrate large tenants out of the shared schema when this becomes a real problem.
- **Tenant deletion is not as clean as in schema-per-tenant.** Wiping a tenant requires deleting rows across many tables instead of a single `DROP SCHEMA`. This must be implemented carefully, ideally with a soft-delete plus background cleanup pattern, and tested.

---

## When this decision should be revisited

The default model is RLS, but specific tenants may need to be moved out of the shared schema into a dedicated schema or dedicated database when one or more of these signals appear:

1. **Compliance or contractual isolation requirements.** A customer signs a contract or falls under a regulation that requires demonstrable physical isolation of their data (HIPAA, certain EU data residency frameworks, enterprise contracts with explicit isolation clauses). Non-negotiable.
2. **Noisy neighbor problem.** A single tenant consumes a disproportionate share of resources (CPU, I/O, locks, connection pool) and measurably degrades the experience of other tenants. Concrete trigger: p95 or p99 latency for small tenants degrades beyond agreed SLA and cannot be fixed with indexing or vertical scaling.
3. **Custom data model.** A tenant requires tables, columns, or indexes that no other tenant uses. Forcing them into the shared schema pollutes the model for everyone.
4. **Blast radius isolation (preventive).** A tenant becomes strategically important enough that the cost of a shared-schema bug affecting them is unacceptable. This is a business decision disguised as a technical one.

For each of these cases, the migration path is: create a dedicated schema (or database) for the tenant, copy their data over, update the application's connection routing to send their traffic to the new location, and verify with end-to-end tests before cutting over. The application code should be designed from day one to support this — specifically, the tenant resolution layer (middleware) must be the only place that knows where a tenant's data physically lives.

---

## References

- PostgreSQL docs — [Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- PostgreSQL docs — [`SET`](https://www.postgresql.org/docs/current/sql-set.html) (note the difference between `SET` and `SET LOCAL`)
- MADR template — https://adr.github.io/madr/