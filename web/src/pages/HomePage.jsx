import { useState, useEffect } from 'react'
import './HomePage.css'

function HomePage({ onNavigate }) {
  const [isDarkMode, setIsDarkMode] = useState(true)

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

  const toggleTheme = () => {
    const newTheme = isDarkMode ? 'light' : 'dark'
    setIsDarkMode(!isDarkMode)
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem('theme', newTheme)
  }

  return (
    <div className="home-container">
      {/* Top Navigation */}
      <div className="top-nav">
        <button className="nav-btn" onClick={() => onNavigate?.('public-docs')}>Views Docs</button>
        <button className="nav-btn" onClick={() => onNavigate?.('public-contact')}>Contact</button>
      </div>
      {/* Left Sidebar */}
      <div className="home-sidebar">
        <div>
          <div className="logo-section">
            <h1>Trading Agents</h1>
            <p>Multi-Agents LLM Financial Trading</p>
          </div>

          <div className="features">
            <div className="feature-item">
              <button className="feature-btn">AI Market Analysis</button>
            </div>
            <div className="feature-item">
              <button className="feature-btn">Autonomous Execution</button>
            </div>
            <div className="feature-item">
              <button className="feature-btn">Risk Management</button>
            </div>
            <div className="feature-item">
              <button className="feature-btn">Backtesting Engine</button>
            </div>
            <div className="feature-item">
              <button className="feature-btn">Supported Markets</button>
            </div>
          </div>
        </div>

        <div className="sidebar-actions">
          <button className="register-btn" onClick={() => onNavigate?.('register')}>Register</button>
          <button className="login-btn" onClick={() => onNavigate?.('signin')}>Login</button>
          <div className="theme-toggle-container">
            <label className="theme-toggle">
              <input 
                type="checkbox" 
                checked={isDarkMode}
                onChange={toggleTheme}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>
        </div>
      </div>

      {/* Right Main Content */}
      <div className="home-main-content">
        {/* Globe Background */}
        <div className="globe-background"></div>

        {/* Candlestick Overlay */}
        <div className="candlestick-overlay">
          <div className="candlestick" style={{ top: '10%', left: '15%' }}></div>
          <div className="candlestick red" style={{ top: '20%', left: '25%', height: '20px' }}></div>
          <div className="candlestick" style={{ top: '15%', left: '35%', height: '35px' }}></div>
          <div className="candlestick red" style={{ top: '25%', left: '45%', height: '25px' }}></div>
          <div className="candlestick" style={{ top: '12%', left: '55%', height: '28px' }}></div>
          <div className="candlestick red" style={{ top: '18%', left: '65%', height: '22px' }}></div>
          <div className="candlestick" style={{ top: '22%', left: '75%', height: '32px' }}></div>
          <div className="candlestick red" style={{ top: '14%', left: '85%', height: '18px' }}></div>
        </div>

        {/* Central Icon */}
        <div className="central-icon">
          <div className="icon-circle"></div>
        </div>

        {/* Content Text */}
        <div className="content-text">
          <h2 className="main-headline">ยกระดับการเทรดด้วย AI อัจฉริยะ</h2>
          <p className="subtitle">Multi-Agents LLM Financial Trading</p>
          <p className="description">
            พบกับ Trading Agent ที่ไม่หยุดนิ่งด้วยสถาปัตยกรรม Multi-Agents LLM Financial Trading 
            ระบบของเราไม่ใช่แค่ระบบธรรมดา แต่เป็นเครือข่ายของ Agents อัจฉริยะที่สื่อสาร แลกเปลี่ยนข้อมูล 
            และเรียนรู้จากประสบการณ์การเทรดนับล้านครั้ง การทำงานร่วมกันของ AI เหล่านี้ช่วยให้ Agent ของคุณ 
            ปรับตัว พัฒนากลยุทธ์ และเพิ่มความสามารถในการทำกำไรอย่างต่อเนื่องในทุกสภาวะตลาด
          </p>
        </div>
      </div>
    </div>
  )
}

export default HomePage

