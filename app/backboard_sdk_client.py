import os
import asyncio
from typing import AsyncIterator, Optional

try:
    from backboard import BackboardClient as BBClient
except Exception:
    BBClient = None  # Will raise at runtime if used without install

from app.config import settings


class BackboardSDK:
    """Async wrapper around backboard-sdk for assistant/threads/messages.
    Reads API key from env via app.config.Settings.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.BACKBOARD_API_KEY
        if not self.api_key:
            raise RuntimeError(
                "BACKBOARD_API_KEY not set. Configure in .env or environment.")
        if BBClient is None:
            raise RuntimeError(
                "backboard-sdk not installed. Run: pip install backboard-sdk")
        self.client = BBClient(api_key=self.api_key)

    async def create_assistant(self, name: str, description: str | None = None, tools: list | None = None):
        return await self.client.create_assistant(name=name, description=description, tools=tools)

    async def create_thread(self, assistant_id: str):
        return await self.client.create_thread(assistant_id)

    async def stream_message(self, thread_id: str, content: str, llm_provider: str = "openai", model_name: str = "gpt-4o") -> AsyncIterator[str]:
        async for chunk in await self.client.add_message(
            thread_id=thread_id,
            content=content,
            llm_provider=llm_provider,
            model_name=model_name,
            stream=True,
        ):
            if chunk.get("type") == "content_streaming":
                yield chunk.get("content", "")
            elif chunk.get("type") == "message_complete":
                break

    async def add_message(self, thread_id: str, content: str, memory: str | None = None, stream: bool = False):
        return await self.client.add_message(thread_id=thread_id, content=content, memory=memory, stream=stream)

    async def upload_document_to_assistant(self, assistant_id: str, file_path: str):
        return await self.client.upload_document_to_assistant(assistant_id, file_path)

    async def get_document_status(self, document_id: str):
        return await self.client.get_document_status(document_id)


async def demo_story():
    sdk = BackboardSDK()
    assistant = await sdk.create_assistant(name="Echo Assistant", description="A helpful assistant")
    thread = await sdk.create_thread(assistant.assistant_id)

    async for text in sdk.stream_message(
        thread_id=thread.thread_id,
        content="Tell me a short story about a robot learning to paint.",
        llm_provider="openai",
        model_name="gpt-4o",
    ):
        print(text, end="", flush=True)


async def demo_document(file_path: str):
    sdk = BackboardSDK()
    assistant = await sdk.create_assistant(name="Document Assistant", description="Analyzes documents")
    doc = await sdk.upload_document_to_assistant(assistant.assistant_id, file_path)

    print("Waiting for document to be indexed...")
    while True:
        status = await sdk.get_document_status(doc.document_id)
        if status.status == "indexed":
            print("Document indexed successfully!")
            break
        if status.status == "failed":
            raise RuntimeError(f"Indexing failed: {status.status_message}")
        await asyncio.sleep(2)

    thread = await sdk.create_thread(assistant.assistant_id)
    response = await sdk.add_message(thread.thread_id, "What are the key points in the uploaded document?", stream=False)
    print(response.content)


async def demo_memory():
    sdk = BackboardSDK()
    assistant = await sdk.create_assistant(name="Memory Assistant", description="Assistant with persistent memory")

    thread1 = await sdk.create_thread(assistant.assistant_id)
    resp1 = await sdk.add_message(
        thread_id=thread1.thread_id,
        content="My name is Sarah and I work as a software engineer at Google.",
        memory="Auto",
        stream=False,
    )
    print(f"AI: {resp1.content}")

    thread2 = await sdk.create_thread(assistant.assistant_id)
    resp3 = await sdk.add_message(
        thread_id=thread2.thread_id,
        content="What do you remember about me?",
        memory="Auto",
        stream=False,
    )
    print(f"AI: {resp3.content}")


if __name__ == "__main__":
    # Quick manual test runner
    choice = os.getenv("BB_DEMO", "story")
    if choice == "story":
        asyncio.run(demo_story())
    elif choice == "document":
        path = os.getenv("BB_DOC_PATH", "my_document.pdf")
        asyncio.run(demo_document(path))
    elif choice == "memory":
        asyncio.run(demo_memory())
    else:
        print("Unknown BB_DEMO choice. Use 'story', 'document', or 'memory'.")
