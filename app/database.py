import os
from contextlib import contextmanager
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
from app.models import Article, UserEvent  # ✅ import models to register metadata

load_dotenv()
DB_URL = os.getenv("DB_URL", "sqlite:///./news.db")

connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, echo=False, connect_args=connect_args)


def init_db():
    """Create tables if not exist"""
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    """Context-managed DB session"""
    with Session(engine) as session:
        yield session


if __name__ == "__main__":
    print("🧱 Initializing database...")
    init_db()
    print("✅ Database initialized.")
