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

    def get_or_create_thread(self, user_id: str) -> str | None:
        if not self.enabled():
            return None
        try:
            # Placeholder: query for existing thread named "My Life Plan" for this user
            url = f"{self.base_url}/threads"
            resp = self.session.get(url, params={"user_id": user_id, "name": "My Life Plan"}, timeout=10)
            if resp.ok and resp.json().get("thread_id"):
                return resp.json()["thread_id"]
            # Otherwise create
            payload = {"user_id": user_id, "name": "My Life Plan"}
            resp = self.session.post(url, json=payload, timeout=10)
            if resp.ok:
                return resp.json().get("thread_id")
        except Exception as e:
            log.warning(f"Backboard thread get/create failed: {e}")
        return None

    def retrieve_memory(self, thread_id: str, query: str) -> str:
        if not self.enabled():
            return ""
        try:
            url = f"{self.base_url}/memory/search"
            resp = self.session.post(url, json={"thread_id": thread_id, "query": query}, timeout=10)
            if resp.ok:
                items = resp.json().get("items", [])
                return "\n".join(i.get("text", "") for i in items)
        except Exception as e:
            log.warning(f"Backboard memory retrieval failed: {e}")
        return ""


backboard = BackboardClient()
