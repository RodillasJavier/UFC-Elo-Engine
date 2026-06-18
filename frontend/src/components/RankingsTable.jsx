/**
 * frontend/src/components/RankingsTable.jsx
 * 
 * A table for displaying fighter rankings.
 */

import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { shortenWC } from '../constants/weightClasses'

/**
 * The variants for the ranking rows.
 */
const rowVariants = {
  hidden: { opacity: 0, x: -8 },
  visible: (i) => ({
    opacity: 1,
    x: 0,
    transition: { delay: i * 0.018, duration: 0.22, ease: 'easeOut' },
  }),
}

export default function RankingsTable({ rankings }) {
  if (!rankings || rankings.length === 0) {
    return <div className="state-center">No fighters found.</div>
  }

  return (
    <div className="rankings-list">
      {rankings.map((row, i) => (
        <motion.div
          key={row.fighter}
          custom={i}
          variants={rowVariants}
          initial="hidden"
          animate="visible"
        >
          <Link
            to={`/fighter/${encodeURIComponent(row.fighter)}`}
            className="ranking-row"
          >
            <div className={`rank-col ${row.rank <= 10 ? 'top-10' : ''}`}>
              {row.rank}
            </div>

            <div className="name-col">
              <div className="fighter-name-row">{row.fighter}</div>

              <div className="fighter-sub">
                <span className="wc-badge">{shortenWC(row.weight_class)}</span>
                <span className="record">{row.record}</span>
              </div>
            </div>

            <div className="elo-col">
              <div className="elo-score">{row.elo.toLocaleString()}</div>
              <div className="elo-label">ELO</div>
            </div>
          </Link>
        </motion.div>
      ))}
    </div>
  )
}
