import { useState, useEffect } from 'react'
import './PublicContactPage.css'

const publicContacts = [
  {
    id: 1,
    name: 'Support Team',
    company: 'Trading Agents',
    position: 'Customer Support',
    email: 'support@tradingagents.com',
    phone: '+1 (555) 000-0001',
    other: 'Available 24/7'
  },
  {
    id: 2,
    name: 'General Inquiries',
    company: 'Trading Agents',
    position: 'Information Desk',
    email: 'info@tradingagents.com',
    phone: '+1 (555) 000-0002',
    other: 'General questions and information'
  },
  {
    id: 3,
    name: 'Business Relations',
    company: 'Trading Agents',
    position: 'Business Development',
    email: 'business@tradingagents.com',
    phone: '+1 (555) 000-0003',
    other: 'Partnerships and collaborations'
  }
]

function PublicContactPage({ onNavigate }) {
  const [isDarkMode, setIsDarkMode] = useState(true)
  const [expandedId, setExpandedId] = useState(null)

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

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id)
  }

  return (
    <div className="public-contact-page">
      <button className="back-link" onClick={() => onNavigate?.('home')}>
        ← Back to Home
      </button>
      
      <h1 className="public-contact-title">Contact</h1>
      
      <div className="public-contact-cards-container">
        {publicContacts.map((contact) => (
          <div
            key={contact.id}
            className={`public-contact-card ${expandedId === contact.id ? 'expanded' : ''}`}
            onClick={() => toggleExpand(contact.id)}
          >
            <div className="public-contact-card-main">
              <div className="public-contact-avatar">
                <div className="public-avatar-placeholder"></div>
              </div>
              
              <div className="public-contact-info">
                <div className="public-contact-field">
                  <span className="public-field-label">NAME:</span>
                  <span className="public-field-value">{contact.name}</span>
                </div>
                
                {expandedId === contact.id ? (
                  <>
                    <div className="public-contact-field">
                      <span className="public-field-label">COMPANY:</span>
                      <span className="public-field-value">{contact.company}</span>
                    </div>
                    <div className="public-contact-field">
                      <span className="public-field-label">POSITION:</span>
                      <span className="public-field-value">{contact.position}</span>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="public-contact-field">
                      <span className="public-field-label">EMAIL:</span>
                      <span className="public-field-value">{contact.email}</span>
                    </div>
                    <div className="public-contact-field">
                      <span className="public-field-label">COMPANY:</span>
                      <span className="public-field-value">{contact.company}</span>
                    </div>
                    <div className="public-contact-field">
                      <span className="public-field-label">POSITION:</span>
                      <span className="public-field-value">{contact.position}</span>
                    </div>
                  </>
                )}
              </div>
            </div>

            {expandedId === contact.id && (
              <div className="public-contact-details">
                <div className="public-detail-box">
                  <div className="public-detail-label">Email</div>
                  <div className="public-detail-value">{contact.email}</div>
                </div>
                <div className="public-detail-box">
                  <div className="public-detail-label">Phone</div>
                  <div className="public-detail-value">{contact.phone}</div>
                </div>
                <div className="public-detail-box">
                  <div className="public-detail-label">Other contact</div>
                  <div className="public-detail-value">{contact.other}</div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default PublicContactPage











