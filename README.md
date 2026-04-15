# Flashcard Engine 🧠

> Built for the **Cuemath Build Challenge — Problem 1: The Flashcard Engine**

AI-powered flashcard app that turns any PDF into a smart, practice-ready study deck with spaced repetition.

## 🌐 Live Demo

| | URL |
|---|---|
| **Frontend** | https://flashcard-engine-beta.vercel.app |
| **Backend API** | https://flashcard-engine-api-ceza.onrender.com |
| **Health Check** | https://flashcard-engine-api-ceza.onrender.com/health |

---

## ✨ Features

### 1. Ingestion Quality
Upload any PDF — lecture notes, textbooks, research papers. The AI (Groq + Llama 3.3 70B) reads deeply and generates cards covering:
- Key definitions
- Conceptual relationships
- Edge cases
- Worked examples

Cards feel like they were written by a great teacher, not blindly scraped by a bot.

### 2. Spaced Repetition (SM-2 Algorithm)
Every card is scheduled individually using the SM-2 algorithm:
- Rate each card: **Again / Hard / Good / Easy**
- Cards you struggle with come back sooner
- Cards you know well fade into the background
- Leitner box system (Box 1–5) visualizes your progress

### 3. Progress Tracking
- Mastery percentage per deck
- Leitner box distribution across all cards
- Cards mastered vs shaky vs struggling
- Per-deck mastery breakdown

### 4. Deck Management
- Upload multiple PDFs, each becomes its own deck
- Search and filter decks
- See due card count and last studied time
- Delete decks you no longer need

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite → Vercel |
| Backend | Python FastAPI → Render |
| AI | Groq API (Llama 3.3 70B) |
| Database | SQLite (local) / PostgreSQL (production) |
| PDF Parsing | pdfplumber |
| Spaced Repetition | SM-2 Algorithm |

---

## 🏗 Architecture

```
flashcard-engine/
├── backend/                  ← FastAPI (Python) → Render
│   ├── main.py               # All API routes
│   ├── sm2.py                # SM-2 spaced repetition algorithm
│   ├── pdf_parser.py         # PDF text extraction & chunking
│   ├── card_generator.py     # Groq AI card generation
│   ├── database.py           # SQLAlchemy async models
│   ├── config.py             # Environment settings
│   └── requirements.txt
└── frontend/                 ← React + Vite → Vercel
    └── src/
        ├── pages/
        │   ├── UploadPage.jsx
        │   ├── DecksPage.jsx
        │   ├── StudyPage.jsx
        │   └── ProgressPage.jsx
        └── api/
            └── client.js
```

---

## 🚀 API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/decks/upload` | Upload PDF, generate cards |
| GET | `/decks` | List all decks with mastery stats |
| GET | `/decks/:id` | Single deck detail |
| DELETE | `/decks/:id` | Delete deck and all its cards |
| GET | `/decks/:id/cards/due` | Get due cards for study session |
| PATCH | `/cards/:id/review` | Submit rating (again/hard/good/easy) |
| GET | `/progress/summary` | Global progress stats |

---

## 💻 Local Development

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate.bat        # Windows
# source venv/bin/activate       # Mac/Linux

pip install -r requirements.txt
pip install aiosqlite openai

cp .env.example .env
# Fill in your .env:
# GROK_API_KEY=gsk_your_groq_key_here
# DATABASE_URL=sqlite+aiosqlite:///./flashcards.db
# ALLOWED_ORIGINS=http://localhost:5173

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

# Create .env file:
# VITE_API_URL=http://localhost:8000

npm run dev
# Open http://localhost:5173
```

---

## 🌍 Deployment

### Backend → Render (Free)

1. Push repo to GitHub
2. Go to https://render.com → New Web Service
3. Connect GitHub repo
4. Settings:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `GROK_API_KEY` = your Groq API key
   - `DATABASE_URL` = your database URL
   - `ALLOWED_ORIGINS` = your Vercel frontend URL

### Frontend → Vercel (Free)

```bash
cd frontend
npm install -g vercel
vercel
vercel env add VITE_API_URL   # set to your Render URL
vercel --prod
```

---

## 🔐 Security

- AI API keys are stored only as server-side environment variables
- Keys are never exposed to the browser or frontend code
- All AI calls are made from the backend only
- CORS configured to allow only the frontend origin

---

