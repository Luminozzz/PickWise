import { QUESTIONS } from './questions.js'

// Render a recorded answer as readable text.
function formatAnswer(question, value) {
  if (value == null) return null
  if (question.type === 'range') {
    return `${question.unit}${value.min} – ${question.unit}${value.max}${value.max >= question.max ? '+' : ''}`
  }
  if (question.type === 'slider') {
    return `${value}${question.unit}`
  }
  if (question.type === 'multiselect') {
    if (!value.length) return 'No preference'
    const labels = value.map((v) => question.options.find((o) => o.value === v)?.label || v)
    return labels.join(', ')
  }
  // select
  return question.options.find((o) => o.value === value)?.label || String(value)
}

export default function Summary({ answers, onRestart, onNavigate }) {
  const rows = Object.keys(QUESTIONS)
    .map(Number)
    .filter((id) => answers[id] !== undefined)
    .map((id) => ({
      id,
      question: QUESTIONS[id].text,
      answer: formatAnswer(QUESTIONS[id], answers[id]),
    }))

  return (
    <main className="quiz quiz--done">
      <div className="quiz__panel">
        <div className="quiz__card quiz__card--summary">
          <span className="quiz__section">All done</span>
          <h2 className="quiz__question">Here's what we learned about you</h2>
          <p className="quiz__lead">
            We'll use these preferences to match you with the right mouse.
          </p>

          <ul className="quiz__summary">
            {rows.map((row) => (
              <li className="quiz__summary-row" key={row.id}>
                <span className="quiz__summary-q">{row.question}</span>
                <span className="quiz__summary-a">{row.answer}</span>
              </li>
            ))}
          </ul>

          <div className="quiz__done-actions">
            <button
              className="btn-primary"
              type="button"
              onClick={() => onNavigate && onNavigate('landing')}
            >
              See my matches
            </button>
            <button className="quiz__restart" type="button" onClick={onRestart}>
              Start over
            </button>
          </div>
        </div>
      </div>
    </main>
  )
}
