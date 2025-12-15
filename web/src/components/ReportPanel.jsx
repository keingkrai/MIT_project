import { useState, useEffect } from 'react'
import { jsPDF } from 'jspdf'

function ReportPanel({ reportSections, reportView, setReportView, ticker, analysisDate, reportLength, teamState }) {
  const [copyButtonText, setCopyButtonText] = useState('Copy report')
  const [outputReports, setOutputReports] = useState([])
  const [loadingReports, setLoadingReports] = useState(false)

  // Fetch reports from output folder based on reportLength
  useEffect(() => {
    const fetchReports = async () => {
      setLoadingReports(true)
      try {
        // Determine API URL
        const isDevelopment = import.meta.env.DEV
        let apiUrl
        if (window.location.protocol === 'file:' || window.location.hostname === '') {
          apiUrl = 'http://localhost:8000'
        } else if (isDevelopment) {
          apiUrl = `${window.location.protocol}//${window.location.host}`
        } else {
          apiUrl = `${window.location.protocol}//${window.location.host}`
        }

        const response = await fetch(`${apiUrl}/api/reports?report_length=${reportLength}`)
        if (response.ok) {
          const data = await response.json()
          if (data.success && data.reports) {
            // Convert reports object to array format
            const reportsArray = Object.entries(data.reports).map(([label, text]) => ({
              key: label.toLowerCase().replace(/\s+/g, '_'),
              label: label,
              text: text
            }))
            setOutputReports(reportsArray)
          }
        }
      } catch (error) {
        console.error('Error fetching reports from output:', error)
      } finally {
        setLoadingReports(false)
      }
    }

    fetchReports()
  }, [reportLength])

  // Check if all teams have completed
  const areAllTeamsCompleted = () => {
    if (!teamState) return false
    
    const allTeams = [
      teamState.analyst,
      teamState.research,
      teamState.trader,
      teamState.risk,
      teamState.portfolio,
    ].filter(Boolean) // Filter out undefined teams

    if (allTeams.length === 0) return false

    return allTeams.every((team) => {
      if (!team || team.length === 0) return true
      return team.every((member) => member.status === 'completed')
    })
  }

  const formatInlineMarkdown = (text) => {
    return escapeHtml(text).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  }

  const escapeHtml = (text) => {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  }

  const convertMarkdownToDom = (markdownText) => {
    const lines = markdownText.split('\n')
    const elements = []
    let currentList = null

    lines.forEach((line) => {
      const trimmed = line.trim()
      if (!trimmed) {
        currentList = null
        return
      }
      if (/^[-*]/.test(trimmed)) {
        if (!currentList) {
          currentList = []
          elements.push({ type: 'list', items: currentList })
        }
        currentList.push(formatInlineMarkdown(trimmed.replace(/^[-*]\s*/, '')))
      } else {
        currentList = null
        elements.push({ type: 'paragraph', text: formatInlineMarkdown(trimmed) })
      }
    })

    return elements
  }

  const summarizeSection = (text) => {
    if (!text) return ''

    const lines = text.split('\n')
    const summary = []
    let currentSection = null
    let currentContent = []

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim()
      if (!line) continue

      const isHeader =
        (line.match(/^[A-Z][A-Za-z\s]+$/) &&
          line.length < 80 &&
          !line.includes('.') &&
          !line.includes(',')) ||
        line.match(/^#{1,6}\s/) ||
        (line.endsWith(':') && line.length < 60)

      if (isHeader && !line.startsWith('•') && !line.startsWith('-') && !line.startsWith('*')) {
        if (currentSection) {
          summary.push(currentSection)
          const keyPoints = extractKeyPoints(currentContent.join(' '))
          if (keyPoints.length > 0) {
            summary.push(...keyPoints.slice(0, 3))
            summary.push('')
          }
        }
        currentSection = line.replace(/^#+\s*/, '').replace(':', '')
        currentContent = []
      } else if (currentSection) {
        currentContent.push(line)
      } else {
        currentContent.push(line)
      }
    }

    if (currentSection) {
      summary.push(currentSection)
      const keyPoints = extractKeyPoints(currentContent.join(' '))
      if (keyPoints.length > 0) {
        summary.push(...keyPoints.slice(0, 3))
      }
    } else if (currentContent.length > 0) {
      const keyPoints = extractKeyPoints(currentContent.join(' '))
      summary.push(...keyPoints.slice(0, 3))
    }

    return summary.join('\n')
  }

  const extractKeyPoints = (text) => {
    const keyPoints = []
    const bulletMatches = text.match(/[-*•·]\s*([^\n]+)/g)
    if (bulletMatches) {
      bulletMatches.slice(0, 3).forEach((match) => {
        const point = match.replace(/^[-*•·]\s*/, '• ').trim()
        if (point.length > 10 && point.length < 200) {
          keyPoints.push(point)
        }
      })
    }

    if (keyPoints.length === 0) {
      const sentences = text.split(/[.!?]+/).filter((s) => {
        const trimmed = s.trim()
        return trimmed.length > 30 && trimmed.length < 250
      })

      const importantTerms = [
        'buy',
        'sell',
        'hold',
        'recommend',
        'price',
        'target',
        'risk',
        'opportunity',
        'trend',
        'analysis',
      ]
      const scoredSentences = sentences
        .map((s) => {
          const lower = s.toLowerCase()
          const score = importantTerms.reduce((acc, term) => acc + (lower.includes(term) ? 1 : 0), 0)
          return { text: s.trim(), score }
        })
        .sort((a, b) => b.score - a.score)

      scoredSentences.slice(0, 2).forEach((item) => {
        if (item.text) {
          keyPoints.push(item.text + '.')
        }
      })
    }

    return keyPoints
  }

  const copyReportToClipboard = async () => {
    const reportsToUse = outputReports.length > 0 ? outputReports : reportSections
    const fullText = reportsToUse.map((section) => `${section.label}\n${section.text}`).join('\n\n')
    if (!fullText) return
    try {
      await navigator.clipboard.writeText(fullText)
      setCopyButtonText('Copied!')
      setTimeout(() => setCopyButtonText('Copy report'), 1800)
    } catch (error) {
      setCopyButtonText('Copy failed')
      setTimeout(() => setCopyButtonText('Copy report'), 1800)
    }
  }

  const downloadReportAsPdf = () => {
    const reportsToUse = outputReports.length > 0 ? outputReports : reportSections
    
    // Use reportView to determine if we should use summary or full report
    // If reportView is 'short', use summarized version, otherwise use full
    let reportForPdf
    if (reportView === 'short') {
      // Use summarized version
      reportForPdf = reportsToUse
        .map((section) => `${section.label}\n${summarizeSection(section.text)}`)
        .join('\n\n')
    } else {
      // Use full version
      reportForPdf = reportsToUse
        .map((section) => `${section.label}\n${section.text}`)
        .join('\n\n')
    }
    
    if (!reportForPdf) return

    const doc = new jsPDF({ unit: 'pt', format: 'a4' })
    const pageWidth = doc.internal.pageSize.getWidth()
    const pageHeight = doc.internal.pageSize.getHeight()
    const margin = 40
    const maxWidth = pageWidth - margin * 2
    const lineHeight = 14

    let yPosition = margin + 20

    doc.setFontSize(16)
    doc.setFont(undefined, 'bold')
    doc.text(`TradingAgents Report: ${ticker}`, margin, yPosition)
    yPosition += 20

    doc.setFontSize(10)
    doc.setFont(undefined, 'normal')
    doc.text(`Analysis Date: ${analysisDate}`, margin, yPosition)
    yPosition += 30

    doc.line(margin, yPosition, pageWidth - margin, yPosition)
    yPosition += 25

    doc.setFontSize(14)
    doc.setFont(undefined, 'bold')
    doc.text(`Current Report (${reportView === 'short' ? 'Summary Report' : 'Full Report'} Format)`, margin, yPosition)
    yPosition += 20

    doc.setFontSize(10)
    doc.setFont(undefined, 'normal')

    const reportLines = doc.splitTextToSize(reportForPdf, maxWidth)

    for (let i = 0; i < reportLines.length; i++) {
      const line = reportLines[i]

      if (yPosition > pageHeight - margin - lineHeight) {
        doc.addPage()
        yPosition = margin
      }

      if (line.trim().match(/^[A-Z][A-Z\s:]+$/) && line.trim().length < 80) {
        yPosition += 5
        if (yPosition > pageHeight - margin - lineHeight) {
          doc.addPage()
          yPosition = margin
        }
        doc.setFontSize(11)
        doc.setFont(undefined, 'bold')
        doc.text(line.trim(), margin, yPosition)
        doc.setFontSize(10)
        doc.setFont(undefined, 'normal')
        yPosition += lineHeight + 3
      } else if (line.trim().startsWith('RECOMMENDATION:')) {
        yPosition += 10
        if (yPosition > pageHeight - margin - lineHeight) {
          doc.addPage()
          yPosition = margin
        }
        doc.setFontSize(12)
        doc.setFont(undefined, 'bold')
        doc.text(line.trim(), margin, yPosition)
        doc.setFontSize(10)
        doc.setFont(undefined, 'normal')
        yPosition += lineHeight + 5
      } else {
        doc.text(line, margin, yPosition)
        yPosition += lineHeight
      }
    }

    const totalPages = doc.internal.pages.length - 1
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i)
      doc.setFontSize(8)
      doc.text(`Page ${i} of ${totalPages}`, pageWidth / 2, pageHeight - 20, { align: 'center' })
    }

    doc.save(`TradingAgents-${ticker}-${analysisDate}.pdf`)
  }

  const renderReportContent = () => {
    // Use output reports if available, otherwise use WebSocket reportSections
    const reportsToDisplay = outputReports.length > 0 ? outputReports : reportSections

    if (loadingReports) {
      return (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px 20px',
          color: 'var(--text-muted)'
        }}>
          <p style={{ fontSize: '1.1rem' }}>
            ⏳ Loading reports from output folder...
          </p>
        </div>
      )
    }

    // If using output reports, show them directly (no need to wait for teams)
    if (outputReports.length > 0) {
      return reportsToDisplay.map((section, index) => {
        const displayText = reportView === 'short' ? summarizeSection(section.text) : section.text
        const elements = convertMarkdownToDom(displayText)

        return (
          <div key={index} className="report-block">
            <h3>{section.label}</h3>
            <div className="report-body">
              {elements.map((el, idx) => {
                if (el.type === 'list') {
                  return (
                    <ul key={idx} className="report-list">
                      {el.items.map((item, itemIdx) => (
                        <li key={itemIdx} dangerouslySetInnerHTML={{ __html: item }} />
                      ))}
                    </ul>
                  )
                } else {
                  return <p key={idx} dangerouslySetInnerHTML={{ __html: el.text }} />
                }
              })}
            </div>
          </div>
        )
      })
    }

    // Fallback to WebSocket reports (original behavior)
    // Check if all teams are completed
    if (!areAllTeamsCompleted()) {
      return (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px 20px',
          color: 'var(--text-muted)'
        }}>
          <p style={{ fontSize: '1.1rem', marginBottom: '12px' }}>
            ⏳ Waiting for all teams to complete...
          </p>
          <p style={{ fontSize: '0.9rem' }}>
            The report will be displayed once all teams finish their analysis.
          </p>
        </div>
      )
    }

    if (reportSections.length === 0) {
      return <p>Run the pipeline to load the latest markdown report.</p>
    }

    return reportSections.map((section, index) => {
      const displayText = reportView === 'short' ? summarizeSection(section.text) : section.text
      const elements = convertMarkdownToDom(displayText)

      return (
        <div key={index} className="report-block">
          <h3>{section.label}</h3>
          <div className="report-body">
            {elements.map((el, idx) => {
              if (el.type === 'list') {
                return (
                  <ul key={idx} className="report-list">
                    {el.items.map((item, itemIdx) => (
                      <li key={itemIdx} dangerouslySetInnerHTML={{ __html: item }} />
                    ))}
                  </ul>
                )
              } else {
                return <p key={idx} dangerouslySetInnerHTML={{ __html: el.text }} />
              }
            })}
          </div>
        </div>
      )
    })
  }

  return (
    <section className="report-panel">
      <header>
        <div>
          <p>Current Report</p>
          <small>Live updates from TradingAgents graph</small>
        </div>
        <div className="report-actions">
          <div className="report-view-toggle">
            <button
              className={`report-view-btn ${reportView === 'short' ? 'active' : ''}`}
              onClick={() => setReportView('short')}
            >
              Summary Report
            </button>
            <button
              className={`report-view-btn ${reportView === 'long' ? 'active' : ''}`}
              onClick={() => setReportView('long')}
            >
              Full Report
            </button>
          </div>
          <button onClick={copyReportToClipboard}>{copyButtonText}</button>
          <button className="ghost" onClick={downloadReportAsPdf}>
            Download PDF
          </button>
        </div>
      </header>
      <article id="report-content">{renderReportContent()}</article>
    </section>
  )
}

export default ReportPanel

