/**
 * frontend/src/App.jsx
 * 
 * The main application component.
 */

import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import SearchBar from './components/SearchBar'
import Rankings from './pages/Rankings'
import FighterProfile from './pages/FighterProfile'

/**
 * The main navigation bar component.
 * 
 * @returns Navigation bar component
 */
function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
      <Link to="/" className="logo">
          UFC <span>ELO</span>
      </Link>

      <SearchBar />
      </div>
    </nav>
  )
}

/**
 * The main application component.
 * 
 * @returns Main application component
 */
export default function App() {
  const location = useLocation()

  return (
    <div className="page-wrap">
      <Navbar />

      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<Rankings />} />
          <Route path="/fighter/:name" element={<FighterProfile />} />
        </Routes>
      </AnimatePresence>
    </div>
  )
}
