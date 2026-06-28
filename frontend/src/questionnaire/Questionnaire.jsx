import { useEffect, useRef } from 'react'
import { useQuestionnaire } from './useQuestionnaire.js'
import QuestionView from './QuestionView.jsx'
import Recommendations from './Recommendations.jsx'

export default function Questionnaire({ onNavigate }) {
  const q = useQuestionnaire()
  const headingRef = useRef(null)

  // Move focus to the new question heading each step so screen readers announce
  // it and keyboard context follows along.
  useEffect(() => {
    headingRef.current?.focus()
  }, [q.question?.id])

  // Keyboard: 1–9 picks a select option, Backspace goes back.
  useEffect(() => {
    function onKey(e) {
      if (q.done || !q.question) return
      if (e.key === 'Backspace' && q.canBack) {
        e.preventDefault()
        q.back()
        return
      }
      if (q.question.type === 'select') {
        const n = parseInt(e.key, 10)
        if (n >= 1 && n <= q.question.options.length) {
          q.select(q.question.options[n - 1])
        }
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [q])

  if (q.done) {
    return <Recommendations answers={q.answers} onRestart={q.restart} onNavigate={onNavigate} />
  }

  return (
    <main className="quiz">
      <div className="quiz__progress" aria-hidden="true">
        <span
          className="quiz__progress-fill"
          style={{ width: `${Math.round(q.progress * 100)}%` }}
        />
      </div>

      <div className="quiz__panel">
        {/* key remounts the card per question so the slide animation replays */}
        <div className="quiz__card" key={q.question.id} data-dir={q.direction}>
          <div className="quiz__meta">
            <span className="quiz__section">{q.question.section}</span>
          </div>
          <h2 className="quiz__question" ref={headingRef} tabIndex={-1}>
            {q.question.text}
          </h2>

          <QuestionView
            question={q.question}
            answer={q.answers[q.question.id]}
            onSelect={q.select}
            onSubmit={q.submit}
          />
        </div>
      </div>

      <div className="quiz__footer">
        <button
          className="quiz__back"
          type="button"
          onClick={q.back}
          disabled={!q.canBack}
        >
          ← Back
        </button>
      </div>
    </main>
  )
}
