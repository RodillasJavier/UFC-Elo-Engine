/**
 * frontend/src/pages/Rankings.jsx
 * 
 * A page for displaying the UFC ELO rankings.
 */

import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { api } from '../api/client'
import RankingsTable from '../components/RankingsTable'

const PER_PAGE = 50

/**
 * A motion variant for the main content of the rankings page.
 */
const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.25, ease: 'easeOut' } },
  exit:    { opacity: 0, y: -8, transition: { duration: 0.15 } },
}

export default function Rankings() {
  const [eloType, setEloType] = useState('current')
  const [weightClass, setWeightClass] = useState('all')
  const [weightClasses, setWeightClasses] = useState([])
  const [page, setPage] = useState(1)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch the available weight classes when the component mounts
  useEffect(() => {
    api.weightClasses().then(setWeightClasses).catch(() => {})
  }, [])

  const fetchRankings = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const res = await api.rankings({ type: eloType, weight_class: weightClass, page, per_page: PER_PAGE })
      setData(res)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [eloType, weightClass, page])

  // Fetch the rankings when the filters change
  useEffect(() => {
    fetchRankings()
  }, [fetchRankings])

  /**
   * Changes the active filter for the rankings.
   * 
   * @param {*} newType - The new ELO type to filter by
   * @param {*} newWC - The new weight class to filter by
   */
  const changeFilter = (newType, newWC) => {
    setPage(1)
    if (newType !== undefined) setEloType(newType)
    if (newWC !== undefined) setWeightClass(newWC)
  }

  const totalPages = data ? Math.ceil(data.total / PER_PAGE) : 1

  return (
    <motion.main variants={pageVariants} initial="initial" animate="animate" exit="exit">
      <div className="content">
        <div className="page-header">
          <h1 className="page-title">
            UFC <span className="accent">ELO</span> Rankings
          </h1>

          <p className="page-subtitle">
            Elo-based ratings for every UFC fighter — updated through May 2026
          </p>
        </div>

        <div className="filter-bar">
          <div className="toggle-group">
            <button
              className={`toggle-btn ${eloType === 'current' ? 'active' : ''}`}
              onClick={() => changeFilter('current', undefined)}
            >
              Current
            </button>

            <button
              className={`toggle-btn ${eloType === 'peak' ? 'active' : ''}`}
              onClick={() => changeFilter('peak', undefined)}
            >
              Peak
            </button>
          </div>

          <div className="wc-pills">
            <button
              className={`wc-pill ${weightClass === 'all' ? 'active' : ''}`}
              onClick={() => changeFilter(undefined, 'all')}
            >
              All
            </button>

            {weightClasses.map((wc) => (
              <button
                key={wc}
                className={`wc-pill ${weightClass === wc ? 'active' : ''}`}
                onClick={() => changeFilter(undefined, wc)}
              >
                {wc}
              </button>
            ))}
          </div>

          {data && (
            <span className="results-count">{data.total.toLocaleString()} fighters</span>
          )}
        </div>

        {loading && <div className="spinner" />}
        {error && <div className="error-msg">Error: {error}</div>}
        {!loading && !error && data && (
          <>
            <RankingsTable rankings={data.rankings} />

            {totalPages > 1 && (
              <div className="pagination">
                <button
                  className="page-btn"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  ← Prev
                </button>

                <span className="page-info">{page} / {totalPages}</span>

                <button
                  className="page-btn"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next →
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </motion.main>
  )
}
