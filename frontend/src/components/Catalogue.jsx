import { useEffect, useMemo, useRef, useState } from 'react'
import ProductCard from './ProductCard.jsx'
import ProductCardSkeleton from './ProductCardSkeleton.jsx'
import { Grid, Rows, Sliders, Sort, ChevronDown, ArrowUp, ArrowDown } from './icons.jsx'
import { connectivityLabel, buildTags, formatPrice } from '../format.js'

const SKELETON_COUNT = 6
const VIEW_KEY = 'pickwise_catalogue_view'

// `dir: null` marks a field with no meaningful inverse — there's no "least
// featured" or "lowest rated" to ask for — and the direction toggle is disabled
// on those rather than offering a flip that means nothing.
const SORTS = [
  { key: 'featured', field: 'featured', dir: null, label: 'Featured' },
  { key: 'rating', field: 'rating', dir: null, label: 'Top rated' },
  { key: 'price-asc', field: 'price', dir: 'asc', label: 'Price: Low to High' },
  { key: 'price-desc', field: 'price', dir: 'desc', label: 'Price: High to Low' },
  { key: 'weight-asc', field: 'weight', dir: 'asc', label: 'Lightest first' },
  { key: 'weight-desc', field: 'weight', dir: 'desc', label: 'Heaviest first' },
  { key: 'name-asc', field: 'name', dir: 'asc', label: 'Name A–Z' },
  { key: 'name-desc', field: 'name', dir: 'desc', label: 'Name Z–A' },
]

const DEFAULT_SORT = SORTS[0].key

// Matches connectivityLabel() output so filtering is a plain string compare.
const CONNECTIVITY_OPTIONS = ['Wireless', 'Wired', 'Wired + Wireless']

function loadView() {
  try {
    return localStorage.getItem(VIEW_KEY) === 'list' ? 'list' : 'card'
  } catch {
    return 'card'
  }
}

const priceOf = (it) => (it.price && it.price.amount != null ? Number(it.price.amount) : null)

// Unknown values always sink to the bottom, whichever way the sort points, so a
// mouse with no price never outranks one that has a real number.
export const COMPARATORS = {
  'price-asc': (a, b) => (priceOf(a) ?? Infinity) - (priceOf(b) ?? Infinity),
  'price-desc': (a, b) => (priceOf(b) ?? -Infinity) - (priceOf(a) ?? -Infinity),
  rating: (a, b) => (b.rating?.stars ?? -1) - (a.rating?.stars ?? -1),
  'weight-asc': (a, b) => (a.weight ?? Infinity) - (b.weight ?? Infinity),
  'weight-desc': (a, b) => (b.weight ?? -Infinity) - (a.weight ?? -Infinity),
  'name-asc': (a, b) => (a.product_name || '').localeCompare(b.product_name || ''),
  'name-desc': (a, b) => (b.product_name || '').localeCompare(a.product_name || ''),
  // 'featured' has no comparator on purpose: it means "leave the API's order".
}

