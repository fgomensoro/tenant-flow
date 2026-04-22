dev:
    uv run uvicorn tenant_flow.main:app --reload --app-dir src

lint:
    uv run ruff check .

format:
    uv run ruff format .

test:
    uv run pytest

db:
    psql -h localhost -U tenantflow_app -d tenantflow_dev
