import json
import uuid
import time
from openai import OpenAI, RateLimitError
from config import settings
from pdf_parser import ContentChunk

# Initialize Groq client using the OpenAI SDK format
client = OpenAI(
    api_key=settings.grok_api_key, # Ensure this matches your config.py/env
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


def call_groq_with_retry(messages: list, retries: int = 3, wait: int = 10) -> str:
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                # Force JSON output for better reliability with Groq
                response_format={"type": "json_object"} 
            )
            return response.choices[0].message.content.strip()
        except RateLimitError:
            if attempt < retries - 1:
                print(f"Rate limited, waiting {wait}s before retry {attempt + 2}/{retries}")
                time.sleep(wait)
            else:
                raise
        except Exception as e:
            print(f"Groq error: {e}")
            raise


def parse_json_response(raw: str) -> dict:
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


async def generate_cards_for_chunk(chunk: ContentChunk) -> list[dict]:
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Generate flashcards from this content:\n\n{chunk.text}"},
        ]
        raw = call_groq_with_retry(messages)
        parsed = parse_json_response(raw)
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
        print(f"Card generation error on chunk: {e}")
        return []


async def generate_all_cards(chunks: list[ContentChunk]) -> list[dict]:
    all_cards = []
    for i, chunk in enumerate(chunks):
        cards = await generate_cards_for_chunk(chunk)
        all_cards.extend(cards)
        if i < len(chunks) - 1:
            time.sleep(2) # Prevent hitting Groq rate limits
    return all_cards


async def infer_deck_metadata(first_chunk: ContentChunk) -> dict:
    try:
        messages = [
            {"role": "system", "content": TITLE_PROMPT},
            {"role": "user", "content": first_chunk.text[:800]},
        ]
        raw = call_groq_with_retry(messages)
        data = parse_json_response(raw)
        return {
            "title": data.get("title", "Untitled Deck"),
            "subject": data.get("subject", "General"),
        }
    except Exception as e:
        print(f"Metadata error: {e}")
        return {"title": "Untitled Deck", "subject": "General"}
