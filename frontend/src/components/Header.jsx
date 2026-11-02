import { Link } from 'react-router'

const Header = () => {
  return (
    <header className="site-header">
        <strong className="brand">EC</strong>
        <input
            type="search"
            placeholder="Search Products"
            aria-label="Search Products"
        />
        <Link to="/cart">Cart</Link>
        <button type="button">Account</button>
    </header>
  )
}

export default Header