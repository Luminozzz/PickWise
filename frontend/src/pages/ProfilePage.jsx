import { useMemo, useState } from 'react'
import Navbar from '../components/Navbar.jsx'
import ProfileField from '../questionnaire/ProfileField.jsx'
import { QUESTIONS } from '../questionnaire/questions.js'
import { profileSections } from '../questionnaire/sections.js'
import { ArrowRight } from '../components/icons.jsx'

const USER_TYPE_Q = QUESTIONS[1] // "Who will be the main user of this mouse?"

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
          <p className="profile__lead">
            Change anything below and save — we'll re-rank your matches. Switching the
            user type keeps your other answers in the background.
          </p>
        </header>

        {/* User — the persona selector lives in its own section. */}
        <section className="profile__section">
          <h3 className="profile__section-title">User</h3>
          <div className="profile__field">
            <span className="profile__field-label">{USER_TYPE_Q.text}</span>
            <ProfileField question={USER_TYPE_Q} value={draft[1]} onChange={(v) => change(1, v)} />
          </div>
        </section>

        {/* Persona-specific questions — keyed by persona so the section
            re-animates whenever the user type changes. */}
        {persona && (
          <section className="profile__section profile__section--persona" key={persona.key}>
            <h3 className="profile__section-title">{persona.title}</h3>
            {persona.questionIds.map(renderField)}
          </section>
        )}

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
