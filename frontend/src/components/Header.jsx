import { Link } from 'react-router'

const Header = ({ cartItemCount, user, search, setSearch, onLogout }) => (
  <header className="site-header">
    <Link to="/" className="brand">GATEWAY<span>.</span></Link>
    <nav className="main-nav" aria-label="Main navigation">
      <Link to="/">Shop</Link>
      {user && <Link to="/orders">Orders</Link>}
    </nav>
    <div className="header-actions">
      <input className="header-search" type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search" aria-label="Search products" />
      <Link to="/cart" className="cart-link">Bag <span>{cartItemCount}</span></Link>
      {user ? <button type="button" className="account-link" onClick={onLogout}>Sign out</button> : <Link to="/login" className="account-link">Sign in</Link>}
    </div>
  </header>
)

export default Header
