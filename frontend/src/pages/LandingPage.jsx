import { useEffect, useState } from 'react'
import Navbar from '../components/Navbar.jsx'
import Catalogue from '../components/Catalogue.jsx'
import { fetchItems } from '../api.js'

export default function LandingPage({ onNavigate, answers }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let active = true
    fetchItems()
      .then((data) => {
        if (active) setItems(Array.isArray(data) ? data : [])
      })
      .catch((err) => {
        if (active) setError(err.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  return (
    <>
      <Navbar onNavigate={onNavigate} />
      <Catalogue items={items} loading={loading} error={error} answers={answers} />
    </>
  )
}