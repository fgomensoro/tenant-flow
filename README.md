# tenant-flow

**A small, inspectable slice of a multi-tenant integration service.** A SaaS team receiving events for multiple customers needs a way to store and read each customer's data without relying on every API query to remember a tenant filter. This project explores that boundary with a FastAPI service, PostgreSQL row-level security (RLS), and an event schema designed for external integrations.

The current code lets an admin create a tenant and lets a caller read that tenant and its events. It does **not** yet receive Shopify or Stripe webhooks, write events through an API, run a processing worker, or provide a RAG/anomaly-detection layer. There is no frontend. The integration scenario shapes the data model and architecture decisions; provider integration remains future work.

## What to inspect

| Layer | Implemented evidence |
| --- | --- |
| HTTP API | [`src/tenant_flow/main.py`](./src/tenant_flow/main.py) wires FastAPI routes for health, admin tenant creation, current tenant, and event reads. |
| Tenant context | [`tenant_context.py`](./src/tenant_flow/middleware/tenant_context.py) checks an admin token or requires a tenant UUID header; [`tenant_session.py`](./src/tenant_flow/dependencies/tenant_session.py) passes that UUID into a database transaction. |
| Integration data model | [Alembic revisions](./alembic/versions/) create tenant, event, and processing-attempt tables with RLS policies. The event table stores raw bytes and JSON payloads and has a unique `(tenant_id, provider, idempotency_key)` constraint; [`models/`](./src/tenant_flow/models/) and [`schemas/`](./src/tenant_flow/schemas/) map storage and API response shapes. |
| Local operations | [`docker-compose.yml`](./docker-compose.yml) starts PostgreSQL; [`scripts/`](./scripts/) initializes the application role and seeds two demo tenants. [`justfile`](./justfile) records development commands. |

The implemented request path is **HTTP header → middleware → tenant-scoped SQLAlchemy session → PostgreSQL RLS → API response**. This shows work across API, persistence, and local infrastructure. The tenant header is currently caller supplied rather than derived from an authenticated identity, so this is an engineering exercise, not a production-ready authorization model.

For the design trade-offs, read [ADR 001: multi-tenancy strategy](./docs/adr/001-multitenancy-strategy.md) and [ADR 002: event processing model](./docs/adr/002-event-processing-model.md). The ADRs describe intended behavior as well as implemented schema; for example, ADR 002's webhook intake, duplicate handling, and worker flow are not yet implemented.

## Run the current slice locally

You need Docker with Compose, [`uv`](https://docs.astral.sh/uv/), `curl`, and an available local port 5432. From the repository root, create a **local-only** `.env` file (ignored by Git):

```dotenv
POSTGRES_USER=tenantflow
POSTGRES_PASSWORD=local-admin-password
POSTGRES_APP_PASSWORD=local-app-password
POSTGRES_DB=tenantflow_dev
POSTGRES_PORT=5432
ADMIN_TOKEN=local-demo-token
```

Then run:

```sh
docker compose up -d
uv sync
uv run alembic upgrade head
PYTHONPATH=src uv run python scripts/seed.py
uv run uvicorn tenant_flow.main:app --app-dir src
```

In a second terminal, exercise the routes that exist today:

```sh
curl http://127.0.0.1:8000/
curl -X POST http://127.0.0.1:8000/admin/tenants \
  -H 'X-Admin-Token: local-demo-token' \
  -H 'Content-Type: application/json' \
  -d '{"name":"Demo Co","slug":"demo-co"}'
curl -H 'X-Tenant-ID: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa' \
  http://127.0.0.1:8000/tenants/me
curl -H 'X-Tenant-ID: aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa' \
  http://127.0.0.1:8000/events
```

The seeded `aaaaaaaa-...` tenant is Acme Corp. `/events` returns an empty list in a fresh database because the repository has no event ingestion route or event seed. Stop the API with Ctrl-C and PostgreSQL with `docker compose down` when finished.

The [`justfile`](./justfile) includes `just dev`, `just seed`, and `just test` if you have `just` installed. At present, [`tests/`](./tests/) has no test cases, so `uv run pytest` reports no tests collected rather than a passing suite.

## Repository map

```text
src/tenant_flow/   FastAPI app, routes, middleware, DB sessions, models, schemas
alembic/           Active schema migrations, including RLS policies
migrations/        Standalone SQL schema scripts (not run by Alembic)
scripts/           PostgreSQL role initialization and demo tenant seed
tests/             Pytest scaffolding; no test cases yet
docs/adr/          Architecture decision records
docker-compose.yml Local PostgreSQL service
pyproject.toml     Python dependencies and tool configuration
justfile           Development command shortcuts
```

## License

MIT — see [`LICENSE`](./LICENSE).
