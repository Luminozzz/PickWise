import { useState } from 'react'

// Dual-thumb budget range. Two overlaid range inputs share one track; CSS
// keeps the inputs click-through except on the thumbs (see index.css).
export default function RangeSlider({ question, initial, onSubmit }) {
  const { min, max, step = 1, unit = '' } = question
  const [lo, setLo] = useState(initial?.min ?? question.defaultMin ?? min)
  const [hi, setHi] = useState(initial?.max ?? question.defaultMax ?? max)

  const setLow = (v) => setLo(Math.min(Number(v), hi - step))
  const setHigh = (v) => setHi(Math.max(Number(v), lo + step))
  const pct = (v) => ((v - min) / (max - min)) * 100

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

      <button
        className="btn-primary quiz__continue"
        type="button"
        onClick={() => onSubmit({ min: lo, max: hi })}
      >
        Continue
      </button>
    </div>
  )
}
