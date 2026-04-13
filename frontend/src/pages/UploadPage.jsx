import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadPDF } from '../api/client'
import styles from './UploadPage.module.css'

const FEATURES = [
  { label: 'Ingestion quality', desc: 'Definitions, relationships, edge cases, worked examples — extracted with teacher-level care.' },
  { label: 'Spaced repetition', desc: 'SM-2 algorithm schedules each card individually. Struggle? It comes back sooner.' },
  { label: 'Deck management', desc: 'Search, filter, and resume any deck. Dozens of topics organized automatically.' },
]

export default function UploadPage() {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [stage, setStage] = useState('')
  const [error, setError] = useState('')
  const inputRef = useRef()
  const navigate = useNavigate()

  const handleFile = async (file) => {
    if (!file || !file.name.endsWith('.pdf')) {
      setError('Please upload a PDF file.')
      return
    }
    setError('')
    setUploading(true)
    setStage('Uploading PDF...')
    setProgress(0)

    try {
      const result = await uploadPDF(file, (pct) => {
        setProgress(pct)
        if (pct === 100) setStage('AI is reading and generating cards...')
      })
      navigate('/decks', { state: { newDeckId: result.deck_id } })
    } catch (err) {
      setError(err.message || 'Upload failed. Please try again.')
      setUploading(false)
      setStage('')
    }
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    handleFile(file)
  }

  return (
    <div className={styles.page}>
      <div className={styles.hero}>
        <h1 className={styles.title}>Turn any PDF into<br />a smart study deck</h1>
        <p className={styles.subtitle}>Upload lecture notes, textbooks, or papers. The AI reads deeply and generates cards that actually teach — not just copy.</p>
      </div>

      <div
        className={`${styles.dropZone} ${dragging ? styles.dragging : ''} ${uploading ? styles.disabled : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !uploading && inputRef.current.click()}
      >
        <input ref={inputRef} type="file" accept=".pdf" style={{ display: 'none' }} onChange={(e) => handleFile(e.target.files[0])} />

        {uploading ? (
          <div className={styles.uploadingState}>
            <div className={styles.spinner} />
            <p className={styles.stageText}>{stage}</p>
            <div className={styles.progressBar}>
              <div className={styles.progressFill} style={{ width: `${progress}%` }} />
            </div>
            <p className={styles.progressPct}>{progress}%</p>
          </div>
        ) : (
          <>
            <div className={styles.dropIcon}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <h3 className={styles.dropTitle}>Drop your PDF here</h3>
            <p className={styles.dropSub}>or click to browse — any textbook, notes, or paper</p>
            <button className={styles.chooseBtn} onClick={(e) => { e.stopPropagation(); inputRef.current.click() }}>Choose PDF</button>
          </>
        )}
      </div>

      {error && <p className={styles.error}>{error}</p>}

      <div className={styles.features}>
        {FEATURES.map((f) => (
          <div key={f.label} className={styles.featCard}>
            <div className={styles.featLabel}>{f.label}</div>
            <p>{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
