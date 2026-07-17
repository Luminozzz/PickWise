import { useMemo, useState } from 'react'
import ProductCard from './ProductCard.jsx'
import ProductCardSkeleton from './ProductCardSkeleton.jsx'
import { Grid, Rows, Sliders, Sort, ChevronDown } from './icons.jsx'
import { connectivityLabel, buildTags, formatPrice } from '../format.js'

const SKELETON_COUNT = 6
const VIEW_KEY = 'pickwise_catalogue_view'

const SORTS = [
  { key: 'featured', label: 'Featured' },
  { key: 'price-asc', label: 'Price: Low to High' },
  { key: 'price-desc', label: 'Price: High to Low' },
  { key: 'rating', label: 'Top rated' },
  { key: 'weight-asc', label: 'Lightest first' },
  { key: 'name', label: 'Name A–Z' },
]

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
  const [sort, setSort] = useState('featured')
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
    const cmp = {
      'price-asc': (a, b) => (priceOf(a) ?? Infinity) - (priceOf(b) ?? Infinity),
      'price-desc': (a, b) => (priceOf(b) ?? -Infinity) - (priceOf(a) ?? -Infinity),
      rating: (a, b) => (b.rating?.stars ?? -1) - (a.rating?.stars ?? -1),
      'weight-asc': (a, b) => (a.weight ?? Infinity) - (b.weight ?? Infinity),
      name: (a, b) => (a.product_name || '').localeCompare(b.product_name || ''),
    }[sort]
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
          <label className="cat-select">
            <Sort size={16} />
            <select value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort">
              {SORTS.map((s) => (
                <option key={s.key} value={s.key}>{s.label}</option>
              ))}
            </select>
            <ChevronDown size={14} />
          </label>
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
