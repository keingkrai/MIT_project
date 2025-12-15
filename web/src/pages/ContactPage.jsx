import { useState } from 'react'
import './ContactPage.css'

const contacts = [
  {
    id: 1,
    name: 'John Doe',
    company: 'Acme Corporation',
    position: 'Senior Manager',
    email: 'john.doe@acme.com',
    phone: '+1 (555) 123-4567',
    other: 'LinkedIn: john-doe'
  },
  {
    id: 2,
    name: 'Jane Smith',
    company: 'Tech Solutions Inc',
    position: 'Product Director',
    email: 'jane.smith@techsolutions.com',
    phone: '+1 (555) 234-5678',
    other: 'Twitter: @janesmith'
  },
  {
    id: 3,
    name: 'Robert Johnson',
    company: 'Global Finance Ltd',
    position: 'CFO',
    email: 'robert.johnson@globalfinance.com',
    phone: '+1 (555) 345-6789',
    other: 'Email preferred'
  }
]

function ContactPage() {
  const [expandedId, setExpandedId] = useState(null)

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id)
  }

  return (
    <div className="contact-page">
      <h1 className="contact-page-title">Contact</h1>
      
      <div className="contact-cards-container">
        {contacts.map((contact) => (
          <div
            key={contact.id}
            className={`contact-card ${expandedId === contact.id ? 'expanded' : ''}`}
            onClick={() => toggleExpand(contact.id)}
          >
            <div className="contact-card-main">
              <div className="contact-avatar">
                <div className="avatar-placeholder"></div>
              </div>
              
              <div className="contact-info">
                <div className="contact-field">
                  <span className="field-label">NAME:</span>
                  <span className="field-value">{contact.name}</span>
                </div>
                
                {expandedId === contact.id ? (
                  <>
                    <div className="contact-field">
                      <span className="field-label">COMPANY:</span>
                      <span className="field-value">{contact.company}</span>
                    </div>
                    <div className="contact-field">
                      <span className="field-label">POSITION:</span>
                      <span className="field-value">{contact.position}</span>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="contact-field">
                      <span className="field-label">EMAIL:</span>
                      <span className="field-value">{contact.email}</span>
                    </div>
                    <div className="contact-field">
                      <span className="field-label">COMPANY:</span>
                      <span className="field-value">{contact.company}</span>
                    </div>
                    <div className="contact-field">
                      <span className="field-label">POSITION:</span>
                      <span className="field-value">{contact.position}</span>
                    </div>
                  </>
                )}
              </div>
            </div>

            {expandedId === contact.id && (
              <div className="contact-details">
                <div className="detail-box">
                  <div className="detail-label">Email</div>
                  <div className="detail-value">{contact.email}</div>
                </div>
                <div className="detail-box">
                  <div className="detail-label">Phone</div>
                  <div className="detail-value">{contact.phone}</div>
                </div>
                <div className="detail-box">
                  <div className="detail-label">Other contact</div>
                  <div className="detail-value">{contact.other}</div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default ContactPage











