import { ArrowUp, ArrowDown, Minus } from './icons.jsx'

// Three rows of criterion chips: fits (green ↑), misfits (red ↓), and neutral
// near-misses (yellow –). Empty rows are dropped; each chip's tooltip is the
// full explanation from the algorithm. Shared by the recommendations listing
// rows and the recommendation card view.
const TAG_ROWS = [
  { kind: 'fit', Icon: ArrowUp },
  { kind: 'unfit', Icon: ArrowDown },
  { kind: 'neutral', Icon: Minus },
]

export default function CriteriaTags({ criteria }) {
  if (!criteria || criteria.length === 0) return null
  return (
    <div className="rec__tags">
      {TAG_ROWS.map(({ kind, Icon }) => {
        const items = criteria.filter((c) => c.status === kind)
        if (items.length === 0) return null
        return (
          <div className="rec__tag-row" key={kind}>
            {items.map((c, i) => (
              <span className={'rec-tag rec-tag--' + kind} key={c.label + i} title={c.detail}>
                <Icon size={11} />
                {c.label}
              </span>
            ))}
          </div>
        )
      })}
    </div>
  )
}
