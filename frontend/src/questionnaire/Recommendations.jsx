import { useEffect, useState } from 'react'
import { fetchRecommendations } from '../api.js'
import { ArrowRight } from '../components/icons.jsx'

function splitName(item) {
  const brand = item.brand_name || ''
  const model =
    brand && item.product_name?.startsWith(brand)
      ? item.product_name.slice(brand.length).trim()
      : item.product_name
  return { brand, model }
}

export default function Recommendations({ answers, onNavigate }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  // Retake = clear the profile and return to the questionnaire.
  const retake = () => onNavigate && onNavigate('questionnaire', null)

  useEffect(() => {
    let active = true
    setData(null)
    setError(null)
    fetchRecommendations(answers)
      .then((d) => active && setData(d))
      .catch((e) => active && setError(e.message))
    return () => {
      active = false
    }
  }, [answers])

  if (error) {
    return (
      <main className="recs">
        <div className="recs__state">Couldn't load recommendations. {error}</div>
        <button className="quiz__restart" type="button" onClick={retake}>
          Start over
        </button>
      </main>
    )
  }

  if (!data) {
    return (
      <main className="recs">
        <div className="recs__state">
          <span className="recs__spinner" aria-hidden="true" />
          Finding your best matches…
        </div>
      </main>
    )
  }

  const results = data.results || []
  const topMatched = results.length ? results[0].passed_rules?.length || 0 : 0

  return (
    <main className="recs">
      <header className="recs__head">
        <span className="quiz__section">Your matches</span>
        <h2 className="recs__title">Mice ranked for you</h2>
        <p className="recs__lead">
          Ordered best-fit first. Lower-ranked options don't match every preference,
          but are still shown.
        </p>
      </header>

      <ol className="recs__list">
        {results.map((item, i) => {
          const { brand, model } = splitName(item)
          const matched = item.passed_rules?.length || 0
          const isBest = matched === topMatched && matched > 0
          // pick a couple of the most useful explanations to surface
          const why = Object.values(item.explanations || {}).slice(0, 2)
          return (
            <li className="rec" key={item.id}>
              <span className="rec__rank">{i + 1}</span>
              <div className="rec__img">
                {item.img_link ? (
                  <img src={item.img_link} alt={item.product_name} loading="lazy" />
                ) : (
                  <div className="rec__img-fallback" />
                )}
              </div>
              <div className="rec__body">
                <div className="rec__name">
                  <span className="rec__brand">{brand}</span>
                  <span className="rec__model">{model}</span>
                </div>
                {why.length > 0 && (
                  <ul className="rec__why">
                    {why.map((text, k) => (
                      <li key={k}>{text}</li>
                    ))}
                  </ul>
                )}
              </div>
              <div className="rec__meta">
                {item.price != null ? (
                  <span className="rec__price">${Number(item.price).toFixed(2)}</span>
                ) : (
                  <span className="rec__price rec__price--na">—</span>
                )}
                <span className={'rec__match' + (isBest ? ' is-best' : '')}>
                  {isBest ? 'Best match' : `${matched} matched`}
                </span>
              </div>
            </li>
          )
        })}
      </ol>

      <div className="recs__actions">
        <button className="btn-primary" type="button" onClick={() => onNavigate && onNavigate('landing')}>
          Browse all mice <ArrowRight size={14} />
        </button>
        <button className="quiz__restart" type="button" onClick={retake}>
          Retake quiz
        </button>
      </div>
    </main>
  )
}
