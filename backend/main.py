import uuid
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from config import settings
from database import get_db, create_tables, Deck, Card, StudySession
from pdf_parser import extract_text_chunks
from card_generator import generate_all_cards, infer_deck_metadata
from sm2 import compute_next_state

app = FastAPI(title="Flashcard Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await create_tables()


class ReviewRequest(BaseModel):
    rating: str


class DeckResponse(BaseModel):
    id: str
    title: str
    subject: str | None
    filename: str
    card_count: int
    mastery_percent: float
    due_count: int
    created_at: datetime
    last_studied_at: datetime | None

    class Config:
        from_attributes = True


class CardResponse(BaseModel):
    id: str
    deck_id: str
    front: str
    back: str
    card_type: str
    interval: int
    repetitions: int
    ease_factor: float
    next_review: datetime
    leitner_box: int
    is_mastered: bool

    class Config:
        from_attributes = True


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/decks/upload")
async def upload_pdf(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    chunks = extract_text_chunks(tmp_path)
    tmp_path.unlink(missing_ok=True)

    if not chunks:
        raise HTTPException(status_code=422, detail="Could not extract text from this PDF")

    metadata = await infer_deck_metadata(chunks[0])
    raw_cards = await generate_all_cards(chunks)

    if not raw_cards:
        raise HTTPException(status_code=422, detail="No cards could be generated from this content")

    deck_id = str(uuid.uuid4())
    deck = Deck(
        id=deck_id,
        title=metadata["title"],
        subject=metadata["subject"],
        filename=file.filename,
        card_count=len(raw_cards),
    )
    db.add(deck)

    now = datetime.now(timezone.utc)
    for raw in raw_cards:
        card = Card(
            id=raw["id"],
            deck_id=deck_id,
            front=raw["front"],
            back=raw["back"],
            card_type=raw["card_type"],
            next_review=now,
        )
        db.add(card)

    await db.commit()
    return {"deck_id": deck_id, "title": metadata["title"], "card_count": len(raw_cards)}


@app.get("/decks", response_model=list[DeckResponse])
async def list_decks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Deck).order_by(Deck.created_at.desc()))
    decks = result.scalars().all()

    now = datetime.now(timezone.utc)
    enriched = []
    for deck in decks:
        cards_result = await db.execute(select(Card).where(Card.deck_id == deck.id))
        cards = cards_result.scalars().all()
        total = len(cards)
        mastered = sum(1 for c in cards if c.is_mastered)
        due = sum(1 for c in cards if c.next_review.replace(tzinfo=timezone.utc) <= now)
        enriched.append(DeckResponse(
            id=deck.id,
            title=deck.title,
            subject=deck.subject,
            filename=deck.filename,
            card_count=total,
            mastery_percent=round((mastered / total) * 100, 1) if total else 0.0,
            due_count=due,
            created_at=deck.created_at,
            last_studied_at=deck.last_studied_at,
        ))
    return enriched


@app.get("/decks/{deck_id}", response_model=DeckResponse)
async def get_deck(deck_id: str, db: AsyncSession = Depends(get_db)):
    deck = await db.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    now = datetime.now(timezone.utc)
    cards_result = await db.execute(select(Card).where(Card.deck_id == deck_id))
    cards = cards_result.scalars().all()
    total = len(cards)
    mastered = sum(1 for c in cards if c.is_mastered)
    due = sum(1 for c in cards if c.next_review.replace(tzinfo=timezone.utc) <= now)

    return DeckResponse(
        id=deck.id,
        title=deck.title,
        subject=deck.subject,
        filename=deck.filename,
        card_count=total,
        mastery_percent=round((mastered / total) * 100, 1) if total else 0.0,
        due_count=due,
        created_at=deck.created_at,
        last_studied_at=deck.last_studied_at,
    )


@app.delete("/decks/{deck_id}")
async def delete_deck(deck_id: str, db: AsyncSession = Depends(get_db)):
    deck = await db.get(Deck, deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    await db.delete(deck)
    await db.commit()
    return {"deleted": deck_id}


@app.get("/decks/{deck_id}/cards/due", response_model=list[CardResponse])
async def get_due_cards(deck_id: str, limit: int = 20, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Card)
        .where(Card.deck_id == deck_id)
        .where(Card.next_review <= now)
        .order_by(Card.next_review)
        .limit(limit)
    )
    return result.scalars().all()


@app.patch("/cards/{card_id}/review", response_model=CardResponse)
async def review_card(card_id: str, body: ReviewRequest, db: AsyncSession = Depends(get_db)):
    if body.rating not in ("again", "hard", "good", "easy"):
        raise HTTPException(status_code=400, detail="Rating must be again, hard, good, or easy")

    card = await db.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    new_state = compute_next_state(
        interval=card.interval,
        repetitions=card.repetitions,
        ease_factor=card.ease_factor,
        rating=body.rating,
    )

    card.interval = new_state.interval
    card.repetitions = new_state.repetitions
    card.ease_factor = new_state.ease_factor
    card.next_review = new_state.next_review
    card.leitner_box = new_state.leitner_box
    card.is_mastered = new_state.is_mastered
    card.last_reviewed_at = datetime.now(timezone.utc)

    deck = await db.get(Deck, card.deck_id)
    if deck:
        deck.last_studied_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(card)
    return card


@app.get("/progress/summary")
async def progress_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Card))
    cards = result.scalars().all()

    leitner_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for card in cards:
        leitner_dist[card.leitner_box] = leitner_dist.get(card.leitner_box, 0) + 1

    mastered = sum(1 for c in cards if c.is_mastered)
    struggling = sum(1 for c in cards if c.leitner_box == 1)
    shaky = sum(1 for c in cards if c.leitner_box in (2, 3))

    return {
        "total_cards": len(cards),
        "mastered": mastered,
        "struggling": struggling,
        "shaky": shaky,
        "leitner_distribution": leitner_dist,
    }
