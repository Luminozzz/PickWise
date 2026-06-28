import { useLayoutEffect, useMemo, useRef, useState } from 'react'
import Navbar from '../components/Navbar.jsx'
import ProfileField from '../questionnaire/ProfileField.jsx'
import { QUESTIONS } from '../questionnaire/questions.js'
import { profileSections } from '../questionnaire/sections.js'
import { ArrowRight } from '../components/icons.jsx'

const USER_TYPE_Q = QUESTIONS[1] // "Who will be the main user of this mouse?"

// Persona section that swipes when the user type changes: the outgoing fields
// glide out to the right while the incoming fields drift in from the left, with
// the height easing between the two so the rest of the page settles smoothly.
function PersonaSwap({ persona, renderField }) {
  const [shown, setShown] = useState(persona)
  const [out, setOut] = useState(null) // outgoing persona during a swipe
  const [height, setHeight] = useState('auto')
  const wrapRef = useRef(null)
  const inRef = useRef(null)

  // Persona changed → lock the current height and stage the swipe.
  useLayoutEffect(() => {
    if (persona.key === shown.key) {
      // Same persona, but its field list may have changed (e.g. a student toggling
      // "play games regularly" reveals the gamer questions) — update, no swipe.
      if (persona.questionIds.join(',') !== shown.questionIds.join(',')) setShown(persona)
      return
    }
    setHeight((wrapRef.current ? wrapRef.current.offsetHeight : 0) + 'px')
    setOut(shown)
    setShown(persona)
  }, [persona])

  // New layer mounted → ease the height to it, then drop the outgoing layer.
  useLayoutEffect(() => {
    if (!out) return
    const toHeight = inRef.current ? inRef.current.offsetHeight : 0
    const raf = requestAnimationFrame(() => setHeight(toHeight + 'px'))
    const done = setTimeout(() => {
      setOut(null)
      setHeight('auto')
    }, 620)
    return () => {
      cancelAnimationFrame(raf)
      clearTimeout(done)
    }
  }, [out, shown])

  return (
    <section className="profile__section profile__section--persona">
      <div
        className="profile__swap"
        ref={wrapRef}
        style={{ height }}
        data-swapping={out ? '' : undefined}
      >
        {out && (
          <div className="profile__swap-layer profile__swap-layer--out" key={'out-' + out.key}>
            <h3 className="profile__section-title">{out.title}</h3>
            {out.questionIds.map(renderField)}
          </div>
        )}
        <div
          className="profile__swap-layer profile__swap-layer--in"
          key={'in-' + shown.key}
          ref={inRef}
        >
          <h3 className="profile__section-title">{shown.title}</h3>
          {shown.questionIds.map(renderField)}
        </div>
      </div>
    </section>
  )
}

export default function ProfilePage({ answers, onNavigate, onSaveProfile }) {
  // Edit a local draft so changes don't mutate the live answers until saved.
  const [draft, setDraft] = useState(() => ({ ...(answers || {}) }))
  const [dirty, setDirty] = useState(false)
  const [status, setStatus] = useState('idle') // idle | saving | error
  const [error, setError] = useState(null)

  const sections = useMemo(() => profileSections(draft), [draft])
  const persona = sections.find((s) => s.key !== 'about')
  const about = sections.find((s) => s.key === 'about')

  function change(id, value) {
    setDraft((prev) => ({ ...prev, [id]: value }))
    setDirty(true)
  }

  async function save() {
    setStatus('saving')
    setError(null)
    try {
      await onSaveProfile(draft)
      setDirty(false)
      setStatus('idle')
    } catch (e) {
      setStatus('error')
      setError(e.message)
    }
  }

  const renderField = (id) => {
    const q = QUESTIONS[id]
    if (!q) return null
    return (
      <div className="profile__field" key={id}>
        <span className="profile__field-label">{q.text}</span>
        <ProfileField question={q} value={draft[id]} onChange={(v) => change(id, v)} />
      </div>
    )
  }

  return (
    <>
      <Navbar onNavigate={onNavigate} />
      <main className="profile">
        <header className="profile__head">
          <span className="quiz__section">Your Preferences</span>
          <h2 className="profile__title">Edit Your Profile</h2>
        </header>

        {/* User — the persona selector lives in its own section. */}
        <section className="profile__section">
          <h3 className="profile__section-title">User</h3>
          <div className="profile__field">
            <span className="profile__field-label">{USER_TYPE_Q.text}</span>
            <ProfileField question={USER_TYPE_Q} value={draft[1]} onChange={(v) => change(1, v)} />
          </div>
        </section>

        {/* Persona-specific questions — swipe in/out when the user type changes. */}
        {persona && <PersonaSwap persona={persona} renderField={renderField} />}

        {/* About you — shown for everyone. */}
        <section className="profile__section">
          <h3 className="profile__section-title">{about.title}</h3>
          {about.questionIds.map(renderField)}
        </section>

        {error && <p className="profile__error">Couldn't save: {error}</p>}

        <div className="profile__actions">
          <button
            className="btn-primary"
            type="button"
            onClick={save}
            disabled={!dirty || status === 'saving'}
          >
            {status === 'saving' ? 'Saving…' : 'Save Changes'}
          </button>
          <button
            className="btn-primary"
            type="button"
            onClick={() => onNavigate('recommendations', draft)}
          >
            See Updated Matches <ArrowRight size={14} />
          </button>
          <button
            className="quiz__restart"
            type="button"
            onClick={() => onNavigate('questionnaire', null)}
          >
            Retake From Scratch
          </button>
        </div>
      </main>
    </>
  )
}
