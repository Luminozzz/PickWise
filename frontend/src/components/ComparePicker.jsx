import { useEffect, useMemo, useRef, useState } from 'react'
import { formatPrice } from '../format.js'

// Menu for choosing which mouse to compare against. Mice already in the
// comparison are listed but disabled, so it's obvious why they can't be picked
// twice rather than them silently vanishing from the list.
export default function ComparePicker({ items, exclude, onPick, onClose, failed }) {
  const [query, setQuery] = useState('')
  const inputRef = useRef(null)
  const panelRef = useRef(null)
  // Kept in a ref so the mount effect below can stay [] — depending on onClose
  // (a fresh arrow on every parent render) would re-run it constantly, stealing
  // focus back to the search box mid-typing.
  const closeRef = useRef(onClose)
  closeRef.current = onClose

  useEffect(() => {
    const opener = document.activeElement
    inputRef.current?.focus()

    const onKey = (e) => {
      if (e.key === 'Escape') {
        closeRef.current()
        return
      }
      if (e.key !== 'Tab') return
      // Keep Tab inside the dialog. The page behind is still focusable and sits
      // under an opaque scrim, so without this a Shift+Tab lands on an invisible
      // "Browse all mice" and Enter throws the comparison away.
      const focusables = panelRef.current?.querySelectorAll(
        'button:not([disabled]), input, [href], [tabindex]:not([tabindex="-1"])',
      )
      if (!focusables || !focusables.length) return
      const first = focusables[0]
      const last = focusables[focusables.length - 1]
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault()
        first.focus()
      }
    }

    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('keydown', onKey)
      // Hand focus back to whatever opened the picker, not the top of the page.
      if (opener instanceof HTMLElement) opener.focus()
    }
  }, [])

  const results = useMemo(() => {
    const q = query.trim().toLowerCase()
    const list = items || []
    if (!q) return list
    return list.filter((i) =>
      `${i.brand_name || ''} ${i.product_name || ''}`.toLowerCase().includes(q),
    )
  }, [items, query])

  return (
    <div className="picker" role="dialog" aria-modal="true" aria-label="Choose a mouse to compare">
      <div className="picker__scrim" onClick={onClose} />
      <div className="picker__panel" ref={panelRef}>
        <header className="picker__head">
          <h3 className="picker__title">Compare against…</h3>
          <button className="picker__close" type="button" aria-label="Close" onClick={onClose}>
            ×
          </button>
        </header>

        <input
          ref={inputRef}
          className="picker__search"
          type="search"
          placeholder="Search by name or brand"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />

        <ul className="picker__list">
          {failed && <li className="picker__none">Couldn't load the catalogue. Try again.</li>}
          {!failed && results.length === 0 && (
            <li className="picker__none">
              {query ? `No mice match “${query}”.` : 'Loading the catalogue…'}
            </li>
          )}
          {results.map((item) => {
            const already = (exclude || []).includes(item.id)
            const price = formatPrice(item.price)
            return (
              <li key={item.id}>
                <button
                  className="picker__item"
                  type="button"
                  disabled={already}
                  onClick={() => onPick(item.id)}
                >
                  <span className="picker__thumb">
                    {item.img_link ? <img src={item.img_link} alt="" loading="lazy" /> : null}
                  </span>
                  <span className="picker__name">
                    <span className="picker__brand">{item.brand_name}</span>
                    {item.product_name}
                  </span>
                  <span className="picker__price">
                    {already ? 'Comparing' : price || '—'}
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}
