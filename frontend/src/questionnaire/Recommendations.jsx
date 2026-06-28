import { useEffect, useMemo, useState } from 'react'
import { fetchItems, fetchRecommendations } from '../api.js'
import { ArrowRight, Grid, Rows } from '../components/icons.jsx'
import CriteriaTags from '../components/CriteriaTags.jsx'
import ProductCard from '../components/ProductCard.jsx'

const VIEW_KEY = 'pickwise_recs_view'

function loadView() {
  try {
    return localStorage.getItem(VIEW_KEY) === 'card' ? 'card' : 'listing'
  } catch {
    return 'listing'
  }
}

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
  const [items, setItems] = useState(null)
  const [view, setView] = useState(loadView)

  // Retake = clear the profile and return to the questionnaire.
  const retake = () => onNavigate && onNavigate('questionnaire', null)

  const changeView = (next) => {
    setView(next)
    try {
      localStorage.setItem(VIEW_KEY, next)
    } catch {
      /* ignore storage errors */
    }
  }

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

  // Full catalogue data (specs, colours, rating) for the card view. Fetched once;
  // merged onto the ranked results by id.
  useEffect(() => {
    let active = true
    fetchItems()
      .then((d) => active && setItems(Array.isArray(d) ? d : []))
      .catch(() => active && setItems([]))
    return () => {
      active = false
    }
  }, [])

  const itemsById = useMemo(
    () => Object.fromEntries((items || []).map((it) => [it.id, it])),
    [items],
  )

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
    <main className={'recs' + (view === 'card' ? ' recs--wide' : '')}>
      <header className="recs__head">
        <div className="recs__head-row">
          <div>
            <span className="quiz__section">Your Matches</span>
            <h2 className="recs__title">Best Mice For You Ranked</h2>
          </div>
          <div className="recs__toggle" role="group" aria-label="Result view">
            <button
              type="button"
              className={'recs__toggle-btn' + (view === 'listing' ? ' is-active' : '')}
              aria-pressed={view === 'listing'}
              onClick={() => changeView('listing')}
            >
              <Rows size={15} /> List
            </button>
            <button
              type="button"
              className={'recs__toggle-btn' + (view === 'card' ? ' is-active' : '')}
              aria-pressed={view === 'card'}
              onClick={() => changeView('card')}
            >
              <Grid size={15} /> Cards
            </button>
          </div>
        </div>
      </header>

      {view === 'card' ? (
        <div className="recs__cards">
          {results.map((r, i) => {
            const item = itemsById[r.id] || {
              id: r.id,
              product_name: r.product_name,
              brand_name: r.brand_name,
              img_link: r.img_link,
            }
            const matched = r.passed_rules?.length || 0
            const isBest = matched === topMatched && matched > 0
            return (
              <ProductCard
                key={r.id}
                item={item}
                rank={i + 1}
                isBest={isBest}
                criteria={r.criteria}
                onNavigate={onNavigate}
              />
            )
          })}
        </div>
      ) : (
        <ol className="recs__list">
          {results.map((item, i) => {
            const { brand, model } = splitName(item)
            const matched = item.passed_rules?.length || 0
            const isBest = matched === topMatched && matched > 0
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
                  <CriteriaTags criteria={item.criteria} />
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
      )}

      <div className="recs__actions">
        <button className="btn-primary" type="button" onClick={() => onNavigate && onNavigate('profile')}>
          Edit preferences
        </button>
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
