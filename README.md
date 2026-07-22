# Task API

A REST API for managing a to-do list, built with Python and FastAPI. It supports full CRUD operations (create, read, update, delete), user authentication via Supabase, validates incoming data, returns proper HTTP status codes, and ships with interactive API docs via Swagger UI. Tasks are persisted in PostgreSQL, running in Docker alongside the app — the whole stack starts with a single command.

## Run it

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Podman) installed and running, plus a free [Supabase](https://supabase.com) project for authentication.

```bash
git clone <your-repo-url>
cd todo-api
cp .env.example .env
docker compose up
```

Visit `http://localhost:8000/docs` for interactive API docs, or `http://localhost:8000/` for basic API info.

The `tasks` table and three example tasks are created automatically on first run. Restarting the stack (`docker compose down` then `docker compose up`) does not duplicate the seed data or lose existing tasks — a Docker volume keeps the database's data outside the container's lifecycle.

### Running without Docker (local development)

If you'd rather run the app directly against a locally running Postgres instance instead of the full compose stack:

```bash
python3 -m venv venv
source venv/Scripts/activate   # Windows Git Bash — use venv/bin/activate on Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

This expects `DATABASE_URL` in your `.env` to point at `localhost` (see `.env.example`) rather than the `db` service name used inside Docker's network.

## Configuration

Copy `.env.example` to `.env` and fill in your own values:

```
DATABASE_URL=postgresql://postgres:dev@localhost:5432/tasks
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_anon_key
PORT=8000
```

- `DATABASE_URL` — connection string for the Postgres container.
- `SUPABASE_URL` / `SUPABASE_KEY` — from your Supabase project's **Project Settings → API**. Use the **anon** key here, never the `service_role` key.

`.env` is git-ignored — real credentials never get committed. `.env.example` documents which variables are required with placeholder values.

## Authentication

User accounts, password hashing, and token signing are all handled by **Supabase Auth** — this API never touches passwords or cryptography directly. It only forwards credentials to Supabase and verifies the tokens Supabase issues.

**How it works:**

1. A client signs up or logs in with an email and password.
2. Supabase validates the credentials and returns an access token (JWT).
3. The client sends that token in the `Authorization: Bearer <token>` header on every request to a protected route.
4. A reusable FastAPI dependency (`get_current_user`) extracts the token and asks Supabase to verify it before the route runs.

Verification is a live check against Supabase (`supabase.auth.get_user(token)`), not just a local signature check — so logging out revokes access immediately, on the very next request, rather than waiting for the token to naturally expire.

| Method | Path | Auth required | Description |
|---|---|---|---|
| POST | `/auth/signup` | No | Create a new user account |
| POST | `/auth/login` | No | Authenticate and receive an access token |
| POST | `/auth/logout` | Yes (Bearer token) | End the current session |
| GET | `/protected/profile` | Yes (Bearer token) | Return the logged-in user's profile data |
| GET | `/protected/dashboard` | Yes (Bearer token) | Example second protected route, demonstrates the auth guard is reusable |
| GET | `/public/info` | No | Open, unauthenticated endpoint |

**Auth status codes:** `201` created (signup) · `200` success (login/read) · `204` no content (logout) · `400` bad request (missing email/password) · `401` unauthorized (missing, malformed, invalid, or expired token).

**Testing auth via curl:**

```bash
# Sign up
curl -i -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Log in
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Call a protected route (replace TOKEN with the access_token from login)
curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer TOKEN"
```

## Task endpoints

| Method | Path          | Description                          |
|--------|---------------|---------------------------------------|
| GET    | /             | API info                              |
| GET    | /health       | Health check                          |
| GET    | /tasks        | List all tasks                        |
| GET    | /tasks/{id}   | Get one task                          |
| POST   | /tasks        | Create a task                         |
| PUT    | /tasks/{id}   | Update a task's title and done status |
| DELETE | /tasks/{id}   | Delete a task                         |

Validation: `POST` and `PUT` require a non-empty `title` — missing or empty returns `400`. Requesting an unknown `id` returns `404`. Successful creates return `201`, successful deletes return `204` with no body.

## Example request

```
$ curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title":"Buy milk"}'
HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
```

## Swagger UI

`/docs` lists every endpoint with a "Try it out" button that sends real requests — the full CRUD cycle (create, list, update, delete) can be run entirely from this page, no `curl` needed. Protected routes show a lock icon; click **Authorize** at the top of the page, paste a bearer token obtained from `/auth/login`, and `/docs` will attach it to every subsequent "Try it out" call automatically.

![Swagger UI](screenshots/swagger.png)

## Data storage

### Evolution of this project

This project moved through three storage layers as a deliberate learning progression — the API itself never changed, only what sits underneath it:

1. **In-memory** — a Python list, gone on every restart.
2. **SQLite** — a single file (`tasks.db`) on disk, survives app restarts but not a clean environment.
3. **PostgreSQL in Docker** (current) — a real database server, running in its own container, with a proper connection string and secrets kept out of version control.

### Why Postgres + Docker

Running Postgres in a container means nobody needs to install or configure a database server by hand — `docker compose up` gives every clone of this repo an identical, disposable database. The app and the database are two separate services (`api` and `db`), each with their own container, connected over Docker's internal network. Data lives in a Docker volume, so it survives container restarts even though the containers themselves are disposable.

One real issue worth noting: Postgres takes a moment to become ready to accept connections after its container starts (it briefly restarts itself during first-time setup). A plain `depends_on` only waits for the container to exist, not for Postgres inside it to be ready — so `compose.yaml` uses a `healthcheck` (`pg_isready`) and a `condition: service_healthy` dependency to make the app wait for the database to genuinely be reachable before starting.

### Example query

```sql
SELECT * FROM tasks WHERE done = true;
```

Run against the database inside the `db` container (`docker exec -it <container> psql -U postgres -d tasks`) — returned every task currently marked complete, confirming the running API and the database are always reading the same live data.

![Database view](screenshots/db-screenshot.png)

## Notes

- No database migrations yet — schema changes currently mean manually altering the table.
- No production-hardening (TLS, connection pooling, secrets management beyond `.env`) — this is a local development / learning setup.
- Task endpoints (`/tasks`) are not currently gated behind authentication — only the `/protected/*` demo routes require a token. Wiring auth into the task routes themselves would be a natural next step.