import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { fetchDecks, deleteDeck } from '../api/client'
import styles from './DecksPage.module.css'

const SUBJECT_COLORS = {
  Biology: '#1D9E75',
  Mathematics: '#534AB7',
  History: '#993C1D',
  Chemistry: '#185FA5',
  Physics: '#185FA5',
  Economics: '#3B6D11',
  General: '#888780',
}

function subjectColor(subject) {
  return SUBJECT_COLORS[subject] || '#888780'
}

export default function DecksPage() {
  const [decks, setDecks] = useState([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    loadDecks()
  }, [location.state])

  async function loadDecks() {
    try {
      const data = await fetchDecks()
      setDecks(data)
    } catch (err) {
      setError('Could not load decks.')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(e, deckId) {
    e.stopPropagation()
    if (!confirm('Delete this deck and all its cards?')) return
    try {
      await deleteDeck(deckId)
      setDecks((prev) => prev.filter((d) => d.id !== deckId))
    } catch {
      alert('Failed to delete deck.')
    }
  }

  const filtered = decks.filter(
    (d) =>
      d.title.toLowerCase().includes(query.toLowerCase()) ||
      (d.subject || '').toLowerCase().includes(query.toLowerCase())
  )

  return (
    <div>
      <div className={styles.header}>
        <h1 className={styles.heading}>My Decks</h1>
        <div className={styles.searchBar}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="Search decks…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
      </div>

      {error && <p className={styles.error}>{error}</p>}

      {loading ? (
        <div className={styles.loadingGrid}>
          {[1, 2, 3].map((i) => <div key={i} className={styles.skeleton} />)}
        </div>
      ) : (
        <div className={styles.grid}>
          {filtered.map((deck) => (
            <div key={deck.id} className={styles.card} onClick={() => navigate(`/decks/${deck.id}/study`)}>
              <div className={styles.cardTop}>
                <span className={styles.subject} style={{ color: subjectColor(deck.subject) }}>
                  {deck.subject || 'General'}
                </span>
                <button className={styles.deleteBtn} onClick={(e) => handleDelete(e, deck.id)} title="Delete deck">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6l-1 14H6L5 6" />
                    <path d="M10 11v6M14 11v6" />
                  </svg>
                </button>
              </div>
              <h3 className={styles.cardTitle}>{deck.title}</h3>
              <p className={styles.meta}>{deck.card_count} cards · {deck.last_studied_at ? `Last studied ${formatRelative(deck.last_studied_at)}` : 'Not started'}</p>
              <div className={styles.masteryBar}>
                <div className={styles.masteryFill} style={{ width: `${deck.mastery_percent}%` }} />
              </div>
              <div className={styles.masteryRow}>
                <span>{deck.mastery_percent}% mastered</span>
                <span className={deck.due_count > 0 ? styles.badgeAmber : styles.badgeTeal}>
                  {deck.due_count > 0 ? `Due: ${deck.due_count}` : 'Up to date'}
                </span>
              </div>
            </div>
          ))}

          <div className={`${styles.card} ${styles.newCard}`} onClick={() => navigate('/')}>
            <span className={styles.plus}>+</span>
            <span className={styles.newLabel}>Upload new PDF</span>
          </div>
        </div>
      )}

      {!loading && filtered.length === 0 && query && (
        <p className={styles.empty}>No decks match "{query}"</p>
      )}
    </div>
  )
}

function formatRelative(iso) {
  const date = new Date(iso)
  const diff = Date.now() - date.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}
