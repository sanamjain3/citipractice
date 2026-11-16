# Payment Approval MVP

A small full-stack app for reviewing payments. New transactions over **10,000** are automatically **FLAGGED** for manual review. Reviewers approve or reject anything still `PENDING` or `FLAGGED` from a React dashboard.

| Layer     | Stack                                                          |
|-----------|----------------------------------------------------------------|
| API       | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0               |
| Database  | SQLite locally; PostgreSQL by changing one env var              |
| Frontend  | React 18 + TypeScript, Vite                                     |
| Tests     | pytest + FastAPI TestClient (in-memory SQLite, 31 tests)        |

---

## Quick start

Prerequisites: **Python 3.10+** and **Node 18+**.

### Backend (Windows PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env            # optional; defaults work without it
uvicorn app.main:app --reload --port 8000 --no-access-log
```

macOS / Linux: replace the activate line with `source .venv/bin/activate` and `copy` with `cp`.

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- On first start the app creates `payments.db` and seeds **8 sample transactions** (2 of each status). Delete the file to reseed.
- `--no-access-log` turns off uvicorn's own access log, because the app's middleware already writes a richer JSON line for every request.

### Frontend

```powershell
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

Vite proxies `/api` and `/health` to `localhost:8000`, so no CORS setup is needed in dev. For a production build, set `VITE_API_BASE_URL` (see `frontend/.env.example`) and run `npm run build`. The output goes to `frontend/dist/`.

### Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```

Each test gets its own in-memory SQLite database built through the app factory. Tests never touch `payments.db` and ignore `.env`.

---

## Configuration (`backend/.env`)

| Variable          | Default                       | Notes                                                       |
|-------------------|-------------------------------|-------------------------------------------------------------|
| `DATABASE_URL`    | `sqlite:///./payments.db`     | Any SQLAlchemy URL                                          |
| `FLAG_THRESHOLD`  | `10000`                       | Amounts **strictly greater** than this are flagged          |
| `SEED_ON_STARTUP` | `true`                        | Seeds only when the table is empty (safe to restart)        |
| `CORS_ORIGINS`    | `["http://localhost:5173"]`   | JSON list                                                   |
| `LOG_LEVEL`       | `INFO`                        |                                                             |

### Switching to PostgreSQL

```powershell
pip install "psycopg[binary]"
# backend/.env
DATABASE_URL=postgresql+psycopg://payments:secret@localhost:5432/payments
```

No code changes needed. The status column is stored as `VARCHAR + CHECK` rather than a native enum, so the schema works the same on both databases.

---

## API

| Method | Path                                   | Description                                         |
|--------|----------------------------------------|-----------------------------------------------------|
| GET    | `/health`                              | `200 {"status":"ok","database":"ok"}`, or `503` if the DB is unreachable |
| GET    | `/api/transactions`                    | List, newest first. Query: `status`, `account_id`, `limit`, `offset` |
| GET    | `/api/transactions/summary`            | Counts per status and total amount per currency     |
| POST   | `/api/transactions`                    | Create `{account_id, amount, currency}` and get back `201` with status set |
| GET    | `/api/transactions/{id}`               | One transaction, or `404`                           |
| POST   | `/api/transactions/{id}/approve`       | `PENDING`/`FLAGGED` → `APPROVED`. `409` if already decided |
| POST   | `/api/transactions/{id}/reject`        | `PENDING`/`FLAGGED` → `REJECTED`. `409` if already decided |

Validation: `amount > 0` with at most 2 decimal places, `currency` is a 3-letter code (upper-cased), `account_id` is 1–64 chars. Invalid input returns `422`.

**Status lifecycle**

```
create ──► amount > threshold ? FLAGGED : PENDING ──► APPROVED | REJECTED   (final)
```

---

## Architecture

```
backend/
  app/
    main.py            app factory, lifespan (create tables, seed), middleware, routers
    config.py          Settings (pydantic-settings, reads .env)
    database.py        Engine/session factory; SQLite vs Postgres differences handled here
    models.py          Transaction ORM model + TransactionStatus enum
    schemas.py         Pydantic v2 request/response models
    repository.py      Data access (queries only, no rules)
    services.py        Business logic: assess_risk(), approve/reject transitions
    seed.py            8 sample records, idempotent
    middleware.py      ASGI request-logging middleware
    logging_config.py  JSON log formatter
    dependencies.py    FastAPI DI: session → repository → service
    routers/           HTTP layer: maps domain errors to 404/409
  tests/
frontend/
  src/
    api.ts             typed fetch client
    App.tsx            state, data loading
    components/        SummaryCards, TransactionTable, TransactionForm, StatusBadge
```

Requests flow **router → service → repository → SQLAlchemy**. Each layer only calls the one below it, so the risk rule (`services.assess_risk`) can be unit-tested with no database or HTTP involved.

