# Inndxd — Next Steps

> **Date:** 2026-05-11
> **Current state:** Stages 1–4 complete. Stage Cloud next.
> **Reference:** [inndxd-project/overview/masterplan.md](https://github.com/Smith-Gray-Pty-Ltd/inndxd-project) v5.5

---

## Stage 4.5 — Polish & Cleanup

Quick tasks to tighten the dashboard before moving to Cloud.

| # | Task | Est. |
|---|------|------|
| 1 | Rebuild `bundle.css` with full Tailwind v4 JIT config so inline fallback utilities are natively available | 1h |
| 2 | Audit all 24 templates for dark theme consistency — ensure every page uses `data-theme="black"` correctly | 1h |
| 3 | Fix `justfile` — add `dev` (run web + api), `build-css` (tailwind CLI), `watch-css` commands | 0.5h |
| 4 | Add `page_title` block to admin templates (currently missing) | 0.5h |
| 5 | Responsive audit — check all pages at mobile/tablet/desktop with DaisyUI breakpoints | 1h |
| 6 | Add loading indicators (`.loading` spinner) to HTMX polling targets | 0.5h |

**Total: ~4.5 hours**

---

## Stage Cloud — Business Operations

> **Repo:** `github.com/Smith-Gray-Pty-Ltd/inndxd-cloud` (private)
> **Full plan:** [`inndxd-cloud/planning/stage-cloud.md`](https://github.com/Smith-Gray-Pty-Ltd/inndxd-project/blob/main/inndxd-cloud/planning/stage-cloud.md)
> **Goal:** Business operations at inndxd.com — signup, billing, admin, traffic routing.

### Phase 1: Website — Public Marketing Site
**6 tasks, ~4 hours**

| # | Task |
|---|------|
| 1.1 | Create `apps/website/pyproject.toml` — FastAPI + Jinja2 + uvicorn |
| 1.2 | Create FastAPI app `inndxd_cloud_website/main.py` — port 8003 |
| 1.3 | Create `templates/base.html` — public layout (no auth, no sidebar) |
| 1.4 | Create landing page — hero, tagline, CTA, 3-column feature grid |
| 1.5 | Create pricing page — 3 tiers (Starter/Pro/Enterprise) + comparison table |
| 1.6 | Create docs + blog stubs — placeholder pages |

### Phase 2: Identity — Signup & Auth
**8 tasks, ~6 hours**

| # | Task |
|---|------|
| 2.1 | Create `apps/identity/pyproject.toml` — FastAPI + httpx + jinja2 |
| 2.2 | Create Customer model — SQLAlchemy, UUID, OAuth fields |
| 2.3 | Create signup + login routers — email/password flow |
| 2.4 | Create Google OAuth provider — redirect, callback, upsert Customer |
| 2.5 | Create GitHub OAuth provider |
| 2.6 | Create auth templates — signup.html, login.html with OAuth buttons |
| 2.7 | Create identity app `main.py` — port 8004 |
| 2.8 | Create CustomerRepository — get_by_email, get_by_oauth_id, create |

### Phase 3: Billing — Stripe Subscriptions
**7 tasks, ~5 hours**

| # | Task |
|---|------|
| 3.1 | Create `apps/billing/pyproject.toml` — stripe SDK |
| 3.2 | Create plan definitions — Starter (free), Pro ($49/mo), Enterprise (custom) |
| 3.3 | Create Subscription + Invoice models |
| 3.4 | Create Stripe checkout session handler — POST /checkout |
| 3.5 | Create Stripe webhook handler — session completed, subscription updated |
| 3.6 | Create billing app `main.py` — port 8005 |
| 3.7 | Create manage subscription route — view, cancel |

### Phase 4: Admin — Internal Panel
**6 tasks, ~4 hours**

| # | Task |
|---|------|
| 4.1 | Create `apps/admin/pyproject.toml` |
| 4.2 | Create admin dashboard — metrics (customers, ARR, instances) |
| 4.3 | Create customer management — search, detail, impersonate |
| 4.4 | Create instance monitoring — list, health, provision |
| 4.5 | Create analytics dashboard — MRR chart, churn, conversion |
| 4.6 | Create admin app `main.py` — port 8006, sidebar layout |

### Phase 5: Gateway — Traffic Routing
**4 tasks, ~3 hours**

| # | Task |
|---|------|
| 5.1 | Create `apps/gateway/pyproject.toml` — FastAPI + httpx |
| 5.2 | Create tenant-to-instance router — DB lookup + fallback config |
| 5.3 | Create reverse proxy handler — wildcard `*.inndxd.ai` → proxy |
| 5.4 | Create VPS provision stub — register tenant→instance mapping |

**Total: 31 tasks, ~22 hours**

### Dependency Chain

```
Phase 1 (Website)     ──► standalone, no deps
Phase 2 (Identity)    ──► needs inndxd-core (auth.py), Postgres
Phase 3 (Billing)     ──► needs Phase 2 (Customer model)
Phase 4 (Admin)       ──► needs Phase 2 + Phase 3
Phase 5 (Gateway)     ──► needs inndxd instances running
```

Phases 1 + 2 can run in parallel. Phases 3, 4, 5 are sequential.

---

## Recommended Execution Order

| Batch | What | Parallel |
|---|---|---|
| **Now** | Stage 4.5 polish (6 tasks) | — |
| **Batch A** | Stage Cloud Phase 1 (Website) + Phase 2 (Identity) | Yes — two apps |
| **Batch B** | Stage Cloud Phase 3 (Billing) | Sequential |
| **Batch C** | Stage Cloud Phase 4 (Admin) | Sequential |
| **Batch D** | Stage Cloud Phase 5 (Gateway) | Sequential |

**Getting started:** Clone `inndxd-cloud`, set up the fresh FastAPI project, start with Phase 1 (Website) — it's the simplest app, no DB, no auth, just Jinja2 + Tailwind.
