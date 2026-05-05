dev:
    uv run uvicorn tenant_flow.main:app --reload --app-dir src

lint:
    uv run ruff check .

format:
    uv run ruff format .

fix:
    uv run ruff check . --fix
    uv run ruff format .

seed:
    PYTHONPATH=src uv run python scripts/seed.py

test:
    uv run pytest

db:
    psql -h localhost -U tenantflow_app -d tenantflow_dev
