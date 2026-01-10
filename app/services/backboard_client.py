import os
import logging
import requests
from app.core.config import settings

log = logging.getLogger(__name__)


class BackboardClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.BACKBOARD_API_KEY
        self.base_url = (base_url or settings.BACKBOARD_BASE_URL).rstrip("/")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"X-API-Key": self.api_key})
        
        self._assistant_id = None
        self._user_threads = {}  # user_id -> thread_id mapping

    def enabled(self) -> bool:
        return bool(self.api_key)
    
    def get_or_create_assistant(self) -> str | None:
        """Get or create the Echo assistant."""
        if not self.enabled():
            return None
        
        if self._assistant_id:
            return self._assistant_id
            
        try:
            # Try to find existing assistant
            resp = self.session.get(f"{self.base_url}/assistants", timeout=10)
            if resp.ok:
                assistants = resp.json()
                for asst in assistants:
                    if asst.get("name") == "Echo Assistant":
                        self._assistant_id = asst["assistant_id"]
                        log.info(f"Found existing assistant: {self._assistant_id}")
                        return self._assistant_id
            
            # Create new assistant
            payload = {
                "name": "Echo Assistant",
                "description": "Personal task and reminder assistant with memory"
            }
            resp = self.session.post(f"{self.base_url}/assistants", json=payload, timeout=10)
            resp.raise_for_status()
            self._assistant_id = resp.json()["assistant_id"]
            log.info(f"Created new assistant: {self._assistant_id}")
            return self._assistant_id
        except Exception as e:
            log.warning(f"Failed to get/create assistant: {e}")
            return None
    
    def get_or_create_thread(self, user_id: str) -> str | None:
        """Get or create a thread for the user."""
        if not self.enabled():
            return None
        
        # Check cache
        if user_id in self._user_threads:
            return self._user_threads[user_id]
        
        assistant_id = self.get_or_create_assistant()
        if not assistant_id:
            return None
            
        try:
            # Create new thread for this user
            resp = self.session.post(
                f"{self.base_url}/assistants/{assistant_id}/threads",
                json={},
                timeout=10
            )
            resp.raise_for_status()
            thread_id = resp.json()["thread_id"]
            self._user_threads[user_id] = thread_id
            log.info(f"Created thread {thread_id} for user {user_id}")
            return thread_id
        except Exception as e:
            log.warning(f"Failed to create thread: {e}")
            return None

    def record_task_memory(self, user_id: str | None, task_id: str, title: str, description: str | None):
        """Record task as a memory in Backboard."""
        if not self.enabled() or not user_id:
            log.info("Backboard disabled or no user_id; skipping memory record.")
            return
        
        thread_id = self.get_or_create_thread(user_id)
        if not thread_id:
            return
            
        try:
            content = f"Task created: {title}"
            if description:
                content += f"\nDescription: {description}"
            
            data = {
                "content": content,
                "memory": "Auto",
                "send_to_llm": "false",
                "metadata": f'{{"task_id": "{task_id}", "type": "task"}}'
            }
            
            resp = self.session.post(
                f"{self.base_url}/threads/{thread_id}/messages",
                data=data,
                timeout=10
            )
            resp.raise_for_status()
            log.info(f"Recorded task memory for {task_id}")
        except Exception as e:
            log.warning(f"Failed to record task memory: {e}")


backboard = BackboardClient()
