import { useEffect, useMemo, useState } from 'react'
import Navbar from '../components/Navbar.jsx'
import ComparePicker from '../components/ComparePicker.jsx'
import { fetchCompare, fetchItems } from '../api.js'
import { ArrowUp, ArrowDown, Minus, ArrowRight } from '../components/icons.jsx'

const STATUS_ICON = { fit: ArrowUp, unfit: ArrowDown, neutral: Minus }
// Spoken equivalents of the fit arrows; 'none' stays silent (nothing was judged).
const STATUS_TEXT = {
  fit: '(fits your preferences)',
  unfit: "(doesn't fit your preferences)",
  neutral: '(borderline for your preferences)',
}

// Three columns side by side is the most that stays readable on a laptop; on a
// phone even two is tight, so that's the floor. 860px is the same point the
// product page uses to collapse its multi-column layouts.
const MAX_COLS = 3
const MOBILE_COLS = 2
const MOBILE_QUERY = '(max-width: 860px)'

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
  return `${currency || '$'}${Number.isInteger(n) ? n : n.toFixed(2)}`
}

// How many columns fit right now. The viewport decides what's *shown*; it never
// rewrites the URL, so rotating a phone can't silently drop a mouse from a
// shared link.
function useMaxCols() {
  const [cols, setCols] = useState(() =>
    typeof window !== 'undefined' && window.matchMedia(MOBILE_QUERY).matches
      ? MOBILE_COLS
      : MAX_COLS,
  )
  useEffect(() => {
    const mq = window.matchMedia(MOBILE_QUERY)
    const sync = () => setCols(mq.matches ? MOBILE_COLS : MAX_COLS)
    sync()
    mq.addEventListener('change', sync)
    return () => mq.removeEventListener('change', sync)
  }, [])
  return cols
}

