import { useState, useEffect } from 'react'
import './RegisterPage.css'

function RegisterPage({ onNavigate }) {
  const [isDarkMode, setIsDarkMode] = useState(true)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
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
    // Handle registration logic here
    console.log('Registration data:', formData)
  }

  return (
    <div className="register-container">
      {/* Left Panel - Informational */}
      <div className="register-left-panel">
        <div className="left-panel-content">
          <h2 className="welcome-text">Welcome to</h2>
          <div className="register-icon-circle">
            <div className="register-icon-inner"></div>
          </div>
          <h1 className="register-logo-text">Trading Agents</h1>
          <p className="register-subtitle">Multi-Agents LLM Financial Trading</p>
          <div className="register-description">
            <p>
              Experience the future of investing with our Trading Agent, powered by the collective intelligence of Multi-Agents LLM Financial Trading. 
              Our system isn't just a simple platform, but a network of intelligent agents that communicate, exchange data, and learn from millions 
              of trading experiences. The collaborative work of these AIs helps your Agent adapt, develop strategies, and continuously enhance its 
              ability to generate profits in all market conditions.
            </p>
          </div>
        </div>
      </div>

      {/* Right Panel - Registration Form */}
      <div className="register-right-panel">
        <div className="register-form-container">
          <h1 className="register-title">create your account</h1>
          <button className="back-link" onClick={() => onNavigate?.('home')}>
            ← Back
          </button>

          <form className="register-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="name">Name</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className="form-input"
              />
            </div>

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

            <div className="form-group">
              <label htmlFor="confirmPassword">
                Confirm Password<span className="required">*</span>
              </label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                className="form-input"
                required
              />
            </div>

            <div className="form-buttons">
              <button type="submit" className="signup-btn">Sign Up</button>
              <button type="button" className="signin-btn" onClick={() => onNavigate?.('signin')}>
                Sign In
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default RegisterPage










