import { useState, useEffect } from 'react'
import './LoginPage.css'

function LoginPage({ onNavigate }) {
  const [isDarkMode, setIsDarkMode] = useState(true)
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })

  useEffect(() => {
    // Load theme from localStorage or default to dark
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark')
      document.documentElement.setAttribute('data-theme', savedTheme)
    } else {
      document.documentElement.setAttribute('data-theme', 'dark')
    }
  }, [])

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    // Handle login logic here
    console.log('Login data:', formData)
    // Navigate to generate page after successful login
    onNavigate?.('generate')
  }

  return (
    <div className="login-container">
      {/* Left Panel - Informational */}
      <div className="login-left-panel">
        <div className="left-panel-content">
          <h2 className="welcome-text">Welcome to</h2>
          <div className="login-icon-circle">
            <div className="login-icon-inner"></div>
          </div>
          <h1 className="login-logo-text">Trading Agents</h1>
          <p className="login-subtitle">Multi-Agents LLM Financial Trading</p>
          <div className="login-description">
            <p>
              Experience the future of investing with our Trading Agent, powered by the collective intelligence of Multi-Agents LLM Financial Trading. 
              Our system isn't just a simple platform, but a network of intelligent agents that communicate, exchange data, and learn from millions 
              of trading experiences. The collaborative work of these AIs helps your Agent adapt, develop strategies, and continuously enhance its 
              ability to generate profits in all market conditions.
            </p>
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="login-right-panel">
        <div className="login-form-container">
          <button className="back-link" onClick={() => onNavigate?.('home')}>
            ← Back
          </button>
          
          <h1 className="login-title">Welcome Back</h1>
          <p className="login-subtitle-text">Log in to your account</p>

          <form className="login-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">
                Email<span className="required">*</span>
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">
                Password<span className="required">*</span>
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                className="form-input"
                required
              />
            </div>

            <div className="form-buttons">
              <button type="submit" className="signin-btn">Sign In</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default LoginPage










