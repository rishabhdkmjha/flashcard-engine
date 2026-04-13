from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import settings

engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Deck(Base):
    __tablename__ = "decks"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    filename = Column(String, nullable=False)
    card_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_studied_at = Column(DateTime, nullable=True)

    cards = relationship("Card", back_populates="deck", cascade="all, delete-orphan")


class Card(Base):
    __tablename__ = "cards"

    id = Column(String, primary_key=True)
    deck_id = Column(String, ForeignKey("decks.id"), nullable=False)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    card_type = Column(String, default="definition")

    interval = Column(Integer, default=1)
    repetitions = Column(Integer, default=0)
    ease_factor = Column(Float, default=2.5)
    next_review = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_reviewed_at = Column(DateTime, nullable=True)
    leitner_box = Column(Integer, default=1)
    is_mastered = Column(Boolean, default=False)

    deck = relationship("Deck", back_populates="cards")


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(String, primary_key=True)
    deck_id = Column(String, ForeignKey("decks.id"), nullable=False)
    cards_studied = Column(Integer, default=0)
    cards_correct = Column(Integer, default=0)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime, nullable=True)


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
