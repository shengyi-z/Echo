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
```

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
- APScheduler uses the same DB for job persistence via SQLAlchemy job store, so scheduled jobs survive restarts.
- For production-grade long-lived flows and retries, consider Temporal (Python SDK).
# Echo