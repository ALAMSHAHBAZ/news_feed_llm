from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes import news_router

app = FastAPI(title="Contextual News Retrieval System", version="1.0")
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(news_router.router)

@app.get("/health")
def health():
    return {"status": "ok"}
