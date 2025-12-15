import './DocsPage.css'

const docs = [
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

const downloads = [
  {
    id: 1,
    title: 'Download Document',
    description: 'Learn about how to use our website',
    buttonText: 'Download',
    buttonColor: 'blue'
  }
]

function DocsPage() {
  return (
    <div className="docs-page">
      <h1 className="docs-title">View Docs</h1>
      
      {/* Document & Tutorials Section */}
      <section className="docs-section">
        <h2 className="section-title">Document & Tutorials</h2>
        <div className="docs-cards">
          {docs.map((doc) => (
            <div key={doc.id} className="doc-card">
              <div className="doc-icon">
                <div className="icon-placeholder">📄</div>
              </div>
              <h3 className="doc-card-title">{doc.title}</h3>
              <p className="doc-card-description">{doc.description}</p>
              <button className={`doc-btn ${doc.buttonColor}`}>
                {doc.buttonText}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Download Document Section */}
      <section className="docs-section">
        <h2 className="section-title">Download Document</h2>
        <div className="docs-cards">
          {downloads.map((doc) => (
            <div key={doc.id} className="doc-card">
              <div className="doc-icon">
                <div className="icon-placeholder">📥</div>
              </div>
              <h3 className="doc-card-title">{doc.title}</h3>
              <p className="doc-card-description">{doc.description}</p>
              <button className={`doc-btn ${doc.buttonColor}`}>
                {doc.buttonText}
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

export default DocsPage











