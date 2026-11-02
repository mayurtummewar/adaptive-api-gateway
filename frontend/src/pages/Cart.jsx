import { Link } from 'react-router'

const Cart = ({ cartItems, onDecreaseQuantity, onIncreaseQuantity}) => {
  return (
    <main className="cart-page">
        <h1>Your Cart</h1>
        {cartItems.length === 0 ? (
            <p>Your cart is empty.</p>
        ):(
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
                            type='button'
                            onClick={() => onDecreaseQuantity(item.product.id)}
                        >Reduce quantity</button>
                        <button
                            type='button'
                            onClick={() => onIncreaseQuantity(item.product.id)}
                        >Increase quantity</button>
                    </li>
                ))}
            </ul>
        )}
        <Link to="/">Continue shopping</Link>
    </main>
  )
}

export default Cart