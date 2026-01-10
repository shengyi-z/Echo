# Echo Assistant (Python Web)

FastAPI-based web backend with Backboard memory integration and durable reminders via APScheduler with a SQLAlchemy job store. Uses SQLite locally for simplicity; you can switch to Postgres with `DATABASE_URL`.

## Setup

1. Create a virtual environment and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Environment variables (optional):

- `BACKBOARD_API_KEY`: your Backboard API key
- `BACKBOARD_BASE_URL`: Backboard API base (defaults to https://api.backboard.io)
- `DATABASE_URL`: e.g., `sqlite:///./data.db` (default) or Postgres `postgresql+psycopg2://user:pass@host:5432/db`
- `TZ_DEFAULT`: default timezone, `UTC` by default

Create a `.env` file in the project root if you prefer:

```
BACKBOARD_API_KEY=your_key_here
BACKBOARD_BASE_URL=https://api.backboard.io
```

## Backboard Setup

- Sign up and generate an API key: https://app.backboard.io/signup
- Review Quickstart/Docs (for official endpoints): https://app.backboard.io/quickstart
- Set `BACKBOARD_API_KEY` in `.env` (see above). `BACKBOARD_BASE_URL` defaults to `https://api.backboard.io` but can be overridden.
- The integration currently posts to a placeholder endpoint in [app/backboard_client.py](app/backboard_client.py). Replace `url = f"{self.base_url}/memory"` with the official memory/thread route from Backboard's docs.

Quick check once your API key is set:

```bash
uvicorn app.main:app --reload
# In another terminal:
curl -X POST http://localhost:8000/tasks \
	-H "Content-Type: application/json" \
	-d '{"title":"Test task","description":"Backboard trial","user_id":"u-demo"}'
```

If `BACKBOARD_API_KEY` is present, [app/backboard_client.py](app/backboard_client.py) will attempt to record the task as memory. Success or failure is logged server-side. Update the endpoint/path to match Backboard's official API to fully enable memory capture.

## Run

Start the API server:

```bash
uvicorn app.main:app --reload
```

## API Quick Test

Create a task:

```bash
curl -X POST http://localhost:8000/tasks \
	-H "Content-Type: application/json" \
	-d '{"title":"Pay bills","description":"Electricity and water","user_id":"u1"}'
```

Create a reminder (set `due_at` a minute from now):

```bash
DUE=$(python - <<'PY'
from datetime import datetime, timedelta
print((datetime.utcnow()+timedelta(minutes=1)).isoformat())
PY
)

curl -X POST http://localhost:8000/reminders \
	-H "Content-Type: application/json" \
	-d '{"task_id":"<TASK_ID>","due_at":"'"$DUE"'","channel":"email"}'
```

List tasks/reminders:

```bash
curl http://localhost:8000/tasks
curl http://localhost:8000/reminders
```

## Notes

- Backboard integration is stubbed in [app/backboard_client.py](app/backboard_client.py). Replace the endpoint with Backboard's official memory API.

## Frontend

- A minimal static frontend is available in [frontend/index.html](frontend/index.html). Open it directly in a browser while the API is running on `localhost:8000`.

## Backboard SDK Demo

- Install dependencies and set the API key in `.env`, then run one of the demos:

```bash
source .venv/bin/activate
pip install -r requirements.txt

# Story streaming demo
BB_DEMO=story python scripts/backboard_demo.py

# Document indexing demo
BB_DEMO=document BB_DOC_PATH=path/to/file.pdf python scripts/backboard_demo.py

# Memory demo
BB_DEMO=memory python scripts/backboard_demo.py
```

- The async wrapper lives in [app/backboard_sdk_client.py](app/backboard_sdk_client.py).
- APScheduler uses the same DB for job persistence via SQLAlchemy job store, so scheduled jobs survive restarts.
- For production-grade long-lived flows and retries, consider Temporal (Python SDK).
# Echo