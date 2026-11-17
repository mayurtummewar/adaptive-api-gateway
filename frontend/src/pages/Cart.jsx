import { Link } from 'react-router'

const Cart = ({ cartItems, onDecreaseQuantity, onIncreaseQuantity}) => {
  const cartTotal = cartItems.reduce(
    (total, item) => total + item.product.price * item.quantity,
    0
  )

  return (
    <main className="cart-page">
        <h1>Your Cart</h1>
        {cartItems.length === 0 ? (
            <p>Your cart is empty.</p>
        ):(
            <>
                <ul>
                    {cartItems.map((item) => (
                        <li className="cart-item"
                        key={item.product.id}
                        >
                            <div>
                            {item.product.name} ={'>'} quantity: {item.quantity}
                            --- Rs. {item.product.price*item.quantity}
                            </div>
                            <button
                                type="button"
                                aria-label={`Reduce quantity of ${item.product.name}`}
                                onClick={() => onDecreaseQuantity(item.product.id)}
                            >Reduce quantity</button>
                            <button
                                type="button"
                                aria-label={`Increase quantity of ${item.product.name}`}
                                onClick={() => onIncreaseQuantity(item.product.id)}
                            >Increase quantity</button>
                        </li>
                    ))}
                </ul>
                <p className="cart-total">Total: Rs. {cartTotal}</p>
            </>
        )}
        <Link to="/">Continue shopping</Link>
    </main>
  )
}

export default Cart