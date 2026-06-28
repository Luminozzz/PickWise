import { useState } from 'react'
import { ArrowRight } from './icons.jsx'
import { buildDescription, buildTags, formatCount, formatPrice } from '../format.js'
import { colourToHex } from '../colours.js'
import CriteriaTags from './CriteriaTags.jsx'

const MAX_SWATCHES = 6

// Catalogue / card-view product card. In the recommendations card view it also
// receives `rank`, `isBest`, and `criteria` (the questionnaire fit results),
// which surface a rank badge and the fit/unfit/neutral tags on the card.
export default function ProductCard({ item, rank, isBest, criteria, onNavigate }) {
  const [imgFailed, setImgFailed] = useState(false)

  const description = buildDescription(item)
  const tags = buildTags(item).slice(0, 3)

  // Split the title so the company name sits on its own line above the model.
  const brand = item.brand_name || ''
  const model =
    brand && item.product_name?.startsWith(brand)
      ? item.product_name.slice(brand.length).trim()
      : item.product_name

  const price = formatPrice(item.price)
  const rating = item.rating
  const colours = item.colours || []
  const hasCriteria = criteria && criteria.length > 0

  return (
    <article className="card">
      <div className="card__image">
        {rank != null && (
          <span className={'card__rank' + (isBest ? ' card__rank--best' : '')}>
            {isBest ? 'Best match' : `#${rank}`}
          </span>
        )}
        {item.img_link && !imgFailed ? (
          <img
            src={item.img_link}
            alt={item.product_name}
            loading="lazy"
            onError={() => setImgFailed(true)}
          />
        ) : (
          <div className="card__image-fallback" />
        )}
      </div>

      <h3 className="card__name">
        {brand && <span className="card__brand">{brand}</span>}
        <span className="card__model">{model}</span>
      </h3>
      <p className="card__desc">{description}</p>

      <div className="card__stats">
        <span className="card__price">
          {price ? (
            <>
              <span className="card__price-from">from</span> {price}
            </>
          ) : (
            <span className="card__price-na">Price unavailable</span>
          )}
        </span>
        {rating?.stars != null && (
          <span className="card__rating" title={`${rating.stars} out of 5`}>
            ★ {Number(rating.stars).toFixed(1)}
            {rating.reviews != null && (
              <span className="card__rating-count">({formatCount(rating.reviews)})</span>
            )}
          </span>
        )}
      </div>

      {colours.length > 0 && (
        <div
          className="card__colours"
          aria-label={`${colours.length} colour${colours.length > 1 ? 's' : ''}: ${colours.join(', ')}`}
        >
          {colours.slice(0, MAX_SWATCHES).map((c) => {
            const hex = colourToHex(c)
            return (
              <span
                key={c}
                className={'swatch' + (hex ? '' : ' swatch--unknown')}
                style={hex ? { background: hex } : undefined}
                title={c}
              />
            )
          })}
          {colours.length > MAX_SWATCHES && (
            <span className="card__colours-more">+{colours.length - MAX_SWATCHES}</span>
          )}
        </div>
      )}

      {hasCriteria ? (
        <CriteriaTags criteria={criteria} />
      ) : (
        tags.length > 0 && (
          <div className="card__tags">
            {tags.map((tag) => (
              <span className="tag" key={tag}>
                {tag}
              </span>
            ))}
          </div>
        )
      )}

      <div className="card__footer">
        <button className="card__action" type="button">
          Compare
        </button>
        <span className="card__footer-divider" />
        {onNavigate ? (
          <button
            className="card__action card__action--primary"
            type="button"
            onClick={() => onNavigate('product', item.id)}
          >
            View details <ArrowRight size={14} />
          </button>
        ) : item.link ? (
          <a
            className="card__action card__action--primary"
            href={item.link}
            target="_blank"
            rel="noreferrer"
          >
            View details <ArrowRight size={14} />
          </a>
        ) : (
          <button className="card__action card__action--primary" type="button">
            View details <ArrowRight size={14} />
          </button>
        )}
      </div>
    </article>
  )
}
