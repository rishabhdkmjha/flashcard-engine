import json
import uuid
from openai import OpenAI
from config import settings
from pdf_parser import ContentChunk

client = OpenAI(
    api_key=settings.grok_api_key,
    base_url="https://api.groq.com/openai/v1",
)

SYSTEM_PROMPT = """You are an expert educator and flashcard author. Given educational content, generate high-quality flashcards that a great teacher would write.

Each card must:
- Have a focused, specific question on the front
- Have a complete, accurate answer on the back (2-4 sentences)
- Cover one of these types: definition, concept, relationship, example, edge_case, formula
- Avoid vague or overly broad questions
- Cover key concepts, definitions, relationships, edge cases, and worked examples

Return ONLY valid JSON with no markdown, no preamble:
{
  "cards": [
    {
      "front": "question text",
      "back": "answer text",
      "card_type": "definition"
    }
  ]
}

Generate between 3 and 8 cards per chunk depending on content richness."""

TITLE_PROMPT = """Given the first chunk of a PDF document, extract:
1. A short descriptive deck title (max 8 words)
2. The subject area (e.g. Biology, Mathematics, History, Physics)

Return ONLY valid JSON with no markdown:
{"title": "...", "subject": "..."}"""


async def generate_cards_for_chunk(chunk: ContentChunk) -> list[dict]:
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate flashcards from this content:\n\n{chunk.text}"},
            ],
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        parsed = json.loads(raw)
        cards = parsed.get("cards", [])
        return [
            {
                "id": str(uuid.uuid4()),
                "front": card["front"],
                "back": card["back"],
                "card_type": card.get("card_type", "concept"),
            }
            for card in cards
            if card.get("front") and card.get("back")
        ]
    except Exception as e:
        print(f"Card generation error: {e}")
        return []


async def generate_all_cards(chunks: list[ContentChunk]) -> list[dict]:
    all_cards = []
    for chunk in chunks:
        cards = await generate_cards_for_chunk(chunk)
        all_cards.extend(cards)
    return all_cards


async def infer_deck_metadata(first_chunk: ContentChunk) -> dict:
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": TITLE_PROMPT},
                {"role": "user", "content": first_chunk.text[:800]},
            ],
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        data = json.loads(raw)
        return {
            "title": data.get("title", "Untitled Deck"),
            "subject": data.get("subject", "General"),
        }
    except Exception as e:
        print(f"Metadata error: {e}")
        return {"title": "Untitled Deck", "subject": "General"}
