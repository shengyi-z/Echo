import os
import logging
import requests
from app.config import settings

log = logging.getLogger(__name__)


class BackboardClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.BACKBOARD_API_KEY
        self.base_url = (base_url or settings.BACKBOARD_BASE_URL).rstrip("/")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update(
                {"Authorization": f"Bearer {self.api_key}"})

    def enabled(self) -> bool:
        return bool(self.api_key)

    def record_task_memory(self, user_id: str | None, task_id: str, title: str, description: str | None):
        if not self.enabled():
            log.info("Backboard API key not set; skipping memory record.")
            return
        # Placeholder: adapt to Backboard's actual memory/thread API.
        payload = {
            "type": "task",
            "user_id": user_id,
            "task_id": task_id,
            "title": title,
            "description": description,
        }
        try:
            # Example endpoint; replace with official Backboard route.
            url = f"{self.base_url}/memory"
            resp = self.session.post(url, json=payload, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            log.warning(f"Backboard memory record failed: {e}")


backboard = BackboardClient()
