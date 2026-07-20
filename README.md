# Task API

A small REST API for managing a to-do list, built with Python and FastAPI. It supports full CRUD operations (create, read, update, delete), validates incoming data, returns proper HTTP status codes, and ships with interactive API docs via Swagger UI. Tasks are persisted in a SQLite database, so data survives a server restart.

## Run it

```bash
git clone <your-repo-url>
cd todo-api
python3 -m venv venv
source venv/Scripts/activate   # Windows Git Bash — use venv/bin/activate on Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs, or `http://localhost:8000/` for basic API info.

The database file (`tasks.db`) is created automatically on first run, along with three seeded example tasks. Restarting the server does not duplicate the seed data or wipe existing tasks.

## Endpoints

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

`/docs` lists every endpoint with a "Try it out" button that sends real requests — the full CRUD cycle (create, list, update, delete) can be run entirely from this page, no `curl` needed.

![Swagger UI](screenshots/swagger.png)

## Data storage — SQLite

Tasks are stored in a SQLite database (`tasks.db`) instead of in memory. SQLite was chosen because it needs no separate server or install — the whole database is a single file, created automatically the first time the app runs, which makes the project runnable by anyone with zero setup beyond `pip install`.

The `tasks` table is created automatically if missing, and three example tasks are seeded only when the table is empty — restarting the server does not duplicate them.

`tasks.db` is git-ignored, so a fresh clone starts with a clean, auto-seeded database rather than shipping example data through version control.

### Example query

Run directly against `tasks.db` in a SQLite viewer:

```sql
SELECT * FROM tasks WHERE done = 1;
```

Returned every task currently marked complete — confirming the API and the database file are always in sync, with no separate "syncing" step.

![Database view](screenshots/db-browser.png)

## Notes

- No database migrations yet — schema changes would currently mean manually altering the table.
- SQLite's single-writer model is fine for local development but wouldn't scale to a production app with many simultaneous users — that's what PostgreSQL is for.