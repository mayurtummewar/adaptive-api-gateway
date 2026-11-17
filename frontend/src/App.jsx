import './App.css'
import { Link, Route, Routes, useNavigate, useParams } from 'react-router'
import { useCallback, useEffect, useMemo, useState } from 'react'
import Header from './components/Header'

const money = (value) => `Rs. ${Number(value).toLocaleString('en-IN', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})}`

function ProductCard({ product, onSelect }) {
  return (
    <article className="product-card">
      <img src={product.image_url} alt="" className="product-image" />
      <div className="product-card-body">
        <p className="eyebrow">{product.category}</p>
        <h2>{product.name}</h2>
        <p className="muted">{product.description}</p>
        <div className="product-card-footer">
          <strong>{money(product.price)}</strong>
          <button type="button" className="button button-dark" onClick={onSelect}>
            View product
          </button>
        </div>
      </div>
    </article>
  )
}

function Home({ products, search, setSearch, onSelect }) {
  const categories = ['All', ...new Set(products.map((product) => product.category))]
  const [category, setCategory] = useState('All')
  const filtered = products.filter((product) => (
    (category === 'All' || product.category === category) &&
    `${product.name} ${product.description}`.toLowerCase().includes(search.toLowerCase())
  ))

  return (
    <main>
      <section className="hero-panel">
        <div>
          <p className="eyebrow">THE GATEWAY EDIT</p>
          <h1>Thoughtful goods for everyday living.</h1>
          <p className="hero-copy">A small collection of useful, well-made pieces. Browse the edit and make your next order with confidence.</p>
          <a className="button button-light" href="#collection">Shop the collection</a>
        </div>
        <div className="hero-orb" aria-hidden="true" />
      </section>
      <section id="collection" className="collection-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">CURATED FOR YOU</p>
            <h2>Featured products</h2>
          </div>
          <input
            className="search-input"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search products"
            aria-label="Search products"
          />
        </div>
        <div className="category-list">
          {categories.map((item) => (
            <button key={item} type="button" className={category === item ? 'category active' : 'category'} onClick={() => setCategory(item)}>
              {item}
            </button>
          ))}
        </div>
        <div className="product-grid">
          {filtered.map((product) => (
            <ProductCard key={product.id} product={product} onSelect={() => onSelect(product.id)} />
          ))}
        </div>
        {!filtered.length && <div className="empty-state"><h2>No products found</h2><p>Try a different search or category.</p></div>}
      </section>
    </main>
  )
}

function ProductPage({ products, onAdd }) {
  const { productId } = useParams()
  const product = products.find((item) => item.id === Number(productId))
  if (!product) return <main className="page"><div className="empty-state"><h1>Product not found</h1><Link to="/" className="button button-dark">Back to shop</Link></div></main>
  return (
    <main className="page product-page">
      <Link to="/" className="back-link">← Back to collection</Link>
      <div className="product-detail">
        <img src={product.image_url} alt={product.name} className="product-detail-image" />
        <div className="product-detail-copy">
          <p className="eyebrow">{product.category} · {product.brand}</p>
          <h1>{product.name}</h1>
          <p className="detail-price">{money(product.price)}</p>
          <p className="detail-description">{product.description}</p>
          <p className="stock-note">{product.stock_quantity > 0 ? `${product.stock_quantity} available` : 'Currently out of stock'}</p>
          <button type="button" className="button button-dark button-large" disabled={!product.stock_quantity} onClick={() => onAdd(product)}>
            Add to bag
          </button>
        </div>
      </div>
    </main>
  )
}

function CartPage({ cart, onUpdate, onRemove, onCheckout, user }) {
  const items = cart?.items || []
  return (
    <main className="page">
      <div className="page-heading"><p className="eyebrow">YOUR SELECTION</p><h1>Your bag</h1></div>
      {!user && <div className="notice">Sign in to save your bag and check out. <Link to="/login">Sign in</Link></div>}
      {!items.length ? (
        <div className="empty-state"><h2>Your bag is waiting</h2><p>Add something from the collection to get started.</p><Link to="/" className="button button-dark">Continue shopping</Link></div>
      ) : (
        <div className="cart-layout">
          <div className="cart-list">
            {items.map((item) => (
              <article className="cart-row" key={item.product.id}>
                <img src={item.product.image_url} alt="" className="cart-image" />
                <div className="cart-row-info"><p className="eyebrow">{item.product.category}</p><h2>{item.product.name}</h2><p>{money(item.product.price)}</p></div>
                <div className="quantity-control"><button type="button" onClick={() => onUpdate(item.product.id, item.quantity - 1)} disabled={item.quantity <= 1}>−</button><span>{item.quantity}</span><button type="button" onClick={() => onUpdate(item.product.id, item.quantity + 1)}>+</button></div>
                <button type="button" className="text-button" onClick={() => onRemove(item.product.id)}>Remove</button>
              </article>
            ))}
          </div>
          <aside className="summary-card"><p className="eyebrow">ORDER SUMMARY</p><div className="summary-line"><span>Subtotal</span><strong>{money(cart.total)}</strong></div><div className="summary-line"><span>Delivery</span><span>Free</span></div><div className="summary-total"><span>Total</span><strong>{money(cart.total)}</strong></div><button type="button" className="button button-dark button-full" onClick={onCheckout}>Place order</button></aside>
        </div>
      )}
    </main>
  )
}

