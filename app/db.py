import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Use sync sqlite by default to avoid requiring aiosqlite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./offset.db")

# For sqlite we need check_same_thread=False when using the same connection across threads
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
