/**
 * frontend/src/pages/FighterProfile.jsx
 * 
 * A page for displaying a fighter's profile.
 */

import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react'
import { api } from '../api/client'
import { methodLabel } from '../constants/weightClasses'

/**
 * A motion variant for the main content of the fighter profile page.
 */
const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.25, ease: 'easeOut' } },
  exit:    { opacity: 0, y: -8, transition: { duration: 0.15 } },
}

/**
 * A motion variant for the rows in the fight history table.
 */
const rowVariants = {
  hidden:  { opacity: 0, x: -6 },
  visible: (i) => ({
    opacity: 1, x: 0,
    transition: { delay: i * 0.025, duration: 0.2, ease: 'easeOut' },
  }),
}

const RESULT_LABELS = { win: 'W', loss: 'L', draw: 'D', nc: 'NC' }

/**
 * A badge component for displaying the result of a fight.
 */
function ResultBadge({ result }) {
  return (
    <span className={`result-badge ${result}`}>
      {result === 'win' && <ArrowUpRight size={11} strokeWidth={2.5} />}
      {result === 'loss' && <ArrowDownRight size={11} strokeWidth={2.5} />}
      {(result === 'draw' || result === 'nc') && <Minus size={11} strokeWidth={2.5} />}
      {RESULT_LABELS[result] ?? result}
    </span>
  )
}

/**
 * A badge component for displaying the delta of a fighter's Elo rating.
 */
function DeltaBadge({ delta }) {
  if (delta === 0) return <span className="delta zero">±0</span>
  if (delta > 0)   return <span className="delta pos">+{delta}</span>
  return <span className="delta neg">{delta}</span>
}

export default function FighterProfile() {
  const { name } = useParams()
  const navigate = useNavigate()
  const [fighter, setFighter] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch the fighter data when the component mounts
  useEffect(() => {
    setLoading(true)
    setError(null)

    api.fighter(decodeURIComponent(name))
      .then(setFighter)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [name])

  if (loading) return (
    <div className="content profile-loading">
      <div className="spinner" />
    </div>
  )

  if (error) return (
    <div className="content profile-loading">
      <button className="back-link" onClick={() => navigate(-1)}>
        <ArrowLeft size={13} /> Back
      </button>

      <div className="error-msg">{error}</div>
    </div>
  )

  if (!fighter) return null

  return (
    <motion.main variants={pageVariants} initial="initial" animate="animate" exit="exit">
      <div className="content profile-content">
        <Link to="/" className="back-link">
          <ArrowLeft size={13} /> Rankings
        </Link>

        {/* Hero */}
        <div className="fighter-hero">
          <div className="fighter-name">{fighter.name}</div>
          <div className="fighter-red-bar" />
          <div className="fighter-meta-row">
            {fighter.rank && (
              <span className="fighter-rank-tag">#{fighter.rank} Overall</span>
            )}
            <span className="wc-badge">{fighter.weight_class}</span>
          </div>
        </div>

        {/* Stats */}
        <div className="stats-grid">
          <div className="stat-card highlight">
            <div className="stat-label">Current Elo</div>
            <div className="stat-value">{fighter.current_elo.toLocaleString()}</div>
          </div>

          <div className="stat-card gold-card">
            <div className="stat-label">Peak Elo</div>
            <div className="stat-value">{fighter.peak_elo.toLocaleString()}</div>
          </div>

          <div className="stat-card">
            <div className="stat-label">Rank</div>
            <div className="stat-value">{fighter.rank ? `#${fighter.rank}` : '—'}</div>
          </div>

          <div className="stat-card green-card">
            <div className="stat-label">Wins</div>
            <div className="stat-value">{fighter.wins}</div>
          </div>

          <div className="stat-card loss-card">
            <div className="stat-label">Losses</div>
            <div className="stat-value">{fighter.losses}</div>
          </div>

          <div className="stat-card">
            <div className="stat-label">Record</div>
            <div className="stat-value" style={{ fontSize: '1.6rem' }}>{fighter.record}</div>
          </div>
        </div>

        {/* Fight History */}
        <div className="section-title">Fight History</div>

        {fighter.fight_history.length === 0 ? (
          <div className="state-center">No fight history.</div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Event</th>
                  <th>Opponent</th>
                  <th className="center">Result</th>
                  <th>Method</th>
                  <th className="right">Elo Change</th>
                </tr>
              </thead>

              <tbody>
                {fighter.fight_history.map((fight, i) => (
                  <motion.tr
                    key={i}
                    custom={i}
                    variants={rowVariants}
                    initial="hidden"
                    animate="visible"
                  >
                    <td className="event-cell">{fight.event}</td>

                    <td>
                      <Link
                        to={`/fighter/${encodeURIComponent(fight.opponent)}`}
                        className="opp-link"
                      >
                        {fight.opponent}
                      </Link>
                    </td>

                    <td className="center">
                      <ResultBadge result={fight.result} />
                    </td>

                    <td className="method-cell">{methodLabel(fight.method)}</td>

                    <td className="right">
                      <div className="elo-flow">
                        <span>{fight.elo_before}</span>
                        <span className="arrow">→</span>
                        <span>{fight.elo_after}</span>

                        <DeltaBadge delta={fight.delta} />
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </motion.main>
  )
}
