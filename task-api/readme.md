# Task API

A simple to-do list REST API built with FastAPI, with full CRUD and SQLite persistence.

## Why SQLite

SQLite needs no separate server or install — the whole database is one file
(`tasks.db`), created automatically the first time the app runs. That's enough
for this project, and it means anyone cloning the repo gets a working database
with zero setup.

## Where the database lives

`tasks.db` in the project root. It's git-ignored, so every fresh clone starts
with a clean, auto-seeded database rather than inheriting old data.

## Run it

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive Swagger UI.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | / | API info |
| GET | /health | Health check |
| GET | /tasks | List tasks (supports `?done=true` and `?search=milk`) |
| GET | /tasks/{id} | Get one task |
| POST | /tasks | Create a task |
| PUT | /tasks/{id} | Update a task |
| DELETE | /tasks/{id} | Delete a task |
| GET | /stats | Task counts (total/done/open) |
| POST | /reset | Reset to the 3 seed tasks |

## Example request


```
PS D:\uni\projects\CRUD> curl.exe --% -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d "{\"title\":\"Buy groceries\"}"
HTTP/1.1 201 Created
date: Tue, 08 Sep 2026 18:23:49 GMT
server: uvicorn
content-length: 41
content-type: application/json

{"id":6,"title":"Buy groceries","done":0}
```

## Exploring the database directly

Opened `tasks.db` in DB Browser for SQLite and ran:

```sql
SELECT * FROM tasks WHERE done = 0;
```

Returned all 5 tasks currently marked incomplete — confirming the API and
the database file are reading the exact same data, with no syncing step
in between.

![DB Browser screenshot](screenshot.png)