export default function ComparePage({ productIds, answers, onNavigate }) {
  const maxCols = useMaxCols()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [items, setItems] = useState([])
  const [itemsFailed, setItemsFailed] = useState(false)
  const [picking, setPicking] = useState(null) // { index } | null

  // What we fetch is what the URL asks for — deliberately independent of the
  // viewport. Keying the fetch on the visible count instead would blank the
  // table and refetch every time a window crossed the mobile breakpoint.
  const requested = useMemo(() => (productIds || []).slice(0, MAX_COLS), [productIds])
  const key = requested.join('-')
  // Known from the prop straight away, unlike data.has_answers which is null
  // mid-fetch — reading that would flash "take the quiz" at people who took it.
  const hasAnswers = !!answers && Object.keys(answers).length > 0

  useEffect(() => {
    let active = true
    setError(null)
    if (!requested.length) {
      setData({ products: [], rows: [], has_answers: false })
      return
    }
    setData(null)
    fetchCompare(requested, answers)
      .then((d) => {
        if (!active) return
        // fetchCompare returns null on a 404 (none of the ids exist). Without
        // this branch !data would keep the page on "Loading…" forever.
        if (d === null) setError("Those mice couldn't be found.")
        else setData(d)
      })
      .catch((e) => active && setError(e.message))
    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, answers])

  // The picker needs the full catalogue; fetched once, lazily.
  useEffect(() => {
    let active = true
    fetchItems()
      .then((list) => {
        if (!active) return
        setItems(Array.isArray(list) ? list : [])
        setItemsFailed(false)
      })
      // Swallowing this would leave the picker claiming "No mice match", which
      // reads as an empty catalogue rather than a failed request.
      .catch(() => active && setItemsFailed(true))
    return () => {
      active = false
    }
  }, [])

  // The viewport only clips what's drawn; the extra mouse stays in the URL so a
  // link shared from a desktop doesn't lose a column on someone's phone.
  const allProducts = data?.products || []
  const rows = data?.rows || []
  const products = allProducts.slice(0, maxCols)
  const hidden = allProducts.length - products.length

  // Work from the ids the server actually resolved, never the raw URL ones. An
  // id for a deleted mouse would otherwise keep occupying a slot forever: the
  // Add button would vanish with only two columns on screen, and there'd be no
  // way to evict the ghost. Building every mutation from liveIds drops it on the
  // next interaction instead.
  const liveIds = allProducts.map((p) => p.id)
  const canAdd = allProducts.length < maxCols

  const go = (ids) => onNavigate('compare', ids)
  const removeAt = (id) => go(liveIds.filter((x) => x !== id))
  const choose = (id) => {
    const next = [...liveIds]
    if (picking && picking.index != null && picking.index < next.length) next[picking.index] = id
    else next.push(id)
    setPicking(null)
    go(next.slice(0, MAX_COLS))
  }

  return (
    <>
      <Navbar onNavigate={onNavigate} />
      <main className="cmp">
        <header className="cmp__head">
          <span className="quiz__section">Side By Side</span>
          <h2 className="cmp__title">Compare Mice</h2>
          <p className="cmp__lead">
            {hasAnswers
              ? 'Specs are ordered by what matters most to you, based on your quiz.'
              : 'Specs are shown in a general order of importance. Take the quiz to rank them around your needs.'}
          </p>
          {!hasAnswers && (
            <button
              className="quiz__restart"
              type="button"
              onClick={() => onNavigate('questionnaire')}
            >
              Take the quiz to personalise <ArrowRight size={14} />
            </button>
          )}
        </header>

        {error && (
          <div className="cmp__empty">
            <p>{error}</p>
            <button className="btn-primary" type="button" onClick={() => setPicking({ index: null })}>
              Choose a mouse
            </button>
          </div>
        )}

        {!error && !data && <div className="recs__state">Loading…</div>}

        {!error && data && requested.length === 0 && (
          <div className="cmp__empty">
            <p>Nothing to compare yet. Pick a mouse to start.</p>
            <button className="btn-primary" type="button" onClick={() => setPicking({ index: null })}>
              Choose a mouse
            </button>
          </div>
        )}

        {!error && data && requested.length > 0 && (
          <>
            {hidden > 0 && (
              <p className="cmp__note">
                Showing {products.length} of {allProducts.length}. A wider screen fits{' '}
                {MAX_COLS} side by side.
              </p>
            )}

            {/* Roles rather than a real <table>: the rows are display:grid, which
                strips a table's implicit semantics anyway. Without these the page
                reads as a flat run of numbers with nothing tying a value to a
                mouse — which is the one question this page exists to answer. */}
            <div
              className="cmp__grid"
              role="table"
              aria-label="Mouse comparison"
              style={{ '--cmp-cols': products.length + (canAdd ? 1 : 0) }}
            >
              {/* Product headers */}
              <div className="cmp__row cmp__row--head" role="row">
                <div className="cmp__rowlabel" role="columnheader" />
                {products.map((p) => {
                  const { brand, model } = splitName(p)
                  return (
                    <div className="cmp__col" role="columnheader" key={p.id}>
                      <button
                        className="cmp__remove"
                        type="button"
                        aria-label={`Remove ${model}`}
                        onClick={() => removeAt(p.id)}
                      >
                        ×
                      </button>
                      <button
                        className="cmp__thumb"
                        type="button"
                        onClick={() => onNavigate('product', p.id)}
                        title="View details"
                      >
                        {p.img_link ? <img src={p.img_link} alt={p.product_name} /> : null}
                      </button>
                      <span className="cmp__brand">{brand}</span>
                      <button
                        className="cmp__name"
                        type="button"
                        onClick={() => onNavigate('product', p.id)}
                      >
                        {model}
                      </button>
                      <span className="cmp__price">{money(p.price, p.currency) || '—'}</span>
                      {p.rating?.stars != null && (
                        <span className="card__rating">
                          ★ {Number(p.rating.stars).toFixed(1)}
                        </span>
                      )}
                      <button
                        className="cmp__swap"
                        type="button"
                        aria-label={`Change ${model}`}
                        onClick={() => setPicking({ index: liveIds.indexOf(p.id) })}
                      >
                        Change
                      </button>
                    </div>
                  )
                })}
                {canAdd && (
                  <div className="cmp__col cmp__col--add">
                    <button
                      className="cmp__add"
                      type="button"
                      onClick={() => setPicking({ index: null })}
                    >
                      <span className="cmp__add-plus">+</span>
                      Add a mouse
                    </button>
                  </div>
                )}
              </div>

              {/* Spec rows, most important first */}
              {rows.map((row) => (
                <div className="cmp__row" role="row" key={row.key}>
                  <div className="cmp__rowlabel" role="rowheader">{row.label}</div>
                  {row.cells.slice(0, maxCols).map((cell, i) => {
                    const Icon = STATUS_ICON[cell.status]
                    return (
                      <div
                        className={'cmp__cell cmp__cell--' + cell.status}
                        role="cell"
                        key={(products[i]?.id ?? i) + row.key}
                      >
                        {Icon ? (
                          <span className="cmp__cell-arrow" aria-hidden="true">
                            <Icon size={14} />
                          </span>
                        ) : null}
                        <span className={cell.value == null ? 'cmp__cell-na' : undefined}>
                          {cell.value == null ? '—' : cell.value}
                        </span>
                        {/* The arrow is the only fit cue and it's aria-hidden, so
                            without this the personalised ranking — the point of
                            the page — is invisible to screen readers. */}
                        {STATUS_TEXT[cell.status] && (
                          <span className="sr-only">{STATUS_TEXT[cell.status]}</span>
                        )}
                      </div>
                    )
                  })}
                  {canAdd && <div className="cmp__cell cmp__cell--ghost" role="cell" />}
                </div>
              ))}
            </div>
          </>
        )}

        <div className="recs__actions">
          <button className="btn-primary" type="button" onClick={() => onNavigate('landing')}>
            Browse all mice <ArrowRight size={14} />
          </button>
        </div>
      </main>

      {picking && (
        <ComparePicker
          items={items}
          failed={itemsFailed}
          exclude={liveIds}
          onPick={choose}
          onClose={() => setPicking(null)}
        />
      )}
    </>
  )
}
