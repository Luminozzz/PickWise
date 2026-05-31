import { useState } from 'react'
import { ArrowUp, ArrowDown, ArrowRight } from './icons.jsx'
import { buildDescription, buildTags } from '../format.js'

export default function ProductCard({ item }) {
  const [imgFailed, setImgFailed] = useState(false)

  const description = buildDescription(item)
  const tags = buildTags(item).slice(0, 3)

  const upside = item.upside || 'price'
  const downside = item.downside || 'performance'

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

      <h3 className="card__name">{item.product_name}</h3>
      <p className="card__desc">{description}</p>

      <div className="card__sides">
        <span className="card__side card__side--up">
          <ArrowUp />
          {upside}
        </span>
        <span className="card__side card__side--down">
          <ArrowDown />
          {downside}
        </span>
      </div>

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