### Observability

Every HTTP request emits one JSON log line:

```json
{"timestamp": "2026-11-15T13:22:29.04+00:00", "level": "INFO", "logger": "app.request",
 "message": "request completed", "request_id": "c4e2f7b1f3bd4a8b92a87ddf9f617d2b",
 "method": "GET", "path": "/health", "status_code": 200, "duration_ms": 64.03}
```

- If the caller sends a well-formed `X-Request-ID` (for example from a load balancer or gateway), it is reused. Otherwise the app generates one. Either way it is returned in the `X-Request-ID` response header so a user report can be matched to the exact log line.
- The middleware is plain ASGI (not `BaseHTTPMiddleware`), so it doesn't buffer responses, and it still logs `500` when the app raises an exception.
- The logging module is named `logging_config.py` on purpose. A file called `logging.py` would shadow Python's standard `logging` module.

---

## AWS deployment notes

```
            ┌─────────────┐
 Browser ──►│ CloudFront  │──► S3 (private, OAC)          React build (frontend/dist)
            │   + WAF     │
            └──────┬──────┘
                   │ /api/*, /health
                   ▼
            ┌─────────────┐      ┌───────────────────────┐
            │     ALB     │─────►│ ECS Fargate service   │  FastAPI container, ≥2 tasks
            │ (HTTPS/ACM) │      │ private subnets, 2 AZ │  health check: GET /health
            └─────────────┘      └──────────┬────────────┘
                                            │
                     ┌──────────────────────┼──────────────────────┐
                     ▼                      ▼                      ▼
             RDS PostgreSQL         Secrets Manager         CloudWatch Logs
             Multi-AZ, encrypted    DATABASE_URL            JSON logs → Logs Insights,
             (via RDS Proxy)                                metric filters, alarms
```

- **Frontend:** `npm run build` → S3 behind CloudFront with Origin Access Control. Route `/api/*` to the ALB through the same distribution so the browser sees one origin and needs no CORS.
- **API:** containerise with `uvicorn app.main:app --host 0.0.0.0 --workers 2` (or gunicorn with uvicorn workers). Run on ECS Fargate in private subnets. Point the ALB target-group health check at `/health`. Because `/health` checks the database, it reflects actual readiness. Scale on CPU or ALB request count. App Runner is a simpler alternative for an MVP.
- **Database:** RDS for PostgreSQL (Multi-AZ, encrypted at rest, automated backups/PITR). Set `DATABASE_URL` from **Secrets Manager**, injected as an ECS task secret and never baked into the image. Use RDS Proxy when task counts grow.
- **Migrations:** the MVP uses `Base.metadata.create_all()`. Before production, add **Alembic** and run migrations as a one-off ECS task in the deploy pipeline, not at app startup. Set `SEED_ON_STARTUP=false` in every non-dev environment.
- **Logging and metrics:** the awslogs driver ships the JSON lines to CloudWatch. Example Logs Insights queries:
  ```
  fields @timestamp, method, path, status_code, duration_ms
  | filter logger = "app.request" and status_code >= 500
  | sort @timestamp desc
  ```
  ```
  stats pct(duration_ms, 95) as p95 by path | sort p95 desc
  ```
  Add metric filters and alarms on 5xx rate and p95 latency, and look up `request_id` for any user-reported error. Use AWS X-Ray or the ADOT/OpenTelemetry sidecar for distributed tracing.
- **Security:** WAF on CloudFront, TLS via ACM, and security groups that allow only ALB → tasks and tasks → RDS. Least-privilege task IAM role. Images are scanned in ECR.
- **CI/CD:** GitHub Actions or CodePipeline: run pytest and `npm run build` → push the image to ECR → run migrations → ECS rolling or blue/green deploy (CodeDeploy) → sync the S3 bucket and invalidate CloudFront.
- **Next step for risk:** for richer rules or ML scoring, publish `TransactionCreated` events to SQS/EventBridge and score asynchronously. A Lambda or worker updates the status, which keeps the create endpoint fast.

---

## Known MVP limitations

- **No authentication or authorisation.** Anyone who can reach the API can approve payments. Put Cognito (or your IdP) in front of the API, check a reviewer role on approve/reject, and record *who* decided and *when* (add `decided_by` and `decided_at` columns plus an audit table).
- The flag threshold ignores currency: 10,000 JPY is flagged the same as 10,000 USD would be. Use per-currency thresholds or FX normalisation for real use.
- There is no idempotency key on `POST /api/transactions`. A retried request creates a duplicate.
- Approve and reject use read-then-write without row locking. Under concurrent reviewers, use `SELECT … FOR UPDATE` or an optimistic version column on PostgreSQL.
- The dashboard's account/ID search only filters the rows already loaded (the newest 100 for the selected status).
