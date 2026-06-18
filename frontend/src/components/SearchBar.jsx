/**
 * frontend/src/components/SearchBar.jsx
 * 
 * A search bar component for searching fighters.
 */

import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function SearchBar() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const timerRef = useRef(null)
  const wrapRef = useRef(null)

  // Debounce the search query
  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      setOpen(false)
      return
    }

    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(async () => {
      try {
        const data = await api.search(query)
        setResults(data)
        setOpen(data.length > 0)
      } catch {
        setResults([])
      }
    }, 250)

    return () => clearTimeout(timerRef.current)
  }, [query])

  // Close the search dropdown when clicking outside of it
  useEffect(() => {
    const close = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false)
    }

    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [])

  // Select a fighter from the search results
  const select = (fighter) => {
    navigate(`/fighter/${encodeURIComponent(fighter.name)}`)
    setQuery('')
    setOpen(false)
  }

  return (
    <div className="search-wrap" ref={wrapRef}>
      <div className="search-input-row">
        <svg className="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>

        <input
          type="text"
          className="search-input"
          placeholder="Search fighter…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
        />
      </div>

      {open && (
        <div className="search-dropdown">
          {results.map((f) => (
            <button key={f.name} className="search-item" onClick={() => select(f)}>
              <span className="search-item-name">{f.name}</span>
              <span className="search-item-meta">{f.weight_class} · {f.elo}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
