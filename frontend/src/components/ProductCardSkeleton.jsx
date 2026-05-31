export default function ProductCardSkeleton() {
  return (
    <article className="card" aria-hidden="true">
      <div className="skeleton skeleton--image" />
      <div className="skeleton skeleton--title" />
      <div className="skeleton skeleton--text" />
      <div className="skeleton skeleton--line" />
      <div className="skeleton skeleton--line" />
      <div className="card__tags">
        <div className="skeleton skeleton--tag" />
        <div className="skeleton skeleton--tag" />
        <div className="skeleton skeleton--tag" />
      </div>
      <div className="skeleton skeleton--footer" />
    </article>
  )
}