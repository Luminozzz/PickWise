import { useEffect, useId, useRef, useState } from 'react'
import { Info } from '../components/icons.jsx'

// Explains the technical terms in a question. Opens on hover and on click: hover
// alone would leave the explanations unreachable on a touch screen, and click
// alone would make you commit a tap to read a definition. A click pins it open so
// it survives the pointer leaving, which is what lets you read a long entry
// without holding the mouse still.
export default function InfoButton({ entries, label = 'What does this mean?' }) {
  const [open, setOpen] = useState(false)
  const [pinned, setPinned] = useState(false)
  const wrapRef = useRef(null)
  const panelId = useId()

  useEffect(() => {
    if (!pinned) return
    const onDown = (e) => {
      if (!wrapRef.current?.contains(e.target)) {
        setPinned(false)
        setOpen(false)
      }
    }
    const onKey = (e) => {
      if (e.key === 'Escape') {
        setPinned(false)
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [pinned])

  if (!entries || entries.length === 0) return null

  const close = () => {
    setPinned(false)
    setOpen(false)
  }

  return (
    <span
      className="qhelp"
      ref={wrapRef}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => !pinned && setOpen(false)}
    >
      <button
        type="button"
        className={'qhelp__btn' + (open ? ' is-open' : '')}
        aria-label={label}
        aria-expanded={open}
        aria-controls={panelId}
        onFocus={() => setOpen(true)}
        onBlur={() => !pinned && setOpen(false)}
        onClick={(e) => {
          // The quiz option is a sibling, not an ancestor, but the profile page
          // nests this inside a clickable label. Stop either from reacting.
          e.stopPropagation()
          e.preventDefault()
          if (pinned) close()
          else {
            setPinned(true)
            setOpen(true)
          }
        }}
      >
        <Info size={16} />
      </button>

      {open && (
        <span className="qhelp__panel" id={panelId} role="tooltip">
          {entries.map((entry, i) => (
            <span className="qhelp__entry" key={entry.term || i}>
              {entry.term && <b className="qhelp__term">{entry.term}:</b>}{' '}
              {entry.text}
            </span>
          ))}
        </span>
      )}
    </span>
  )
}
