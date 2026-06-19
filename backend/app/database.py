from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

SessionFactory = sessionmaker(engine, class_=Session, expire_on_commit=False)


def get_db():
    with SessionFactory() as session:
        yield session


def init_db():
    SQLModel.metadata.create_all(engine)
