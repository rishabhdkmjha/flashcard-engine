import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchDeck, fetchDueCards, reviewCard } from '../api/client'
import styles from './StudyPage.module.css'

const RATINGS = [
  { key: 'again', label: 'Again', className: 'again' },
  { key: 'hard', label: 'Hard', className: 'hard' },
  { key: 'good', label: 'Good', className: 'good' },
  { key: 'easy', label: 'Easy', className: 'easy' },
]

const LEITNER_LABELS = { 1: 'Daily', 2: 'Every 2d', 3: 'Every 4d', 4: 'Weekly', 5: 'Mastered' }

export default function StudyPage() {
  const { deckId } = useParams()
  const navigate = useNavigate()

  const [deck, setDeck] = useState(null)
  const [cards, setCards] = useState([])
  const [cardIndex, setCardIndex] = useState(0)
  const [revealed, setRevealed] = useState(false)
  const [session, setSession] = useState({ correct: 0, hard: 0, again: 0 })
  const [loading, setLoading] = useState(true)
  const [done, setDone] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadSession()
  }, [deckId])

  async function loadSession() {
    try {
      const [deckData, dueCards] = await Promise.all([
        fetchDeck(deckId),
        fetchDueCards(deckId, 20),
      ])
      setDeck(deckData)
      setCards(dueCards)
      if (dueCards.length === 0) setDone(true)
    } finally {
      setLoading(false)
    }
  }

  async function handleRating(rating) {
    if (submitting) return
    setSubmitting(true)

    const currentCard = cards[cardIndex]
    try {
      await reviewCard(currentCard.id, rating)
    } catch {
    }

    setSession((prev) => ({
      correct: rating === 'good' || rating === 'easy' ? prev.correct + 1 : prev.correct,
      hard: rating === 'hard' ? prev.hard + 1 : prev.hard,
      again: rating === 'again' ? prev.again + 1 : prev.again,
    }))

    const next = cardIndex + 1
    if (next >= cards.length) {
      setDone(true)
    } else {
      setCardIndex(next)
      setRevealed(false)
    }
    setSubmitting(false)
  }

  if (loading) return <div className={styles.centered}><div className={styles.spinner} /></div>

  if (done) {
    return (
      <div className={styles.donePage}>
        <div className={styles.doneCard}>
          <div className={styles.doneIcon}>✓</div>
          <h2 className={styles.doneTitle}>Session complete</h2>
          <p className={styles.doneSub}>{deck?.title}</p>
          <div className={styles.sessionStats}>
            <div className={`${styles.stat} ${styles.statGreen}`}><span className={styles.statNum}>{session.correct}</span><span className={styles.statLbl}>Correct</span></div>
            <div className={`${styles.stat} ${styles.statAmber}`}><span className={styles.statNum}>{session.hard}</span><span className={styles.statLbl}>Hard</span></div>
            <div className={`${styles.stat} ${styles.statRed}`}><span className={styles.statNum}>{session.again}</span><span className={styles.statLbl}>Again</span></div>
          </div>
          <div className={styles.doneActions}>
            <button className={styles.primaryBtn} onClick={() => { setDone(false); setLoading(true); loadSession() }}>Study again</button>
            <button className={styles.ghostBtn} onClick={() => navigate('/decks')}>Back to decks</button>
          </div>
        </div>
      </div>
    )
  }

  const current = cards[cardIndex]

  return (
    <div>
      <div className={styles.breadcrumb}>
        <span className={styles.backLink} onClick={() => navigate('/decks')}>← My Decks</span>
        <span className={styles.sep}>/</span>
        <span>{deck?.title}</span>
      </div>

      <div className={styles.layout}>
        <aside className={styles.sidebar}>
          <h3 className={styles.sideLabel}>Session</h3>
          <div className={styles.statRow}>
            <div className={`${styles.stat} ${styles.statGreen}`}><span className={styles.statNum}>{session.correct}</span><span className={styles.statLbl}>Correct</span></div>
            <div className={`${styles.stat} ${styles.statAmber}`}><span className={styles.statNum}>{session.hard}</span><span className={styles.statLbl}>Hard</span></div>
            <div className={`${styles.stat} ${styles.statRed}`}><span className={styles.statNum}>{session.again}</span><span className={styles.statLbl}>Again</span></div>
          </div>
          <h3 className={styles.sideLabel}>Queue</h3>
          <div className={styles.queue}>
            {cards.slice(cardIndex, cardIndex + 5).map((c, i) => (
              <div key={c.id} className={`${styles.queueItem} ${i === 0 ? styles.queueCurrent : ''}`}>
                <span className={styles.queueDot} style={{ background: leitnerColor(c.leitner_box) }} />
                <span className={styles.queueFront}>{c.front.substring(0, 40)}{c.front.length > 40 ? '…' : ''}</span>
              </div>
            ))}
          </div>
        </aside>

        <div className={styles.main}>
          <div className={styles.progress}>Card {cardIndex + 1} of {cards.length} due today</div>

          <div
            className={`${styles.flashcard} ${revealed ? styles.revealed : ''}`}
            onClick={() => !revealed && setRevealed(true)}
          >
            <div className={styles.cardTag}>
              <span className={styles.typeBadge}>{current.card_type}</span>
              <span className={styles.leitnerBadge}>Box {current.leitner_box} · {LEITNER_LABELS[current.leitner_box]}</span>
            </div>
            <span className={styles.faceLabel}>{revealed ? 'Answer' : 'Question'}</span>
            <p className={styles.cardFront}>{current.front}</p>
            {revealed ? (
              <>
                <div className={styles.divider} />
                <p className={styles.cardBack}>{current.back}</p>
              </>
            ) : (
              <span className={styles.hint}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
                Tap to reveal answer
              </span>
            )}
          </div>

          {revealed && (
            <div className={styles.ratingRow}>
              {RATINGS.map((r) => (
                <button
                  key={r.key}
                  className={`${styles.ratingBtn} ${styles[r.className]}`}
                  onClick={() => handleRating(r.key)}
                  disabled={submitting}
                >
                  {r.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function leitnerColor(box) {
  const colors = { 1: '#E24B4A', 2: '#BA7517', 3: '#378ADD', 4: '#1D9E75', 5: '#534AB7' }
  return colors[box] || '#888780'
}
