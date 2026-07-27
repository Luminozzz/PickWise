import { useState } from 'react'
import RangeSlider from './RangeSlider.jsx'
import InfoButton from '../components/InfoButton.jsx'

// An option and, when the option names a technical term, its explanation. The
// info button is a sibling of the option rather than a child: a button inside a
// button is invalid, and the click would be fought over. It's positioned over the
// option's right edge so every option keeps its full width whether it has help or
// not.
export function OptionRow({ option, children }) {
  return (
    <div className={'quiz__option-row' + (option.help ? ' has-help' : '')}>
      {children}
      {option.help && (
        // Only the text: the option's own label already names the term, so
        // repeating it in bold above the explanation would say it twice.
        <InfoButton
          entries={[{ text: option.help.text }]}
          label={`What does ${option.label} mean?`}
        />
      )}
    </div>
  )
}

// Renders the right input for a question's type.
export default function QuestionView({ question, answer, onSelect, onSubmit }) {
  switch (question.type) {
    case 'select':
      return <SelectInput question={question} answer={answer} onSelect={onSelect} />
    case 'multiselect':
      return <MultiSelectInput question={question} initial={answer} onSubmit={onSubmit} />
    case 'slider':
      return <SliderInput question={question} initial={answer} onSubmit={onSubmit} />
    case 'range':
      return <RangeSlider question={question} initial={answer} onSubmit={onSubmit} />
    default:
      return null
  }
}

function SelectInput({ question, answer, onSelect }) {
  return (
    <div className="quiz__options">
      {question.options.map((opt) => (
        <OptionRow option={opt} key={opt.value}>
          <button
            type="button"
            aria-pressed={answer === opt.value}
            className={'quiz__option' + (answer === opt.value ? ' is-selected' : '')}
            onClick={() => onSelect(opt)}
          >
            <span className="quiz__radio" aria-hidden="true" />
            <span className="quiz__option-label">{opt.label}</span>
          </button>
        </OptionRow>
      ))}
    </div>
  )
}

function SliderInput({ question, initial, onSubmit }) {
  const [val, setVal] = useState(initial ?? question.default ?? question.min)
  return (
    <div className="quiz__slider">
      <div className="quiz__slider-value">
        {val}
        <span className="quiz__slider-unit">{question.unit}</span>
      </div>
      <input
        className="quiz__range-input quiz__range-input--single"
        type="range"
        min={question.min}
        max={question.max}
        step={question.step || 1}
        value={val}
        onChange={(e) => setVal(Number(e.target.value))}
        aria-label={question.text}
        aria-valuetext={`${val}${question.unit}`}
      />
      <div className="quiz__scale">
        <span>{question.min}{question.unit}</span>
        <span>{question.max}{question.unit}</span>
      </div>
      <button className="btn-primary quiz__continue" type="button" onClick={() => onSubmit(val)}>
        Continue
      </button>
    </div>
  )
}

function MultiSelectInput({ question, initial, onSubmit }) {
  const [sel, setSel] = useState(Array.isArray(initial) ? initial : [])

  function toggle(opt) {
    if (opt.exclusive) {
      setSel((prev) => (prev.length === 1 && prev[0] === opt.value ? [] : [opt.value]))
      return
    }
    setSel((prev) => {
      // selecting a normal option clears any exclusive ("No preference") choice
      const cleared = prev.filter((v) => {
        const o = question.options.find((x) => x.value === v)
        return v !== opt.value && !(o && o.exclusive)
      })
      return prev.includes(opt.value) ? cleared : [...cleared, opt.value]
    })
  }

  return (
    <div>
      <div className="quiz__options">
        {question.options.map((opt) => (
          <OptionRow option={opt} key={opt.value}>
            <button
              type="button"
              aria-pressed={sel.includes(opt.value)}
              className={'quiz__option' + (sel.includes(opt.value) ? ' is-selected' : '')}
              onClick={() => toggle(opt)}
            >
              <span className="quiz__check" aria-hidden="true" />
              <span className="quiz__option-label">{opt.label}</span>
            </button>
          </OptionRow>
        ))}
      </div>
      <button className="btn-primary quiz__continue" type="button" onClick={() => onSubmit(sel)}>
        {sel.length ? 'Continue' : 'Skip'}
      </button>
    </div>
  )
}
