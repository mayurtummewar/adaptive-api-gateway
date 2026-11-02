import { Link, useParams } from 'react-router'

const Product = ({ products, onAddToCart }) => {
  const { productId } = useParams()
  const product = products.find((item) => item.id === Number(productId))

  if (!product) {
    return (
      <main>
        <p>Product not found.</p>
        <Link to="/">Back to products</Link>
      </main>
    )
  }

  return (
    <section className="product-details">
        <Link to="/">Back to products</Link>

        <div className="product-details-content">
            <div className="product-details-image" aria-hidden="true"></div>

            <div>
                <p>{product.category}</p>
                <h1>{product.name}</h1>
                <p>Rs. {product.price}</p>
                <button type="button" onClick={() => onAddToCart(product)}>
                  Add to cart
                </button>
                <p>{product.description}</p>
            </div>
        </div>
    </section>
  )
}

export default Product