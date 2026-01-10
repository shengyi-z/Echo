from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import chat  # 暂时只导入 chat

app = FastAPI(title="Echo API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat.router)

# 暂时注释掉其他路由，等实现后再添加
# app.include_router(goals.router)
# app.include_router(tasks.router)
# app.include_router(plans.router)
# app.include_router(reminders.router)

@app.get("/")
def read_root():
    return {"message": "Echo API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)