import { useState } from 'react'
import RangeSlider from './RangeSlider.jsx'

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
        <button
          key={opt.value}
          type="button"
          aria-pressed={answer === opt.value}
          className={'quiz__option' + (answer === opt.value ? ' is-selected' : '')}
          onClick={() => onSelect(opt)}
        >
          <span className="quiz__radio" aria-hidden="true" />
          <span className="quiz__option-label">{opt.label}</span>
        </button>
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
          <button
            key={opt.value}
            type="button"
            aria-pressed={sel.includes(opt.value)}
            className={'quiz__option' + (sel.includes(opt.value) ? ' is-selected' : '')}
            onClick={() => toggle(opt)}
          >
            <span className="quiz__check" aria-hidden="true" />
            <span className="quiz__option-label">{opt.label}</span>
          </button>
        ))}
      </div>
      <button className="btn-primary quiz__continue" type="button" onClick={() => onSubmit(sel)}>
        {sel.length ? 'Continue' : 'Skip'}
      </button>
    </div>
  )
}
