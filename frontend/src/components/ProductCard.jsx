const ProductCard = ({product, onSelect}) => {
  return (
    <article className="product-card">
        <div className="product-image" aria-hidden="true"></div>
        <h2>{product.name}</h2>
        <p>{product.category}</p>
        <p>Rs. {product.price}</p>
        <button type="button" onClick={() => onSelect(product)}>
            View details
        </button>
    </article>
  )
}

export default ProductCard