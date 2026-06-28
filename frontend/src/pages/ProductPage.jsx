import { useEffect, useState } from 'react'
import Navbar from '../components/Navbar.jsx'
import { fetchProduct } from '../api.js'
import { colourToHex } from '../colours.js'
import { ArrowUp, ArrowDown, Minus, ArrowRight } from '../components/icons.jsx'

const STATUS_ICON = { fit: ArrowUp, unfit: ArrowDown, neutral: Minus }
const THUMB_SLOTS = 5

function splitName(p) {
  const brand = p.brand_name || ''
  const model =
    brand && p.product_name?.startsWith(brand)
      ? p.product_name.slice(brand.length).trim()
      : p.product_name
  return { brand, model }
}

function money(amount, currency) {
  if (amount == null) return null
  const n = Number(amount)
  const value = Number.isInteger(n) ? n.toString() : n.toFixed(2)
  return `${currency || '$'}${value}`
}

export default function ProductPage({ productId, answers, onNavigate }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    let active = true
    setData(null)
    setError(null)
    setSelected(null)
    fetchProduct(productId, answers)
      .then((d) => {
        if (!active) return
        if (d === null) setError('Product not found.')
        else {
          setData(d)
          setSelected(d.img_link || d.alt_img_link || null)
        }
      })
      .catch((e) => active && setError(e.message))
    return () => {
      active = false
    }
  }, [productId, answers])

  if (error) {
    return (
      <>
        <Navbar onNavigate={onNavigate} />
        <main className="pdp">
          <div className="recs__state">{error}</div>
          <button className="quiz__restart" type="button" onClick={() => onNavigate('landing')}>
            Back to catalogue
          </button>
        </main>
      </>
    )
  }

  if (!data) {
    return (
      <>
        <Navbar onNavigate={onNavigate} />
        <main className="pdp">
          <div className="recs__state">
            <span className="recs__spinner" aria-hidden="true" />
            Loading…
          </div>
        </main>
      </>
    )
  }

  const { brand, model } = splitName(data)
  const images = [data.img_link, data.alt_img_link].filter(Boolean)
  const thumbs = images.slice()
  while (thumbs.length < THUMB_SLOTS) thumbs.push(null)
  const colours = data.colours || []
  const criteria = data.criteria || []
  const price = money(data.price, data.currency)

  return (
    <>
      <Navbar onNavigate={onNavigate} />
      <main className="pdp">
        <button className="pdp__back" type="button" onClick={() => window.history.back()}>
          ← Back
        </button>

        <div className="pdp__hero">
          {/* Gallery */}
          <div className="pdp__gallery">
            <div className="pdp__image">
              {selected ? (
                <img src={selected} alt={data.product_name} />
              ) : (
                <div className="card__image-fallback" />
              )}
            </div>
            <div className="pdp__thumbs">
              {thumbs.map((src, i) => (
                <button
                  key={i}
                  type="button"
                  className={
                    'pdp__thumb' +
                    (src && src === selected ? ' is-active' : '') +
                    (src ? '' : ' pdp__thumb--empty')
                  }
                  onClick={() => src && setSelected(src)}
                  disabled={!src}
                  aria-label={src ? `View image ${i + 1}` : undefined}
                >
                  {src && <img src={src} alt="" />}
                </button>
              ))}
            </div>
          </div>

          {/* Info */}
          <div className="pdp__info">
            <div className="pdp__panel pdp__head">
              <span className="pdp__brand">{brand}</span>
              <h1 className="pdp__title">{model}</h1>
              <p className="pdp__desc">{data.description}</p>
            </div>

            {criteria.length > 0 && (
              <div className="pdp__tags">
                {criteria.map((c, i) => {
                  const Icon = STATUS_ICON[c.status] || Minus
                  return (
                    <span
                      key={c.label + i}
                      className={'rec-tag rec-tag--' + c.status}
                      title={c.detail}
                    >
                      <Icon size={12} />
                      {c.label}
                    </span>
                  )
                })}
              </div>
            )}

            <div className="pdp__panel pdp__buy">
              <span className="pdp__price">
                {price ? (
                  <>
                    <span className="card__price-from">from</span> {price}
                  </>
                ) : (
                  <span className="card__price-na">Price unavailable</span>
                )}
              </span>
              {data.rating?.stars != null && (
                <span className="card__rating" title={`${data.rating.stars} out of 5`}>
                  ★ {Number(data.rating.stars).toFixed(1)}
                  <span className="card__rating-count">({data.rating.reviews ?? 0})</span>
                </span>
              )}
            </div>

            {colours.length > 0 && (
              <div className="pdp__colours">
                {colours.map((c) => {
                  const hex = colourToHex(c)
                  return (
                    <span
                      key={c}
                      className={'swatch swatch--lg' + (hex ? '' : ' swatch--unknown')}
                      style={hex ? { background: hex } : undefined}
                      title={c}
                    />
                  )
                })}
              </div>
            )}

            <div className="pdp__actions">
              {data.link && (
                <a className="btn-primary" href={data.link} target="_blank" rel="noreferrer">
                  Visit store <ArrowRight size={14} />
                </a>
              )}
              {!data.has_answers && (
                <button
                  className="quiz__restart"
                  type="button"
                  onClick={() => onNavigate('questionnaire')}
                >
                  Take the quiz to personalise →
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Scrolled detail: specs ordered by importance, with fit arrows */}
        <section className="pdp__specs">
          <header className="pdp__specs-head">
            <span className="pdp__brand pdp__brand--accent">
              {data.has_answers ? 'How It Fits You' : 'Specifications'}
            </span>
            <h2 className="pdp__specs-title">
              {data.has_answers ? 'Details, Ranked By What Matters To You' : 'Full Specifications'}
            </h2>
          </header>
          <ul className="pdp__spec-list">
            {data.details.map((d) => {
              const Icon = STATUS_ICON[d.status]
              return (
                <li className={'pdp__spec pdp__spec--' + d.status} key={d.key}>
                  <span className="pdp__spec-arrow" aria-hidden="true">
                    {Icon ? <Icon size={15} /> : null}
                  </span>
                  <span className="pdp__spec-label">{d.label}</span>
                  <span className="pdp__spec-value">{d.value}</span>
                </li>
              )
            })}
          </ul>
        </section>
      </main>
    </>
  )
}
