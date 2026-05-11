# Inndxd — Next Steps

> **Date:** 2026-05-11
> **Current state:** Stages 1–4 complete. Stage 5 planned, Stage Cloud planned.
> **Canonical plans:** [inndxd-project](https://github.com/Smith-Gray-Pty-Ltd/inndxd-project) — private planning repo.

---

## Stage 5 — Production Polish (33 tasks)

> **Plan:** [`inndxd-project/inndxd/planning/stage5.md`](https://github.com/Smith-Gray-Pty-Ltd/inndxd-project/blob/main/inndxd/planning/stage5.md)

**Phase 1 — Security** (6 tasks): CSRF tokens, secure cookies, SRI hashes, password confirmation, rate limiting, CSP headers

**Phase 2 — Performance** (5 tasks): Pagination, DB indexes, dashboard query optimization, connection pooling, CSS purge

**Phase 3 — Code Quality** (5 tasks): DRY chat routes, remove hardcoded tenant UUID, 403 template, CSS dedup, type hints

**Phase 4 — Testing** (6 tasks): Fixtures, auth/CRUD/HTMX/Admin tests, GitHub CI pipeline

**Phase 5 — UX Polish** (6 tasks): Responsive audit, dark theme consistency, loading states, empty states, form validation, keyboard shortcuts

**Phase 6 — Reliability** (5 tasks): SSE reconnection, Docker fix, error pages, request timing, DB health check

**Priority:** Security → Code Quality → Performance → Testing → Reliability → UX Polish

---

## Stage Cloud (31 tasks)

> **Plan:** [`inndxd-project/inndxd-cloud/planning/stage-cloud.md`](https://github.com/Smith-Gray-Pty-Ltd/inndxd-project/blob/main/inndxd-cloud/planning/stage-cloud.md)

**Phase 1 — Website** (6 tasks): Landing, pricing, docs, blog at inndxd.com
**Phase 2 — Identity** (8 tasks): Signup, Google/GitHub OAuth, Customer model
**Phase 3 — Billing** (7 tasks): Stripe subscriptions, webhooks
**Phase 4 — Admin** (6 tasks): Customer management, instance monitoring
**Phase 5 — Gateway** (5 tasks): `*.inndxd.ai` reverse proxy routing

---

## Proposed Execution Order

| Order | What | Why |
|---|---|---|
| **1st** | Stage 5 Phase 1 (Security) | CSRF/cookies/rate limits before anything public-facing |
| **2nd** | Stage 5 Phase 3-4 (Quality + Tests) | Fix tech debt, add CI to prevent regressions |
| **3rd** | Stage Cloud Phase 1-2 (Website + Identity) | Public presence — can run in parallel with Stage 5 |
| **4th** | Stage 5 Phase 2,5,6 (Performance, UX, Reliability) | Polish while cloud identity is building |
| **5th** | Stage Cloud Phase 3-5 (Billing, Admin, Gateway) | Business monetization |
