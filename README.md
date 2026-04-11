# tenant-flow

A multi-tenant integration platform built as an engineering deep-dive. Webhook ingestion (Shopify, Stripe), Postgres row-level security, idempotent processing, and a RAG layer for financial anomaly detection.

---

## What this is

tenant-flow is a from-scratch implementation of a B2B SaaS integration platform: it ingests webhooks from external systems (Shopify, Stripe, and others), processes them safely under multi-tenant isolation, and exposes the resulting data through an API and an AI layer that can detect anomalies and answer natural-language questions.

The scope is intentionally narrow. The goal is not to build a product — it is to build the parts of a real system where the interesting engineering decisions live: tenant isolation, idempotency, webhook reliability, retrieval-augmented generation with strict data boundaries, and operational concerns like observability and deployment.

## Why this exists

This repository is a learning project with a clear constraint: every meaningful decision must be reasoned about, documented, and defensible. Tutorials are skipped in favor of building the hard parts directly and writing down the trade-offs along the way.

The primary artifact of the project is not just the code — it is the set of **Architecture Decision Records** in [`docs/adr/`](./docs/adr/). Each ADR captures one decision: the context, the alternatives considered, what was chosen, and what trade-offs are being explicitly accepted. Reading the ADRs in order should give a clear picture of how the system was reasoned into existence.

If you are evaluating this repository, the ADRs are the place to start. The code shows what was built; the ADRs show why it was built that way.

## Status

Early work in progress. Phase 1 (multi-tenant webhook processor) is being built first, followed by Phase 2 (RAG layer for anomaly detection and natural-language queries over tenant data).

## Repository layout

```
tenant-flow/
├── docs/
│   └── adr/                      # Architecture Decision Records
│       └── 001-multitenancy-strategy.md
├── .gitignore
├── LICENSE
└── README.md
```

More structure will be added as the project grows. This README will be updated to reflect the current state at the end of each phase.

## License

MIT — see [`LICENSE`](./LICENSE).