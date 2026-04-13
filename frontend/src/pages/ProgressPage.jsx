import { useState, useEffect } from 'react'
import { fetchProgressSummary, fetchDecks } from '../api/client'
import styles from './ProgressPage.module.css'

const LEITNER_CONFIG = [
  { box: 1, label: 'Box 1', sub: 'Daily review', colorClass: 'b1' },
  { box: 2, label: 'Box 2', sub: 'Every 2 days', colorClass: 'b2' },
  { box: 3, label: 'Box 3', sub: 'Every 4 days', colorClass: 'b3' },
  { box: 4, label: 'Box 4', sub: 'Weekly', colorClass: 'b4' },
  { box: 5, label: 'Box 5', sub: 'Mastered', colorClass: 'b5' },
]

export default function ProgressPage() {
  const [summary, setSummary] = useState(null)
  const [decks, setDecks] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([fetchProgressSummary(), fetchDecks()])
      .then(([s, d]) => { setSummary(s); setDecks(d) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className={styles.loading}><div className={styles.spinner} /></div>

  const leitnerDist = summary?.leitner_distribution || {}
  const topDecks = [...decks].sort((a, b) => b.mastery_percent - a.mastery_percent)

  return (
    <div>
      <div className={styles.header}>
        <h1 className={styles.heading}>Your progress</h1>
        <span className={styles.meta}>All decks · all time</span>
      </div>

      <div className={styles.metricGrid}>
        <div className={`${styles.metric} ${styles.mTeal}`}>
          <div className={styles.metricNum}>{summary?.mastered ?? 0}</div>
          <div className={styles.metricLbl}>Cards mastered</div>
        </div>
        <div className={`${styles.metric} ${styles.mAmber}`}>
          <div className={styles.metricNum}>{summary?.shaky ?? 0}</div>
          <div className={styles.metricLbl}>Shaky — needs work</div>
        </div>
        <div className={`${styles.metric} ${styles.mRed}`}>
          <div className={styles.metricNum}>{summary?.struggling ?? 0}</div>
          <div className={styles.metricLbl}>Struggling</div>
        </div>
        <div className={`${styles.metric} ${styles.mPurple}`}>
          <div className={styles.metricNum}>{summary?.total_cards ?? 0}</div>
          <div className={styles.metricLbl}>Total cards</div>
        </div>
      </div>

      <div className={styles.sectionLabel}>Leitner boxes</div>
      <div className={styles.leitnerRow}>
        {LEITNER_CONFIG.map(({ box, label, sub, colorClass }) => (
          <div key={box} className={`${styles.lbox} ${styles[colorClass]}`}>
            <div className={styles.lboxNum}>{leitnerDist[box] ?? 0}</div>
            <div className={styles.lboxLabel}>{label}</div>
            <div className={styles.lboxSub}>{sub}</div>
          </div>
        ))}
      </div>

      <div className={styles.sectionLabel}>Mastery by deck</div>
      {decks.length === 0 ? (
        <p className={styles.empty}>No decks yet. Upload a PDF to get started.</p>
      ) : (
        <div className={styles.breakdown}>
          {topDecks.map((deck) => (
            <div key={deck.id} className={styles.breakRow}>
              <span className={styles.breakName} title={deck.title}>{deck.title}</span>
              <div className={styles.breakBarBg}>
                <div className={styles.breakBarFill} style={{ width: `${deck.mastery_percent}%` }} />
              </div>
              <span className={styles.breakPct}>{deck.mastery_percent}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
