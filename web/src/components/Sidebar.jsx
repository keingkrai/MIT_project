import { useState, useEffect } from 'react'

const navItems = [
  { id: 'home', icon: '🏠', label: 'Home' },
  { id: 'generate', icon: '⚙️', label: 'Genarate' },
  { id: 'contact', icon: '👥', label: 'Contact' },
  { id: 'docs', icon: '📄', label: 'View Docs' },
]

function Sidebar({ currentPage, setCurrentPage }) {
  const [darkMode, setDarkMode] = useState(true)

  useEffect(() => {
    // Load theme from localStorage
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      setDarkMode(savedTheme === 'dark')
      document.documentElement.setAttribute('data-theme', savedTheme)
    } else {
      document.documentElement.setAttribute('data-theme', 'dark')
    }
  }, [])

  const toggleTheme = () => {
    const newTheme = darkMode ? 'light' : 'dark'
    setDarkMode(!darkMode)
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem('theme', newTheme)
  }

  return (
    <aside className="sidebar">
      <button className="hamburger-menu" aria-label="Menu">
        <span></span>
        <span></span>
        <span></span>
      </button>
      
      <div className="sidebar-logo">
        <div className="sidebar-logo-circle">
          <div className="sidebar-logo-inner"></div>
        </div>
      </div>
      
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-link ${currentPage === item.id ? 'active' : ''}`}
            onClick={() => setCurrentPage(item.id)}
          >
            <span className="icon">{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      
      <div className="theme-toggle-container">
        <label className="theme-toggle-switch">
          <input
            type="checkbox"
            checked={darkMode}
            onChange={toggleTheme}
          />
          <span className="toggle-slider"></span>
        </label>
      </div>
    </aside>
  )
}

export default Sidebar

