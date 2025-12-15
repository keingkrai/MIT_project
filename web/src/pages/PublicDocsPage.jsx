import { useState, useEffect } from 'react'
import './PublicDocsPage.css'

const publicDocs = [
  {
    id: 1,
    title: 'Document',
    description: 'Learn about how to use our website',
    buttonText: 'Get Start',
    buttonColor: 'green'
  },
  {
    id: 2,
    title: 'Tutorials',
    description: 'Learn about how to use our website',
    buttonText: 'Get Start',
    buttonColor: 'green'
  },
  {
    id: 3,
    title: 'Learn about our Agent',
    description: 'Learn about how to use our website',
    buttonText: 'Get Start',
    buttonColor: 'green'
  }
]

const publicDownloads = [
  {
    id: 1,
    title: 'Download Document',
    description: 'Learn about how to use our website',
    buttonText: 'Download',
    buttonColor: 'blue'
  }
]

function PublicDocsPage({ onNavigate }) {
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

  return (
    <div className="public-docs-page">
      <button className="back-link" onClick={() => onNavigate?.('home')}>
        ← Back to Home
      </button>
      
      <h1 className="public-docs-title">View Docs</h1>
      
      {/* Document & Tutorials Section */}
      <section className="public-docs-section">
        <h2 className="public-section-title">Document & Tutorials</h2>
        <div className="public-docs-cards">
          {publicDocs.map((doc) => (
            <div key={doc.id} className="public-doc-card">
              <div className="public-doc-icon">
                <div className="public-icon-placeholder">📄</div>
              </div>
              <h3 className="public-doc-card-title">{doc.title}</h3>
              <p className="public-doc-card-description">{doc.description}</p>
              <button className={`public-doc-btn ${doc.buttonColor}`}>
                {doc.buttonText}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Download Document Section */}
      <section className="public-docs-section">
        <h2 className="public-section-title">Download Document</h2>
        <div className="public-docs-cards">
          {publicDownloads.map((doc) => (
            <div key={doc.id} className="public-doc-card">
              <div className="public-doc-icon">
                <div className="public-icon-placeholder">📥</div>
              </div>
              <h3 className="public-doc-card-title">{doc.title}</h3>
              <p className="public-doc-card-description">{doc.description}</p>
              <button className={`public-doc-btn ${doc.buttonColor}`}>
                {doc.buttonText}
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

export default PublicDocsPage











