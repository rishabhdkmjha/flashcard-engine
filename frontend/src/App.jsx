import { Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import UploadPage from './pages/UploadPage'
import DecksPage from './pages/DecksPage'
import StudyPage from './pages/StudyPage'
import ProgressPage from './pages/ProgressPage'
import styles from './App.module.css'

export default function App() {
  return (
    <div className={styles.shell}>
      <nav className={styles.nav}>
        <div className={styles.logo}>flash<span>card.</span></div>
        <div className={styles.navLinks}>
          <NavLink to="/" end className={({ isActive }) => isActive ? styles.active : ''}>Upload</NavLink>
          <NavLink to="/decks" className={({ isActive }) => isActive ? styles.active : ''}>My Decks</NavLink>
          <NavLink to="/progress" className={({ isActive }) => isActive ? styles.active : ''}>Progress</NavLink>
        </div>
      </nav>
      <main className={styles.main}>
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/decks" element={<DecksPage />} />
          <Route path="/decks/:deckId/study" element={<StudyPage />} />
          <Route path="/progress" element={<ProgressPage />} />
        </Routes>
      </main>
    </div>
  )
}
