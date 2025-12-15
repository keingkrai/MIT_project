import { useState } from 'react'
import { WebSocketProvider } from './contexts/WebSocketContext'
import { AnalysisProvider } from './contexts/AnalysisContext'
import Sidebar from './components/Sidebar'
import HomePage from './pages/HomePage'
import GeneratePage from './pages/GeneratePage'
import DebugPage from './pages/DebugPage'
import RegisterPage from './pages/RegisterPage'
import LoginPage from './pages/LoginPage'
import ContactPage from './pages/ContactPage'
import PublicContactPage from './pages/PublicContactPage'
import DocsPage from './pages/DocsPage'
import PublicDocsPage from './pages/PublicDocsPage'

function App() {
  const [currentPage, setCurrentPage] = useState('home')

  // Home page and Register page have their own layouts, so don't show the sidebar
  if (currentPage === 'home') {
    return (
      <WebSocketProvider>
        <AnalysisProvider>
          <HomePage onNavigate={setCurrentPage} />
        </AnalysisProvider>
      </WebSocketProvider>
    )
  }

  // Public contact page (from HomePage navigation)
  if (currentPage === 'public-contact') {
    return (
      <WebSocketProvider>
        <AnalysisProvider>
          <PublicContactPage onNavigate={setCurrentPage} />
        </AnalysisProvider>
      </WebSocketProvider>
    )
  }

  // Public docs page (from HomePage navigation)
  if (currentPage === 'public-docs') {
    return (
      <WebSocketProvider>
        <AnalysisProvider>
          <PublicDocsPage onNavigate={setCurrentPage} />
        </AnalysisProvider>
      </WebSocketProvider>
    )
  }

  if (currentPage === 'register') {
    return (
      <WebSocketProvider>
        <AnalysisProvider>
          <RegisterPage onNavigate={setCurrentPage} />
        </AnalysisProvider>
      </WebSocketProvider>
    )
  }

  if (currentPage === 'signin') {
    return (
      <WebSocketProvider>
        <AnalysisProvider>
          <LoginPage onNavigate={setCurrentPage} />
        </AnalysisProvider>
      </WebSocketProvider>
    )
  }

  return (
    <WebSocketProvider>
      <AnalysisProvider>
        <div className="app-shell">
          <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />
          <main className="main">
            <div style={{ display: currentPage === 'generate' ? 'block' : 'none' }}>
              <GeneratePage />
            </div>
            <div style={{ display: currentPage === 'contact' ? 'block' : 'none' }}>
              <ContactPage />
            </div>
            <div style={{ display: currentPage === 'docs' ? 'block' : 'none' }}>
              <DocsPage />
            </div>
            <div style={{ display: currentPage === 'debug' ? 'block' : 'none' }}>
              <DebugPage />
            </div>
          </main>
        </div>
      </AnalysisProvider>
    </WebSocketProvider>
  )
}

export default App

