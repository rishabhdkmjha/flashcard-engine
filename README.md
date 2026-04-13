# Flashcard Engine

AI-powered flashcard app built for the Cuemath Build Challenge. Upload any PDF and get a smart, practice-ready deck with spaced repetition.

## Stack

- **Frontend:** React + Vite → deployed on Vercel
- **Backend:** Python FastAPI → deployed on Railway
- **Database:** PostgreSQL via Supabase
- **AI:** Anthropic Claude API (server-side only)
- **Spaced Repetition:** SM-2 algorithm

---

## Local Development

### 1. Clone and set up backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
```

### 2. Set up database (Supabase)

1. Create a free project at https://supabase.com
2. Copy the **Connection string** (URI format) from Settings → Database
3. Paste it as `DATABASE_URL` in `backend/.env`
   - Make sure the URL starts with `postgresql+asyncpg://`

### 3. Run backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Tables are created automatically on first startup.

### 4. Set up frontend

```bash
cd frontend
npm install
cp .env.example .env
# VITE_API_URL=http://localhost:8000
npm run dev
```

Open http://localhost:5173

---

## Deployment

### Backend → Railway

1. Push repo to GitHub
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Select the `backend/` folder as root
4. Set environment variables in Railway dashboard:
   - `ANTHROPIC_API_KEY`
   - `DATABASE_URL`
   - `ALLOWED_ORIGINS` (your Vercel URL, e.g. `https://your-app.vercel.app`)
5. Railway auto-deploys. Note your Railway URL.

### Frontend → Vercel

```bash
cd frontend
npm install -g vercel
vercel
```

When prompted, set:
- `VITE_API_URL` = your Railway backend URL (e.g. `https://flashcard-api.railway.app`)

Redeploy after setting env vars:
```bash
vercel --prod
```

---

## Project Structure

```
flashcard-engine/
├── backend/
│   ├── main.py           # FastAPI routes
│   ├── sm2.py            # Spaced repetition algorithm
│   ├── pdf_parser.py     # PDF text extraction
│   ├── card_generator.py # Anthropic API card generation
│   ├── database.py       # SQLAlchemy models + async engine
│   ├── config.py         # Pydantic settings
│   ├── requirements.txt
│   └── railway.toml      # Railway deploy config
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── pages/
    │   │   ├── UploadPage.jsx
    │   │   ├── DecksPage.jsx
    │   │   ├── StudyPage.jsx
    │   │   └── ProgressPage.jsx
    │   └── api/
    │       └── client.js
    ├── index.html
    └── vite.config.js
```

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| POST | `/decks/upload` | Upload PDF, generate cards |
| GET | `/decks` | List all decks with mastery stats |
| GET | `/decks/:id` | Single deck detail |
| DELETE | `/decks/:id` | Delete deck and cards |
| GET | `/decks/:id/cards/due` | Due cards for study session |
| PATCH | `/cards/:id/review` | Submit rating (again/hard/good/easy) |
| GET | `/progress/summary` | Global progress stats |