function AuthPage({ mode, onSubmit, error }) {
  const login = mode === 'login'
  const [form, setForm] = useState({ full_name: '', email: '', password: '' })
  const submit = (event) => { event.preventDefault(); onSubmit(form) }
  return (
    <main className="page auth-page">
      <div className="auth-card"><p className="eyebrow">{login ? 'WELCOME BACK' : 'JOIN THE EDIT'}</p><h1>{login ? 'Sign in' : 'Create your account'}</h1><p className="muted">{login ? 'Access your saved bag and order history.' : 'Keep your bag, orders, and details together.'}</p>
        <form onSubmit={submit} className="form-stack">
          {!login && <label>Full name<input required minLength="2" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} /></label>}
          <label>Email<input required type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></label>
          <label>Password<input required minLength="8" type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} /></label>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button-dark button-full">{login ? 'Sign in' : 'Create account'}</button>
        </form>
        <p className="auth-switch">{login ? 'New here?' : 'Already have an account?'} <Link to={login ? '/signup' : '/login'}>{login ? 'Create an account' : 'Sign in'}</Link></p>
      </div>
    </main>
  )
}

function OrdersPage({ orders, user }) {
  if (!user) return <main className="page empty-state"><h1>Sign in to view orders</h1><Link to="/login" className="button button-dark">Sign in</Link></main>
  return <main className="page"><div className="page-heading"><p className="eyebrow">YOUR ACCOUNT</p><h1>Order history</h1></div>{!orders.length ? <div className="empty-state"><h2>No orders yet</h2><p>Your completed orders will appear here.</p><Link to="/" className="button button-dark">Explore the collection</Link></div> : <div className="order-list">{orders.map((order) => <article className="order-card" key={order.id}><div><p className="eyebrow">ORDER {order.id.slice(0, 8).toUpperCase()}</p><h2>{new Date(order.created_at).toLocaleDateString()}</h2></div><span className="status-pill">{order.status}</span><strong>{money(order.total)}</strong><ul>{order.items.map((item) => <li key={item.product_id}>{item.product_name} × {item.quantity}</li>)}</ul></article>)}</div>}</main>
}

function App() {
  const navigate = useNavigate()
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState(null)
  const [orders, setOrders] = useState([])
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem('gateway-user') || 'null'))
  const [token, setToken] = useState(() => localStorage.getItem('gateway-token'))
  const [search, setSearch] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const request = useCallback(async (path, options = {}) => {
    const response = await fetch(`/api${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(options.headers || {}) } })
    const body = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`)
    return body
  }, [token])

  useEffect(() => { request('/products').then(setProducts).catch((err) => setError(err.message)) }, [request])
  useEffect(() => {
    if (!token) return undefined
    let cancelled = false
    const loadAccountData = async () => {
      try {
        const [nextCart, nextOrders] = await Promise.all([
          request('/cart'),
          request('/orders'),
        ])
        if (!cancelled) {
          setCart(nextCart)
          setOrders(nextOrders)
        }
      } catch {
        if (!cancelled) setToken(null)
      }
    }
    loadAccountData()
    return () => { cancelled = true }
  }, [request, token])

  const cartCount = useMemo(() => (cart?.items || []).reduce((total, item) => total + item.quantity, 0), [cart])
  const addToCart = async (product) => {
    if (!user) { navigate('/login'); return }
    try { setCart(await request('/cart/items', { method: 'POST', body: JSON.stringify({ product_id: product.id, quantity: 1 }) })); setNotice('Added to your bag'); navigate('/cart') } catch (err) { setError(err.message) }
  }
  const updateCart = async (productId, quantity) => { if (quantity < 1) return; try { setCart(await request(`/cart/items/${productId}`, { method: 'PATCH', body: JSON.stringify({ quantity }) })) } catch (err) { setError(err.message) } }
  const removeFromCart = async (productId) => { try { setCart(await request(`/cart/items/${productId}`, { method: 'DELETE' })) } catch (err) { setError(err.message) } }
  const authenticate = async (mode, form) => {
    try {
      const body = await request(`/auth/${mode}`, { method: 'POST', body: JSON.stringify(form) })
      localStorage.setItem('gateway-token', body.access_token); localStorage.setItem('gateway-user', JSON.stringify(body.user)); setToken(body.access_token); setUser(body.user); setError(''); navigate('/')
    } catch (err) { setError(err.message) }
  }
  const logout = () => { localStorage.removeItem('gateway-token'); localStorage.removeItem('gateway-user'); setToken(null); setUser(null); setCart(null); navigate('/') }
  const checkout = async () => { try { await request('/orders', { method: 'POST' }); const nextOrders = await request('/orders'); setOrders(nextOrders); setCart(null); setNotice('Order placed successfully'); navigate('/orders') } catch (err) { setError(err.message) } }

  return <>
    <Header cartItemCount={cartCount} user={user} search={search} setSearch={setSearch} onLogout={logout} />
    {notice && <button type="button" className="toast" onClick={() => setNotice('')}>{notice} ×</button>}
    {error && <button type="button" className="toast error-toast" onClick={() => setError('')}>{error} ×</button>}
    <Routes>
      <Route path="/" element={<Home products={products} search={search} setSearch={setSearch} onSelect={(id) => navigate(`/products/${id}`)} />} />
      <Route path="/products/:productId" element={<ProductPage products={products} onAdd={addToCart} />} />
      <Route path="/cart" element={<CartPage cart={cart} user={user} onUpdate={updateCart} onRemove={removeFromCart} onCheckout={checkout} />} />
      <Route path="/login" element={<AuthPage mode="login" error={error} onSubmit={(form) => authenticate('login', form)} />} />
      <Route path="/signup" element={<AuthPage mode="signup" error={error} onSubmit={(form) => authenticate('signup', form)} />} />
      <Route path="/orders" element={<OrdersPage orders={orders} user={user} />} />
    </Routes>
    <footer><span>GATEWAY / LOCAL EDIT</span><span>Securely routed by APISIX</span></footer>
  </>
}

export default App
