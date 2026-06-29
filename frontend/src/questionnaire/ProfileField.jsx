import { useState } from 'react'

// Live, immediately-committing versions of the quiz inputs for the profile page.
// They share the quiz's CSS classes but report raw value changes via onChange.
export default function ProfileField({ question, value, onChange }) {
  switch (question.type) {
    case 'select':
      return <LiveSelect q={question} value={value} onChange={onChange} />
    case 'multiselect':
      return <LiveMulti q={question} value={value} onChange={onChange} />
    case 'slider':
      return <LiveSlider q={question} value={value} onChange={onChange} />
    case 'range':
      return <LiveRange q={question} value={value} onChange={onChange} />
    default:
      return null
  }
}

function LiveSelect({ q, value, onChange }) {
  return (
    <div className="quiz__options">
      {q.options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          aria-pressed={value === opt.value}
          className={'quiz__option' + (value === opt.value ? ' is-selected' : '')}
          onClick={() => onChange(opt.value)}
        >
          <span className="quiz__radio" aria-hidden="true" />
          <span className="quiz__option-label">{opt.label}</span>
        </button>
      ))}
    </div>
  )
}

function LiveMulti({ q, value, onChange }) {
  const sel = Array.isArray(value) ? value : []

  function toggle(opt) {
    if (opt.exclusive) {
      onChange(sel.length === 1 && sel[0] === opt.value ? [] : [opt.value])
      return
    }
    // selecting a normal option clears any exclusive ("No preference") choice
    const cleared = sel.filter((v) => {
      const o = q.options.find((x) => x.value === v)
      return v !== opt.value && !(o && o.exclusive)
    })
    onChange(sel.includes(opt.value) ? cleared : [...cleared, opt.value])
  }

  return (
    <div className="quiz__options">
      {q.options.map((opt) => (
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
  )
}

function LiveSlider({ q, value, onChange }) {
  const val = value ?? q.default ?? q.min
  return (
    <div className="quiz__slider">
      <div className="quiz__slider-value">
        {val}
        <span className="quiz__slider-unit">{q.unit}</span>
      </div>
      <input
        className="quiz__range-input quiz__range-input--single"
        type="range"
        min={q.min}
        max={q.max}
        step={q.step || 1}
        value={val}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label={q.text}
        aria-valuetext={`${val}${q.unit}`}
      />
      <div className="quiz__scale">
        <span>{q.min}{q.unit}</span>
        <span>{q.max}{q.unit}</span>
      </div>
    </div>
  )
}

function LiveRange({ q, value, onChange }) {
  const { min, max, step = 1, unit = '' } = q
  const lo = value?.min ?? q.defaultMin ?? min
  const hi = value?.max ?? q.defaultMax ?? max
  const pct = (v) => ((v - min) / (max - min)) * 100

  const setLow = (v) => onChange({ min: Math.min(Number(v), hi - step), max: hi })
  const setHigh = (v) => onChange({ min: lo, max: Math.max(Number(v), lo + step) })

  return (
    <div className="quiz__range-wrap">
      <div className="quiz__range-values">
        <span className="quiz__range-chip">{unit}{lo}</span>
        <span className="quiz__range-dash">to</span>
        <span className="quiz__range-chip">
          {unit}{hi}
          {hi >= max ? '+' : ''}
        </span>
      </div>
      <div className="quiz__range-track">
        <span
          className="quiz__range-fill"
          style={{ left: `${pct(lo)}%`, right: `${100 - pct(hi)}%` }}
        />
        <input
          className="quiz__range-input"
          type="range"
          min={min}
          max={max}
          step={step}
          value={lo}
          onChange={(e) => setLow(e.target.value)}
          aria-label="Minimum budget"
          aria-valuetext={`${unit}${lo}`}
        />
        <input
          className="quiz__range-input"
          type="range"
          min={min}
          max={max}
          step={step}
          value={hi}
          onChange={(e) => setHigh(e.target.value)}
          aria-label="Maximum budget"
          aria-valuetext={`${unit}${hi}${hi >= max ? '+' : ''}`}
        />
      </div>
      <div className="quiz__scale">
        <span>{unit}{min}</span>
        <span>{unit}{max}+</span>
      </div>
    </div>
  )
}