// Sort control. The native <select> is gone because its popup can't be themed
// cross-browser — so everything it gave us for free (arrow keys, Home/End,
// type-ahead, Escape, click-away, focus return) is re-implemented here rather
// than quietly dropped.
function SortControl({ value, onChange }) {
  const [open, setOpen] = useState(false)
  const wrapRef = useRef(null)
  const triggerRef = useRef(null)
  const listRef = useRef(null)

  const current = SORTS.find((s) => s.key === value) || SORTS[0]

  const close = ({ refocus = true } = {}) => {
    setOpen(false)
    if (refocus) triggerRef.current?.focus()
  }

  // Close when the click lands anywhere else on the page.
  useEffect(() => {
    if (!open) return
    const onDown = (e) => {
      if (!wrapRef.current?.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [open])

  // Open with the current option focused, so arrow keys start from where you are
  // rather than from the top of the list.
  useEffect(() => {
    if (!open) return
    const list = listRef.current
    const target = list?.querySelector('[aria-selected="true"]') || list?.firstElementChild
    target?.focus()
  }, [open])

  const options = () => [...(listRef.current?.querySelectorAll('[role="option"]') || [])]

  const onListKeyDown = (e) => {
    const items = options()
    const at = items.indexOf(document.activeElement)

    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault()
      const next = e.key === 'ArrowDown' ? Math.min(at + 1, items.length - 1) : Math.max(at - 1, 0)
      items[next]?.focus()
    } else if (e.key === 'Home') {
      e.preventDefault()
      items[0]?.focus()
    } else if (e.key === 'End') {
      e.preventDefault()
      items[items.length - 1]?.focus()
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      const key = document.activeElement?.dataset.sortKey
      if (key) {
        onChange(key)
        close()
      }
    } else if (e.key === 'Escape') {
      e.preventDefault()
      close()
    } else if (e.key === 'Tab') {
      setOpen(false) // let focus move on naturally
    } else if (e.key.length === 1) {
      // Type-ahead, wrapping past the current position — the native select had
      // this and losing it would be a regression.
      const from = at + 1
      const ordered = [...items.slice(from), ...items.slice(0, from)]
      ordered
        .find((el) => el.textContent.trim().toLowerCase().startsWith(e.key.toLowerCase()))
        ?.focus()
    }
  }

  const DirIcon = current.dir === 'asc' ? ArrowUp : current.dir === 'desc' ? ArrowDown : Sort

  return (
    <div className={'cat-select' + (open ? ' is-open' : '')} ref={wrapRef}>
      <button
        ref={triggerRef}
        type="button"
        className="cat-select__trigger"
        onClick={() => setOpen((o) => !o)}
        onKeyDown={(e) => {
          if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            e.preventDefault()
            setOpen(true)
          }
        }}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        {/* Reflects which way the current sort points. #5 makes this a control. */}
        <span className="cat-select__dir" aria-hidden="true">
          <DirIcon size={15} />
        </span>
        <span className="cat-select__value">{current.label}</span>
        <span className="cat-select__chev" aria-hidden="true">
          <ChevronDown size={14} />
        </span>
      </button>

      {open && (
        <ul
          className="cat-select__menu"
          role="listbox"
          aria-label="Sort by"
          ref={listRef}
          onKeyDown={onListKeyDown}
        >
          {SORTS.map((s, i) => (
            <li
              key={s.key}
              role="option"
              aria-selected={s.key === value}
              tabIndex={-1}
              data-sort-key={s.key}
              className={'cat-select__opt' + (s.key === value ? ' is-selected' : '')}
              style={{ '--row': i }}
              onClick={() => {
                onChange(s.key)
                close()
              }}
            >
              <span className="cat-select__opt-dir" aria-hidden="true">
                {s.dir === 'asc' ? <ArrowUp size={12} /> : s.dir === 'desc' ? <ArrowDown size={12} /> : null}
              </span>
              {s.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function CatalogueRow({ item, answers, onNavigate }) {
  const brand = item.brand_name || ''
  const model =
    brand && item.product_name?.startsWith(brand)
      ? item.product_name.slice(brand.length).trim()
      : item.product_name
  const tags = buildTags(item, answers).slice(0, 3)
  const price = formatPrice(item.price)
  return (
    <li
      className={'rec' + (onNavigate ? ' rec--clickable' : '')}
      onClick={onNavigate ? () => onNavigate('product', item.id) : undefined}
      role={onNavigate ? 'button' : undefined}
      tabIndex={onNavigate ? 0 : undefined}
      onKeyDown={
        onNavigate
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onNavigate('product', item.id)
              }
            }
          : undefined
      }
    >
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
        {tags.length > 0 && (
          <div className="card__tags rec__inline-tags">
            {tags.map((t) => (
              <span className="tag" key={t}>{t}</span>
            ))}
          </div>
        )}
      </div>
      <div className="rec__meta">
        {price ? (
          <span className="rec__price">{price}</span>
        ) : (
          <span className="rec__price rec__price--na">—</span>
        )}
        {item.rating?.stars != null && (
          <span className="card__rating" title={`${item.rating.stars} out of 5`}>
            ★ {Number(item.rating.stars).toFixed(1)}
          </span>
        )}
      </div>
    </li>
  )
}

export default function Catalogue({ items, loading, error, answers, onNavigate }) {
  const [view, setView] = useState(loadView)
  const [sort, setSort] = useState(DEFAULT_SORT)
  const [brands, setBrands] = useState([])
  const [conns, setConns] = useState([])
  const [showFilters, setShowFilters] = useState(false)

  const changeView = (v) => {
    setView(v)
    try {
      localStorage.setItem(VIEW_KEY, v)
    } catch {
      /* ignore */
    }
  }

  const allBrands = useMemo(
    () => [...new Set((items || []).map((i) => i.brand_name).filter(Boolean))].sort(),
    [items],
  )

  const displayed = useMemo(() => {
    let list = [...(items || [])]
    if (brands.length) list = list.filter((i) => brands.includes(i.brand_name))
    if (conns.length) list = list.filter((i) => conns.includes(connectivityLabel(i.connectivity)))
    const cmp = COMPARATORS[sort]
    if (cmp) list.sort(cmp)
    return list
  }, [items, brands, conns, sort])

  const toggleIn = (setter, arr, val) =>
    setter(arr.includes(val) ? arr.filter((x) => x !== val) : [...arr, val])
  const activeFilters = brands.length + conns.length

  if (error) {
    return (
      <main className="catalogue">
        <div className="catalogue__error">
          <p>Couldn't load the catalogue.</p>
          <p><code>{error}</code></p>
          <p>Is the backend running?</p>
        </div>
      </main>
    )
  }

  return (
    <main className="catalogue">
      <div className="catalogue__toolbar">
        <span className="catalogue__count">
          {loading ? 'Loading…' : `${displayed.length} ${displayed.length === 1 ? 'mouse' : 'mice'}`}
        </span>
        <div className="catalogue__tools">
          <button
            type="button"
            className={'cat-btn' + (showFilters ? ' is-active' : '')}
            onClick={() => setShowFilters((s) => !s)}
            aria-expanded={showFilters}
          >
            <Sliders size={16} /> Filter
            {activeFilters > 0 && <span className="cat-btn__count">{activeFilters}</span>}
          </button>
          <SortControl value={sort} onChange={setSort} />
          <div className="recs__toggle" role="group" aria-label="View">
            <button
              type="button"
              className={'recs__toggle-btn' + (view === 'list' ? ' is-active' : '')}
              aria-pressed={view === 'list'}
              onClick={() => changeView('list')}
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
      </div>

      {showFilters && (
        <div className="catalogue__filters">
          <div className="filter-group">
            <span className="filter-group__label">Brand</span>
            <div className="filter-chips">
              {allBrands.map((b) => (
                <button
                  key={b}
                  type="button"
                  className={'filter-chip' + (brands.includes(b) ? ' is-on' : '')}
                  aria-pressed={brands.includes(b)}
                  onClick={() => toggleIn(setBrands, brands, b)}
                >
                  {b}
                </button>
              ))}
            </div>
          </div>
          <div className="filter-group">
            <span className="filter-group__label">Connectivity</span>
            <div className="filter-chips">
              {CONNECTIVITY_OPTIONS.map((c) => (
                <button
                  key={c}
                  type="button"
                  className={'filter-chip' + (conns.includes(c) ? ' is-on' : '')}
                  aria-pressed={conns.includes(c)}
                  onClick={() => toggleIn(setConns, conns, c)}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>
          {activeFilters > 0 && (
            <button
              type="button"
              className="filter-clear"
              onClick={() => {
                setBrands([])
                setConns([])
              }}
            >
              Clear all
            </button>
          )}
        </div>
      )}

      {loading ? (
        <div className="catalogue__grid">
          {Array.from({ length: SKELETON_COUNT }).map((_, i) => (
            <ProductCardSkeleton key={i} />
          ))}
        </div>
      ) : displayed.length === 0 ? (
        <p className="catalogue__empty">No mice match these filters.</p>
      ) : view === 'card' ? (
        <div className="catalogue__grid">
          {displayed.map((it) => (
            <ProductCard key={it.id} item={it} answers={answers} onNavigate={onNavigate} />
          ))}
        </div>
      ) : (
        <ol className="catalogue__list">
          {displayed.map((it) => (
            <CatalogueRow key={it.id} item={it} answers={answers} onNavigate={onNavigate} />
          ))}
        </ol>
      )}
    </main>
  )
}
