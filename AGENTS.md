# AGENTS

This document describes how to authenticate and interact with the SA Navigator API for AI agents (OpenClaw, Hermes, etc.).

## Authentication

### API Keys (Recommended for Agents)

Agents should use **API keys** via the `X-API-Key` header. API keys are scoped to a user and have a role that determines what they can do.

```
X-API-Key: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Creating API Keys

Create keys through the API (requires JWT auth):

```bash
curl -X POST http://localhost:8000/api/auth/keys \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"name": "openclaw-agent", "role": "viewer"}'
```

**Response:**
```json
{
  "id": "uuid-here",
  "name": "openclaw-agent",
  "role": "viewer",
  "active": true,
  "key": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "key_prefix": "sk-xxxxxxx••••••••",
  "expires_at": null,
  "created_at": "2025-01-01T00:00:00"
}
```

> ⚠️ **Save the raw `key` value immediately.** It is only shown once during creation.

### Role Options

| Role | Level | Permissions |
|------|-------|-------------|
| `viewer` | 0 | Read-only (GET endpoints) |
| `editor` | 1 | Full CRUD on opportunities + API key management |
| `admin` | 2 | All editor permissions + user management |

## API Reference

### Base URL

```
http://localhost:8000
```

### Endpoints

#### List Opportunities

```
GET /api/opportunities
```

Query params: `search`, `owner`, `client`, `project`, `status`, `sort`, `page`, `page_size`, `include_deleted`

```bash
curl -H "X-API-Key: sk-..." \
  "http://localhost:8000/api/opportunities?search=acme&page_size=10"
```

#### Get Opportunity

```
GET /api/opportunities/{id}
```

#### Create Opportunity

```
POST /api/opportunities
```

Requires `editor` role or higher.

```bash
curl -X POST http://localhost:8000/api/opportunities \
  -H "X-API-Key: sk-..." \
  -H "Content-Type: application/json" \
  -d '{"client": "Acme", "project": "Cloud Migration", "owner": "Jane Smith"}'
```

#### Update Opportunity

```
PATCH /api/opportunities/{id}
```

Requires `editor` role. Add `?log_changes=true` to record change history.

#### Delete Opportunity

```
DELETE /api/opportunities/{id}
```

Requires `editor` role.

**Soft delete.** The row is marked `status: "Lost"` plus a `deleted_at`
timestamp and is hidden from list, search and detail views - it is **not**
removed from the database, and its updates and change logs are preserved.
Deleting an already-deleted opportunity is a successful no-op (still `204`).
Hidden rows are reachable only with `?include_deleted=true`.

#### Restore Opportunity

```
POST /api/opportunities/{id}/restore
```

Requires `editor` role. Clears `deleted_at` and puts the previous status back
(held in `status_before_delete`), so a restore is lossless. Returns `400` if
the opportunity is not currently deleted, `404` if it does not exist.

#### Listing deleted opportunities

```
GET /api/opportunities?include_deleted=true
GET /api/opportunities/{id}?include_deleted=true
```

Deleted rows are excluded unless `include_deleted=true` is passed. The `status`
filter never reveals deleted rows on its own - `?status=Lost` returns only
opportunities that were genuinely marked Lost, not deleted ones.

#### Opportunity Updates Feed

```
GET /api/opportunities/{id}/updates
POST /api/opportunities/{id}/updates
```

GET returns the activity feed (change logs + manual updates). POST adds a manual text update (requires `editor`).

#### List API Keys

```
GET /api/auth/keys
```

Requires JWT auth. Returns masked key list (no raw keys).

#### Revoke API Key

```
DELETE /api/auth/keys/{id}
```

Requires JWT auth. Deactivates the key.

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad request (invalid role name, etc.) |
| 401 | Missing or invalid credentials |
| 403 | Role insufficient for this operation |
| 404 | Resource not found |
| 422 | Validation error (check `detail` for field errors) |

## Rate Limiting

No rate limits are enforced in this version. Production deployments should add rate limiting via middleware or reverse proxy (e.g., NGINX, Cloudflare).

## Schema Examples

### Opportunity

```json
{
  "id": "uuid",
  "client": "Acme Corp",
  "project": "Digital Transformation",
  "owner": "John Doe",
  "ccw_estimate": "500k",
  "salesforce_link": "",
  "sow_sod": "",
  "total_tcv": 500000.0,
  "total_bgp": 75000.0,
  "total_margin": 15.0,
  "account_manager": "Jane Smith",
  "close_date": "2025-06-30",
  "status": "New",
  "deleted_at": null,
  "status_before_delete": null,
  "created_by": "uuid",
  "creator_name": "Jane Smith",
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

### List Response

```json
{
  "items": [...],
  "total": 123,
  "page": 1,
  "page_size": 25,
  "pages": 5
}
```
