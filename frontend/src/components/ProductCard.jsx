import { useState } from 'react'
import { ArrowRight } from './icons.jsx'
import { buildDescription, buildTags, formatPrice } from '../format.js'

export default function ProductCard({ item }) {
  const [imgFailed, setImgFailed] = useState(false)

  const description = buildDescription(item)
  const tags = buildTags(item).slice(0, 3)

  // Split the title so the company name sits on its own line above the model.
  const brand = item.brand_name || ''
  const model =
    brand && item.product_name.startsWith(brand)
      ? item.product_name.slice(brand.length).trim()
      : item.product_name

  const price = formatPrice(item.price)
  const rating = item.rating
  const colours = item.colours || []

  return (
    <article className="card">
      <div className="card__image">
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
              <span className="card__rating-count">
                ({Number(rating.reviews).toLocaleString()})
              </span>
            )}
          </span>
        )}
      </div>

      {colours.length > 0 && (
        <p className="card__colours">
          {colours.length} colour{colours.length > 1 ? 's' : ''}: {colours.join(', ')}
        </p>
      )}

      {tags.length > 0 && (
        <div className="card__tags">
          {tags.map((tag) => (
            <span className="tag" key={tag}>
              {tag}
            </span>
          ))}
        </div>
      )}

      <div className="card__footer">
        <button className="card__action" type="button">
          Compare
        </button>
        <span className="card__footer-divider" />
        {item.link ? (
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