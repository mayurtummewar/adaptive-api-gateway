import './App.css'
import Header from './components/Header'
import ProductCard from './components/ProductCard'
import Product from './pages/Product'
import Cart from './pages/Cart'
import { Route, Routes, useNavigate } from 'react-router'
import { useState } from 'react'

function App() {
  const products = [
    {
      id: 1,
      name: "Gateway Demo Jacket",
      category: "Clothing",
      description: "This is a generic discription for all the products on this website",
      price: 1299,
    },
    {
      id: 2,
      name: "Canvas Backpack",
      category: "Bags",
      description: "This is a generic discription for all the products on this website",
      price: 899,
    },
    {
      id: 3,
      name: "Canvas Backpack",
      category: "Bags",
      description: "This is a generic discription for all the products on this website",
      price: 899,
    },
    {
      id: 4,
      name: "Canvas Backpack",
      category: "Bags",
      description: "This is a generic discription for all the products on this website",
      price: 899,
    },
    {
      id: 5,
      name: "Canvas Backpack",
      category: "Bags",
      description: "This is a generic discription for all the products on this website",
      price: 899,
    },
    {
      id: 6,
      name: "Canvas Backpack",
      category: "Bags",
      description: "This is a generic discription for all the products on this website",
      price: 899,
    },
    {
      id: 7,
      name: "Canvas Backpack",
      category: "Bags",
      description: "This is a generic discription for all the products on this website",
      price: 899,
    },
    {
      id: 8,
      name: "Canvas Backpack",
      category: "Bags",
      description: "This is a generic discription for all the products on this website",
      price: 899,
    },
    {
      id: 9,
      name: "Silhouette Seed",
      category: "Bags",
      description: "This is a generic discription for all the products on this website",
      price: 1499,
    }
  ]
  const navigate = useNavigate();
  const [cartItems, setCartItems] = useState([])
  const addToCart = (product) => {
    setCartItems((currentItems) => {
      const existingItem = currentItems.find(
        (item) => item.product.id === product.id
      )

      if (existingItem) {
        return currentItems.map((item) =>
          item.product.id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        )
      }

      return [...currentItems, { product, quantity: 1 }]
    })
  }
  const decreaseCartItem = (productId) => {
    setCartItems((currentItems) => {
      const updatedItems = currentItems.map((item) =>
      item.product.id == productId
        ? {...item, quantity: item.quantity - 1}
        : item
      )
      return updatedItems.filter((item) => item.quantity > 0)
    })
  }
  const increaseCartItem = (productId) => {
    setCartItems((currentItems) => {
      const updatedItems =  currentItems.map((item) => 
        item.product.id === productId
        ? {...item, quantity: item.quantity + 1}
        : item
      )
      return updatedItems
    })
  }

  return (
    <>
      <Header />
      <Routes>
        <Route
          path="/"
          element={
            <main>
              <h1>Featured Products</h1>
              <p>Best of our Products</p>
              <div className="product-grid">
                {products.map((product) => (
                  <ProductCard
                  key={product.id}
                  product={product}
                  onSelect={() => navigate(`/products/${product.id}`)}
                  />
                ))}
              </div>
            </main>
          }
        />
        <Route
          path="/products/:productId"
          element={
            <Product
              products={products}
              onAddToCart={addToCart}
            />
          }
        />
        <Route
          path="/cart"
          element={
            <Cart
              cartItems={cartItems}
              onDecreaseQuantity={decreaseCartItem}
              onIncreaseQuantity={increaseCartItem}
            />
          }
        />
      </Routes>
    </>
  )
}

export default App
