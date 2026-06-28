import ProductCard from './ProductCard.jsx'
import ProductCardSkeleton from './ProductCardSkeleton.jsx'

const SKELETON_COUNT = 6

export default function Catalogue({ items, loading, error, onNavigate }) {
  return (
    <main className="catalogue">
      {error ? (
        <div className="catalogue__error">
          <p>Couldn't load the catalogue.</p>
          <p>
            <code>{error}</code>
          </p>
          <p>Is the backend running?</p>
        </div>
      ) : (
        <div className="catalogue__grid">
          {loading
            ? Array.from({ length: SKELETON_COUNT }).map((_, i) => (
                <ProductCardSkeleton key={i} />
              ))
            : items.map((item) => (
                <ProductCard key={item.id} item={item} onNavigate={onNavigate} />
              ))}
        </div>
      )}
    </main>
  )
}