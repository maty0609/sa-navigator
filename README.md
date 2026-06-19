# SA Navigator

Opportunity dashboard for internal team use. Full CRUD management of sales opportunities with search, filtering, and multi-user access.

[Features](#features) • [Quick Start](#quick-start) • [Tech Stack](#tech-stack) • [Configuration](#configuration) • [API](#api) • [Project Structure](#project-structure) • [Deployment](#deployment) • [Development](#development)

## Features

- **Opportunity CRUD** — Create, view, edit, and delete opportunities (Owner, Technology, Description)
- **Search & Filter** — Full-text search across fields, filter by owner or technology
- **Authentication** — JWT-based login with access + refresh tokens (BCrypt)
- **Multi-user** — Role-based access (admin / editor)
- **Pagination** — Paginated listings with configurable page size
- **Responsive UI** — shadcn/ui + TailwindCSS

## Quick Start

Requires **Docker & Docker Compose**.

```bash
git clone <repo-url> && cd sa-navigator
docker compose up -d --build
```

Then create at least one user before logging in:

```bash
docker compose exec backend python scripts/seed_users.py -u admin -p admin123 -r admin
```

| | |
|---|---|
| **Frontend** | http://localhost:3000/login |
| **Backend API** | http://localhost:8000/docs |
| **Default credentials** | `admin` / `admin123` |

Create more users:

```bash
docker compose exec backend python scripts/seed_users.py -u alice -p pass123 -r editor
```

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, FastAPI, SQLModel, Alembic |
| **Database** | PostgreSQL 16 |
| **Frontend** | Next.js 16 (App Router), React 19, TailwindCSS v4 |
| **UI** | shadcn/ui, Radix UI, Lucide icons |
| **State** | React Query (TanStack Query) |
| **Auth** | JWT access tokens (1h) + server-side refresh tokens (7d) |
| **Orchestration** | Docker Compose |

## Configuration

### Backend (`backend/.env`)

Copy `.env.example` and adjust:

```ini
# Database
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/sa_navigator

# JWT — change to a random secret in production
JWT_SECRET_KEY=change-me-to-a-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS — list of allowed origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (`frontend/.env.local`)

```ini
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API

All endpoints return JSON. Interactive docs available at `http://localhost:8000/docs`.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Authenticate, receive access + refresh tokens |
| `POST` | `/api/auth/refresh` | Exchange refresh token for new access + refresh tokens |
| `POST` | `/api/auth/logout` | Revoke refresh token |

### Opportunities

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/opportunities` | List with search, filter, pagination |
| `POST` | `/api/opportunities` | Create |
| `GET` | `/api/opportunities/{id}` | Detail |
| `PATCH` | `/api/opportunities/{id}` | Partial update |
| `DELETE` | `/api/opportunities/{id}` | Delete |

**Query parameters** (list endpoint):

| Parameter | Type | Description |
|---|---|---|
| `search` | string | Search across owner, technology, description |
| `owner` | string | Filter by owner (partial match) |
| `technology` | string | Filter by technology (partial match) |
| `sort` | string | Sort field, prefix `-` for descending (default: `-created_at`) |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page, 1–100 (default: 25) |

### Authentication

All endpoints require a `Bearer` token:

```
Authorization: Bearer <access_token>
```

Access tokens expire after 1 hour. Use the refresh endpoint to get a new pair without re-authenticating.

## Project Structure

```
sa-navigator/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── scripts/
│   │   └── seed_users.py        # User creation utility
│   ├── app/
│   │   ├── api/                  # Route handlers
│   │   │   ├── auth.py
│   │   │   └── opportunities.py
│   │   ├── models/               # SQLModel ORM models
│   │   │   ├── user.py
│   │   │   ├── opportunity.py
│   │   │   └── refresh_token.py
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   │   ├── auth.py
│   │   │   └── opportunity.py
│   │   ├── services/             # Business logic
│   │   │   └── auth_service.py
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── config.py             # Settings (env vars)
│   │   ├── database.py           # Engine, session factory
│   │   └── deps.py               # Auth dependencies
│   ├── migrations/               # Alembic migrations
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   └── src/
│       ├── app/                  # Next.js App Router pages
│       │   ├── (dashboard)/      # Protected dashboard routes
│       │   ├── login/            # Login page
│       │   ├── layout.tsx        # Root layout
│       │   ├── providers.tsx     # React Query + Theme providers
│       │   └── globals.css       # TailwindCSS + shadcn theme vars
│       ├── components/           # React components
│       │   ├── layout/
│       │   ├── opportunities/
│       │   └── ui/               # shadcn/ui primitives
│       └── lib/                  # API client, React Query hooks
└── README.md
```

## Deployment

### Docker Compose (production)

Use the `.env` files to configure secrets before deploying. Key changes for production:

1. Generate a strong `JWT_SECRET_KEY`
2. Set `DATABASE_URL` to your production PostgreSQL instance
3. Set `ALLOWED_ORIGINS` to your frontend domain
4. Remove `--reload` from the backend command in `docker-compose.yml`
5. Set `NEXT_PUBLIC_API_URL` to your backend URL

```bash
# Production build (no --reload, optimized images)
docker compose -f docker-compose.prod.yml up -d --build
```

### Running the tests

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests/ -v
```

Tests use in-memory SQLite — no PostgreSQL needed.

### Linting

```bash
cd backend
ruff check app/ tests/
```

## Development

### Local setup (no Docker)

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # edit with your DB credentials
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL
npm run dev   # http://localhost:3000
```

### Adding a migration

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

### Adding a shadcn/ui component

```bash
cd frontend
npx shadcn@latest add <component-name>
```

## License

Internal use only.
