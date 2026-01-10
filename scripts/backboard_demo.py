import os
import asyncio
from app.backboard_sdk_client import demo_story, demo_document, demo_memory

if __name__ == "__main__":
    mode = os.getenv("BB_DEMO", "story")
    if mode == "story":
        asyncio.run(demo_story())
    elif mode == "document":
        path = os.getenv("BB_DOC_PATH", "my_document.pdf")
        asyncio.run(demo_document(path))
    elif mode == "memory":
        asyncio.run(demo_memory())
    else:
        print("Unknown BB_DEMO choice. Use 'story', 'document', or 'memory'.")
