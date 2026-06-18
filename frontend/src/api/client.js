/**
 * frontend/src/api/client.js
 * 
 * A client for making API requests.
 */

const BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

/**
 * Fetches data from the API.
 * 
 * @param {string} path 
 * @returns {Promise<any>}
 */
async function apiFetch(path) {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

/**
 * The API client.
 */
export const api = {
  rankings: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return apiFetch(`/api/rankings${qs ? '?' + qs : ''}`)
  },
  search: (q) => apiFetch(`/api/fighters/search?q=${encodeURIComponent(q)}`),
  fighter: (name) => apiFetch(`/api/fighters/${encodeURIComponent(name)}`),
  weightClasses: () => apiFetch('/api/weight_classes'),
}
