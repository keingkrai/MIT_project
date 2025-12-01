"use strict";

(() => {
  const analystsData = [
    { label: "Market Analyst", value: "market" },
    { label: "Social Media Analyst", value: "social" },
    { label: "News Analyst", value: "news" },
    { label: "Fundamentals Analyst", value: "fundamentals" },
  ];

  const researchDepthOptions = [
    {
      label: "Shallow",
      helper: "Quick research, single debate loop",
      value: 1,
    },
    {
      label: "Medium",
      helper: "Balanced debate and risk review",
      value: 3,
    },
    {
      label: "Deep",
      helper: "Comprehensive discussions + full risk audits",
      value: 5,
    },
  ];

  const llmProviders = [
    { id: "google", label: "Google", url: "https://generativelanguage.googleapis.com/v1" },
  ];

  const shallowAgents = {
    google: [
      ["Gemini 2.0 Flash-Lite • low latency", "gemini-2.0-flash-lite"],
      ["Gemini 2.0 Flash • next-gen speed", "gemini-2.0-flash"],
      ["Gemini 2.5 Flash • adaptive", "gemini-2.5-flash-preview-05-20"],
    ],
  };

  const deepAgents = {
    google: [
      ["Gemini 2.0 Flash-Lite", "gemini-2.0-flash-lite"],
      ["Gemini 2.0 Flash", "gemini-2.0-flash"],
      ["Gemini 2.5 Flash", "gemini-2.5-flash-preview-05-20"],
      ["Gemini 2.5 Pro", "gemini-2.5-pro-preview-06-05"],
    ],
  };

  const teamTemplate = {
    analyst: [
      { name: "Market Analyst", status: "pending" },
      { name: "Social Media Analyst", status: "pending" },
      { name: "News Analyst", status: "pending" },
      { name: "Fundamentals Analyst", status: "pending" },
    ],
    research: [
      { name: "Bull Research", status: "pending" },
      { name: "Bear Research", status: "pending" },
      { name: "Research Manager", status: "pending" },
    ],
    trader: [{ name: "Trader", status: "pending" }],
    risk: [
      { name: "Risk Analyst", status: "pending" },
      { name: "Neutral Analyst", status: "pending" },
      { name: "Safe Analyst", status: "pending" },
      { name: "Portfolio Manager", status: "pending" },
    ],
  };

  const reportSources = [
    {
      key: "market",
      label: "Market Analysis",
      path: "../results/AAPL/2025-11-25/reports/market_report.md",
    },
    {
      key: "sentiment",
      label: "Social Sentiment",
      path: "../results/AAPL/2025-11-25/reports/sentiment_report.md",
    },
    {
      key: "news",
      label: "News Analysis",
      path: "../results/AAPL/2025-11-25/reports/news_report.md",
    },
    {
      key: "fundamentals",
      label: "Fundamentals Review",
      path: "../results/AAPL/2025-11-25/reports/fundamentals_report.md",
    },
    {
      key: "trader",
      label: "Trader Investment Plan",
      path: "../results/AAPL/2025-11-25/reports/trader_investment_plan.md",
    },
    {
      key: "final",
      label: "Portfolio Management Decision",
      path: "../results/AAPL/2025-11-25/reports/final_trade_decision.md",
    },
  ];

  const elements = {
    tickerInput: document.getElementById("ticker-input"),
    analysisDate: document.getElementById("analysis-date"),
    headerDate: document.getElementById("header-date"),
    analystGrid: document.getElementById("analyst-grid"),
    depthOptions: document.getElementById("depth-options"),
    providerSelect: document.getElementById("llm-provider"),
    backendUrl: document.getElementById("backend-url"),
    shallowSelect: document.getElementById("shallow-agent"),
    deepSelect: document.getElementById("deep-agent"),
    generateBtn: document.getElementById("generate-btn"),
    reportContent: document.getElementById("report-content"),
    copyBtn: document.getElementById("copy-report"),
    downloadBtn: document.getElementById("download-report"),
    summarySymbol: document.getElementById("summary-symbol"),
    summaryDate: document.getElementById("summary-date"),
    summaryDepth: document.getElementById("summary-depth"),
    summaryDecision: document.getElementById("summary-decision"),
    recommendationCard: document.querySelector(".recommendation"),
    // Debug panel elements
    debugToggle: document.getElementById("debug-toggle"),
    debugContent: document.getElementById("debug-content"),
    debugPanel: document.querySelector(".debug-panel"),
    debugWsStatus: document.getElementById("debug-ws-status"),
    debugWsUrl: document.getElementById("debug-ws-url"),
    debugMsgCount: document.getElementById("debug-msg-count"),
    debugLastUpdate: document.getElementById("debug-last-update"),
    debugLastType: document.getElementById("debug-last-type"),
    debugErrorCount: document.getElementById("debug-error-count"),
    debugLog: document.getElementById("debug-log"),
    debugClear: document.getElementById("debug-clear"),
    debugCopy: document.getElementById("debug-copy"),
  };

  const state = {
    ticker: "SPY",
    analysisDate: toISODate(),
    analysts: new Set(analystsData.map((item) => item.value)),
    researchDepth: researchDepthOptions[1].value,
    llmProvider: "google",
    backendUrl: "https://generativelanguage.googleapis.com/v1",
    shallowModel: shallowAgents.google[0][1],
    deepModel: deepAgents.google[0][1],
    isRunning: false,
    reportPlainText: "",
  };
  let teamState = deepClone(teamTemplate);
  
  // Debug state
  const debugState = {
    wsConnected: false,
    wsUrl: "",
    messageCount: 0,
    errorCount: 0,
    lastUpdate: null,
    lastType: null,
    logEntries: [],
    maxLogEntries: 50,
  };

  init();

  function init() {
    hydrateDates();
    renderAnalysts();
    renderDepthOptions();
    renderProviders();
    populateAgentSelects();
    renderAllTeamCards();
    updateSummary();
    setRecommendation("Awaiting run");
    initDebugPanel();
    bindEvents();
  }
  
  function initDebugPanel() {
    // Toggle debug panel
    if (elements.debugToggle) {
      elements.debugToggle.addEventListener("click", () => {
        elements.debugPanel.classList.toggle("collapsed");
        const toggleSpan = elements.debugToggle.querySelector("span");
        if (elements.debugPanel.classList.contains("collapsed")) {
          toggleSpan.textContent = "▶";
        } else {
          toggleSpan.textContent = "▼";
        }
      });
    }
    
    // Clear log button
    if (elements.debugClear) {
      elements.debugClear.addEventListener("click", () => {
        debugState.logEntries = [];
        debugState.messageCount = 0;
        debugState.errorCount = 0;
        updateDebugDisplay();
      });
    }
    
    // Copy log button
    if (elements.debugCopy) {
      elements.debugCopy.addEventListener("click", async () => {
        const logText = debugState.logEntries
          .map(entry => `[${entry.time}] [${entry.type}] ${entry.content}`)
          .join("\n");
        try {
          await navigator.clipboard.writeText(logText);
          elements.debugCopy.textContent = "Copied!";
          setTimeout(() => {
            elements.debugCopy.textContent = "Copy Log";
          }, 2000);
        } catch (error) {
          console.error("Failed to copy log:", error);
        }
      });
    }
    
    updateDebugDisplay();
  }
  
  function updateDebugDisplay() {
    // Update WebSocket status
    if (elements.debugWsStatus) {
      const statusIndicator = elements.debugWsStatus.querySelector(".status-indicator");
      const statusText = elements.debugWsStatus.querySelector("span:last-child");
      
      if (debugState.wsConnected) {
        statusIndicator.className = "status-indicator connected";
        statusText.textContent = "Connected";
      } else if (state.isRunning) {
        statusIndicator.className = "status-indicator connecting";
        statusText.textContent = "Connecting...";
      } else {
        statusIndicator.className = "status-indicator disconnected";
        statusText.textContent = "Disconnected";
      }
    }
    
    // Update URL
    if (elements.debugWsUrl) {
      elements.debugWsUrl.textContent = debugState.wsUrl || "—";
    }
    
    // Update counts
    if (elements.debugMsgCount) {
      elements.debugMsgCount.textContent = debugState.messageCount;
    }
    
    if (elements.debugErrorCount) {
      elements.debugErrorCount.textContent = debugState.errorCount;
    }
    
    // Update last update time
    if (elements.debugLastUpdate) {
      if (debugState.lastUpdate) {
        const time = new Date(debugState.lastUpdate).toLocaleTimeString();
        elements.debugLastUpdate.textContent = time;
      } else {
        elements.debugLastUpdate.textContent = "—";
      }
    }
    
    // Update last type
    if (elements.debugLastType) {
      elements.debugLastType.textContent = debugState.lastType || "—";
    }
    
    // Update log display
    if (elements.debugLog) {
      if (debugState.logEntries.length === 0) {
        elements.debugLog.innerHTML = '<div class="debug-log-empty">No messages yet</div>';
      } else {
        elements.debugLog.innerHTML = debugState.logEntries
          .slice(-debugState.maxLogEntries)
          .map(entry => {
            const entryClass = entry.type === "error" ? "error" : 
                              entry.type === "warning" ? "warning" : "";
            return `
              <div class="debug-log-entry ${entryClass}">
                <span class="debug-log-entry-time">${entry.time}</span>
                <span class="debug-log-entry-type">[${entry.type}]</span>
                <span class="debug-log-entry-content">${escapeHtml(entry.content.substring(0, 100))}${entry.content.length > 100 ? "..." : ""}</span>
              </div>
            `;
          })
          .join("");
        // Scroll to bottom
        elements.debugLog.scrollTop = elements.debugLog.scrollHeight;
      }
    }
  }
  
  function addDebugLog(type, content, isError = false) {
    const time = new Date().toLocaleTimeString();
    debugState.logEntries.push({
      time,
      type,
      content: String(content),
    });
    
    // Keep only last N entries
    if (debugState.logEntries.length > debugState.maxLogEntries) {
      debugState.logEntries.shift();
    }
    
    debugState.messageCount++;
    debugState.lastUpdate = new Date().toISOString();
    debugState.lastType = type;
    
    if (isError) {
      debugState.errorCount++;
    }
    
    updateDebugDisplay();
  }
  
  function updateDebugWsStatus(connected, url = "") {
    debugState.wsConnected = connected;
    if (url) {
      debugState.wsUrl = url;
    }
    updateDebugDisplay();
  }

  function hydrateDates() {
    const today = toISODate();
    elements.analysisDate.value = today;
    elements.headerDate.value = today;
  }

  function renderAnalysts() {
    elements.analystGrid.innerHTML = "";
    analystsData.forEach((analyst) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = `chip ${
        state.analysts.has(analyst.value) ? "selected" : ""
      }`;
      chip.textContent = analyst.label;
      chip.dataset.value = analyst.value;
      chip.addEventListener("click", () => toggleAnalyst(analyst.value));
      elements.analystGrid.appendChild(chip);
    });
  }

  function renderDepthOptions() {
    elements.depthOptions.innerHTML = "";
    researchDepthOptions.forEach((option) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `depth-option ${
        option.value === state.researchDepth ? "active" : ""
      }`;
      button.innerHTML = `<strong>${option.label}</strong><span>${option.helper}</span>`;
      button.addEventListener("click", () => {
        state.researchDepth = option.value;
        renderDepthOptions();
        updateSummary();
      });
      elements.depthOptions.appendChild(button);
    });
  }

  function renderProviders() {
    elements.providerSelect.innerHTML = "";
    llmProviders.forEach((provider) => {
      const option = document.createElement("option");
      option.value = provider.id;
      option.textContent = provider.label;
      if (provider.id === state.llmProvider) {
        option.selected = true;
      }
      elements.providerSelect.appendChild(option);
    });
    elements.backendUrl.textContent = state.backendUrl;
  }

  function populateAgentSelects() {
    populateAgentSelect(
      elements.shallowSelect,
      shallowAgents[state.llmProvider],
      state.shallowModel,
      (value) => {
        state.shallowModel = value;
      }
    );
    populateAgentSelect(
      elements.deepSelect,
      deepAgents[state.llmProvider],
      state.deepModel,
      (value) => {
        state.deepModel = value;
      }
    );
  }

  function populateAgentSelect(selectElement, options, selectedValue, onChange) {
    selectElement.innerHTML = "";
    options.forEach(([label, value]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      if (value === selectedValue) {
        option.selected = true;
      }
      selectElement.appendChild(option);
    });
    selectElement.onchange = (event) => onChange(event.target.value);
  }

  function bindEvents() {
    elements.tickerInput.addEventListener("input", (event) => {
      const ticker = event.target.value.trim().toUpperCase();
      state.ticker = ticker || "SPY";
      updateSummary();
    });

    elements.analysisDate.addEventListener("change", (event) => {
      const value = event.target.value || toISODate();
      state.analysisDate = value;
      elements.headerDate.value = value;
      updateSummary();
    });

    elements.headerDate.addEventListener("change", (event) => {
      const value = event.target.value || toISODate();
      state.analysisDate = value;
      elements.analysisDate.value = value;
      updateSummary();
    });

    elements.providerSelect.addEventListener("change", (event) => {
      const providerId = event.target.value;
      state.llmProvider = providerId;
      const provider = llmProviders.find((item) => item.id === providerId);
      state.backendUrl = provider ? provider.url : "";
      elements.backendUrl.textContent = state.backendUrl;
      state.shallowModel = shallowAgents[providerId][0][1];
      state.deepModel = deepAgents[providerId][0][1];
      populateAgentSelects();
      updateSummary();
    });

    elements.generateBtn.addEventListener("click", runPipeline);
    elements.copyBtn.addEventListener("click", copyReportToClipboard);
    elements.downloadBtn.addEventListener("click", downloadReportAsPdf);
  }

  function toggleAnalyst(analystValue) {
    if (state.analysts.has(analystValue) && state.analysts.size === 1) {
      return;
    }
    if (state.analysts.has(analystValue)) {
      state.analysts.delete(analystValue);
    } else {
      state.analysts.add(analystValue);
    }
    renderAnalysts();
    updateSummary();
  }

  function renderAllTeamCards() {
    Object.keys(teamState).forEach(renderTeamCard);
  }

  function renderTeamCard(teamKey) {
    const card = document.querySelector(`.team-card[data-team="${teamKey}"]`);
    if (!card) return;
    const members = teamState[teamKey];
    const list = card.querySelector(".team-list");
    list.innerHTML = "";
    members.forEach((member) => {
      const li = document.createElement("li");
      const label = document.createElement("span");
      label.textContent = member.name;
      const status = document.createElement("span");
      status.className = `status-pill ${member.status}`;
      status.textContent = member.status.replace("_", " ");
      li.appendChild(label);
      li.appendChild(status);
      list.appendChild(li);
    });
    const completed =
      (members.filter((member) => member.status === "completed").length /
        members.length) *
      100;
    updateProgressRing(card, Math.round(completed));
  }

  function updateProgressRing(card, percentage) {
    const ring = card.querySelector(".progress-ring");
    if (!ring) return;
    const degrees = (percentage / 100) * 360;
    ring.style.background = `conic-gradient(var(--accent) ${degrees}deg, rgba(255,255,255,0.08) 0deg)`;
    const label = ring.querySelector("span");
    if (label) label.textContent = `${percentage}%`;
  }

  function updateSummary() {
    elements.summarySymbol.textContent = state.ticker;
    elements.summaryDate.textContent = state.analysisDate;
    const depth = researchDepthOptions.find(
      (option) => option.value === state.researchDepth
    );
    elements.summaryDepth.textContent = depth ? depth.label : "—";
  }

  async function runPipeline() {
    if (state.isRunning) return;
    state.isRunning = true;
    elements.generateBtn.disabled = true;
    elements.generateBtn.textContent = "Running…";
    teamState = deepClone(teamTemplate);
    renderAllTeamCards();
    
    // Clear previous reports
    elements.reportContent.innerHTML = "<p>Starting analysis...</p>";
    state.reportPlainText = "";
    
    // Determine WebSocket URL
    // If running from file:// or different port, default to localhost:8000
    let wsUrl;
    if (window.location.protocol === "file:" || window.location.hostname === "") {
      // Running from file system, use localhost
      wsUrl = "ws://localhost:8000/ws";
    } else {
      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsHost = window.location.hostname;
      const wsPort = window.location.port || (window.location.protocol === "https:" ? "443" : "8000");
      wsUrl = `${wsProtocol}//${wsHost}:${wsPort}/ws`;
    }
    
    try {
      const ws = new WebSocket(wsUrl);
      
      // Map backend agent names to frontend team structure
      const agentToTeamMap = {
        "Market Analyst": ["analyst", "Market Analyst"],
        "Social Analyst": ["analyst", "Social Media Analyst"],
        "News Analyst": ["analyst", "News Analyst"],
        "Fundamentals Analyst": ["analyst", "Fundamentals Analyst"],
        "Bull Researcher": ["research", "Bull Research"],
        "Bear Researcher": ["research", "Bear Research"],
        "Research Manager": ["research", "Research Manager"],
        "Trader": ["trader", "Trader"],
        "Risky Analyst": ["risk", "Risk Analyst"],
        "Neutral Analyst": ["risk", "Neutral Analyst"],
        "Safe Analyst": ["risk", "Safe Analyst"],
        "Portfolio Manager": ["risk", "Portfolio Manager"],
      };
      
      // Store report sections
      const reportSections = [];
      
      ws.onopen = () => {
        console.log("WebSocket connected");
        updateDebugWsStatus(true, wsUrl);
        addDebugLog("system", "WebSocket connected", false);
        // Send analysis request
        const request = {
          action: "start_analysis",
          request: {
            ticker: state.ticker,
            analysis_date: state.analysisDate,
            analysts: Array.from(state.analysts),
            research_depth: state.researchDepth,
            llm_provider: state.llmProvider,
            backend_url: state.backendUrl,
            shallow_thinker: state.shallowModel,
            deep_thinker: state.deepModel,
          }
        };
        ws.send(JSON.stringify(request));
        addDebugLog("request", `Starting analysis for ${state.ticker}`, false);
      };
      
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        const { type, data } = message;
        
        // Debug logging
        addDebugLog(type, JSON.stringify(data).substring(0, 200), type === "error");
        
        switch (type) {
          case "status":
            // Update agent statuses
            if (data.agents) {
              Object.entries(data.agents).forEach(([agentName, status]) => {
                const mapping = agentToTeamMap[agentName];
                if (mapping) {
                  const [teamKey, frontendName] = mapping;
                  updateAgentStatus(teamKey, frontendName, status);
                }
              });
            }
            break;
            
          case "message":
            // Could add to a messages log if needed
            console.log(`[${data.type}] ${data.content.substring(0, 100)}...`);
            break;
            
          case "tool_call":
            // Could display tool calls if needed
            console.log(`Tool: ${data.name}`);
            break;
            
          case "report":
            // Add or update report section
            const existingIndex = reportSections.findIndex(s => s.key === data.section);
            const reportSection = {
              key: data.section,
              label: data.label,
              text: data.content,
            };
            
            if (existingIndex >= 0) {
              reportSections[existingIndex] = reportSection;
            } else {
              reportSections.push(reportSection);
            }
            
            // Render all reports
            renderReportSections(reportSections);
            break;
            
          case "complete":
            // Analysis complete
            console.log("Analysis complete:", data.decision);
            
            // Update final reports if provided
            if (data.final_state) {
              const finalSections = [];
              const sectionMap = {
                market_report: { key: "market", label: "Market Analysis" },
                sentiment_report: { key: "sentiment", label: "Social Sentiment" },
                news_report: { key: "news", label: "News Analysis" },
                fundamentals_report: { key: "fundamentals", label: "Fundamentals Review" },
                investment_plan: { key: "investment_plan", label: "Research Team Decision" },
                trader_investment_plan: { key: "trader", label: "Trader Investment Plan" },
                final_trade_decision: { key: "final", label: "Portfolio Management Decision" },
              };
              
              Object.entries(data.final_state).forEach(([key, content]) => {
                if (content && sectionMap[key]) {
                  finalSections.push({
                    key: sectionMap[key].key,
                    label: sectionMap[key].label,
                    text: content,
                  });
                }
              });
              
              if (finalSections.length > 0) {
                renderReportSections(finalSections);
              }
            }
            
            // Extract and set recommendation
            if (data.decision) {
              setRecommendation(data.decision);
            } else {
              // Try to extract from final report
              const finalSection = reportSections.find(s => s.key === "final_trade_decision");
              if (finalSection) {
                const decision = extractDecision(finalSection.text);
                setRecommendation(decision);
              }
            }
            
            // Mark all agents as completed
            Object.keys(agentToTeamMap).forEach(agentName => {
              const mapping = agentToTeamMap[agentName];
              if (mapping) {
                const [teamKey, frontendName] = mapping;
                updateAgentStatus(teamKey, frontendName, "completed");
              }
            });
            
            ws.close();
            break;
            
          case "error":
            console.error("Error:", data.message);
            elements.reportContent.innerHTML = `<p style="color: var(--danger)">Error: ${data.message}</p>`;
            ws.close();
            break;
            
          case "pong":
            // Keep-alive response
            break;
        }
      };
      
      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        updateDebugWsStatus(false);
        addDebugLog("error", `WebSocket error: ${error.message || "Connection failed"}`, true);
        elements.reportContent.innerHTML = `<p style="color: var(--danger)">Connection error. Make sure the FastAPI backend is running on port 8000.</p>`;
        state.isRunning = false;
        elements.generateBtn.disabled = false;
        elements.generateBtn.textContent = "Generate";
      };
      
      ws.onclose = () => {
        console.log("WebSocket closed");
        updateDebugWsStatus(false);
        addDebugLog("system", "WebSocket connection closed", false);
        state.isRunning = false;
        elements.generateBtn.disabled = false;
        elements.generateBtn.textContent = "Generate";
      };
      
    } catch (error) {
      console.error("Error starting analysis:", error);
      elements.reportContent.innerHTML = `<p style="color: var(--danger)">Error: ${error.message}</p>`;
      state.isRunning = false;
      elements.generateBtn.disabled = false;
      elements.generateBtn.textContent = "Generate";
    }
  }

  function updateAgentStatus(teamKey, agentName, nextStatus) {
    const members = teamState[teamKey];
    if (!members) return;
    const member = members.find((item) => item.name === agentName);
    if (!member) return;
    member.status = nextStatus;
    renderTeamCard(teamKey);
  }

  async function loadSampleReports() {
    const promises = reportSources.map(async (section) => {
      try {
        const response = await fetch(section.path);
        if (!response.ok) {
          throw new Error(`Failed to fetch ${section.label}`);
        }
        const text = await response.text();
        return { ...section, text };
      } catch (error) {
        return { ...section, text: `Error loading ${section.label}: ${error.message}` };
      }
    });
    return Promise.all(promises);
  }

  function renderReportSections(sections) {
    elements.reportContent.innerHTML = "";
    const fullText = [];
    sections.forEach((section) => {
      const wrapper = document.createElement("div");
      wrapper.className = "report-block";
      const heading = document.createElement("h3");
      heading.textContent = section.label;
      wrapper.appendChild(heading);
      const body = convertMarkdownToDom(section.text);
      wrapper.appendChild(body);
      elements.reportContent.appendChild(wrapper);
      fullText.push(`${section.label}\n${section.text}`);
    });
    state.reportPlainText = fullText.join("\n\n");
  }

  function convertMarkdownToDom(markdownText) {
    const fragment = document.createElement("div");
    fragment.className = "report-body";
    const lines = markdownText.split("\n");
    let listEl = null;
    lines.forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed) {
        listEl = null;
        return;
      }
      if (/^[-*]/.test(trimmed)) {
        if (!listEl) {
          listEl = document.createElement("ul");
          listEl.className = "report-list";
          fragment.appendChild(listEl);
        }
        const li = document.createElement("li");
        li.innerHTML = formatInlineMarkdown(
          trimmed.replace(/^[-*]\s*/, "")
        );
        listEl.appendChild(li);
      } else {
        listEl = null;
        const paragraph = document.createElement("p");
        paragraph.innerHTML = formatInlineMarkdown(trimmed);
        fragment.appendChild(paragraph);
      }
    });
    return fragment;
  }

  function formatInlineMarkdown(text) {
    return escapeHtml(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  }

  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function extractDecision(markdownText) {
    const match = markdownText.match(
      /(BUY|SELL|HOLD|REDUCE|MONITOR|RE-EVALUATE)/i
    );
    return match ? match[0].toUpperCase() : "REVIEW";
  }

  function setRecommendation(decision) {
    elements.summaryDecision.textContent = decision;
    const normalized = decision.toLowerCase();
    let variant = "neutral";
    if (normalized.includes("buy")) variant = "buy";
    if (normalized.includes("sell")) variant = "sell";
    if (normalized.includes("reduce")) variant = "reduce";
    elements.recommendationCard.dataset.variant = variant;
  }

  async function copyReportToClipboard() {
    if (!state.reportPlainText) return;
    try {
      await navigator.clipboard.writeText(state.reportPlainText);
      elements.copyBtn.textContent = "Copied!";
      setTimeout(() => (elements.copyBtn.textContent = "Copy report"), 1800);
    } catch (error) {
      elements.copyBtn.textContent = "Copy failed";
      setTimeout(() => (elements.copyBtn.textContent = "Copy report"), 1800);
    }
  }

  function summarizeReport(reportText) {
    if (!reportText) return "";
    
    // Split by section headers (lines that look like headers)
    const lines = reportText.split("\n");
    const summary = [];
    let currentSection = null;
    let currentContent = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      
      // Detect section headers (titles like "Market Analysis", "Social Sentiment", etc.)
      const isHeader = (
        (line.match(/^[A-Z][A-Za-z\s]+$/) && line.length < 80 && !line.includes(".") && !line.includes(",")) ||
        line.match(/^#{1,6}\s/) ||
        (line.endsWith(":") && line.length < 60)
      );
      
      if (isHeader && !line.startsWith("•") && !line.startsWith("-") && !line.startsWith("*")) {
        // Save previous section
        if (currentSection) {
          summary.push(currentSection);
          const keyPoints = extractKeyPoints(currentContent.join(" "));
          if (keyPoints.length > 0) {
            summary.push(...keyPoints);
          }
          summary.push(""); // Add spacing
        }
        currentSection = line.replace(/^#+\s*/, "").replace(":", "");
        currentContent = [];
      } else if (currentSection) {
        currentContent.push(line);
      } else {
        // Content before first section
        currentContent.push(line);
      }
    }
    
    // Add last section
    if (currentSection) {
      summary.push(currentSection);
      const keyPoints = extractKeyPoints(currentContent.join(" "));
      if (keyPoints.length > 0) {
        summary.push(...keyPoints);
      }
    } else if (currentContent.length > 0) {
      // No sections found, just summarize the content
      const keyPoints = extractKeyPoints(currentContent.join(" "));
      summary.push(...keyPoints);
    }
    
    // Add recommendation if available
    const decision = elements.summaryDecision.textContent;
    if (decision && decision !== "Awaiting run" && decision !== "—") {
      summary.push("");
      summary.push(`RECOMMENDATION: ${decision}`);
    }
    
    return summary.join("\n");
  }
  
  function extractKeyPoints(text) {
    const keyPoints = [];
    
    // Extract bullet points first (most important)
    const bulletMatches = text.match(/[-*•·]\s*([^\n]+)/g);
    if (bulletMatches) {
      bulletMatches.slice(0, 3).forEach(match => {
        const point = match.replace(/^[-*•·]\s*/, "• ").trim();
        if (point.length > 10 && point.length < 200) {
          keyPoints.push(point);
        }
      });
    }
    
    // If no bullets, extract first 2-3 key sentences
    if (keyPoints.length === 0) {
      const sentences = text.split(/[.!?]+/).filter(s => {
        const trimmed = s.trim();
        return trimmed.length > 30 && trimmed.length < 250;
      });
      
      // Prioritize sentences with key terms
      const importantTerms = ["buy", "sell", "hold", "recommend", "price", "target", "risk", "opportunity", "trend", "analysis"];
      const scoredSentences = sentences.map(s => {
        const lower = s.toLowerCase();
        const score = importantTerms.reduce((acc, term) => acc + (lower.includes(term) ? 1 : 0), 0);
        return { text: s.trim(), score };
      }).sort((a, b) => b.score - a.score);
      
      scoredSentences.slice(0, 2).forEach(item => {
        if (item.text) {
          keyPoints.push(item.text + ".");
        }
      });
    }
    
    return keyPoints;
  }

  function downloadReportAsPdf() {
    if (!state.reportPlainText) return;
    if (!window.jspdf || !window.jspdf.jsPDF) return;
    
    const doc = new window.jspdf.jsPDF({ unit: "pt", format: "a4" });
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 40;
    const maxWidth = pageWidth - (margin * 2);
    const lineHeight = 14;
    
    let yPosition = margin + 20;
    
    // Add header
    doc.setFontSize(16);
    doc.setFont(undefined, "bold");
    doc.text(`TradingAgents Report: ${state.ticker}`, margin, yPosition);
    yPosition += 20;
    
    doc.setFontSize(10);
    doc.setFont(undefined, "normal");
    doc.text(`Analysis Date: ${state.analysisDate}`, margin, yPosition);
    yPosition += 30;
    
    // Add separator line
    doc.line(margin, yPosition, pageWidth - margin, yPosition);
    yPosition += 25;
    
    // Add "Current Report" section header
    doc.setFontSize(14);
    doc.setFont(undefined, "bold");
    doc.text("Current Report", margin, yPosition);
    yPosition += 20;
    
    // Generate summarized report
    const summarizedReport = summarizeReport(state.reportPlainText);
    
    // Set font for body text
    doc.setFontSize(10);
    doc.setFont(undefined, "normal");
    
    // Split summarized text into lines
    const summaryLines = doc.splitTextToSize(summarizedReport, maxWidth);
    
    // Process each line
    for (let i = 0; i < summaryLines.length; i++) {
      const line = summaryLines[i];
      
      // Check if we need a new page
      if (yPosition > pageHeight - margin - lineHeight) {
        doc.addPage();
        yPosition = margin;
      }
      
      // Handle section headers (uppercase lines ending with colon or all caps)
      if (line.trim().match(/^[A-Z][A-Z\s:]+$/) && line.trim().length < 80) {
        yPosition += 5; // Add spacing before section header
        if (yPosition > pageHeight - margin - lineHeight) {
          doc.addPage();
          yPosition = margin;
        }
        doc.setFontSize(11);
        doc.setFont(undefined, "bold");
        doc.text(line.trim(), margin, yPosition);
        doc.setFontSize(10);
        doc.setFont(undefined, "normal");
        yPosition += lineHeight + 3;
      } else if (line.trim().startsWith("RECOMMENDATION:")) {
        // Highlight recommendation
        yPosition += 10;
        if (yPosition > pageHeight - margin - lineHeight) {
          doc.addPage();
          yPosition = margin;
        }
        doc.setFontSize(12);
        doc.setFont(undefined, "bold");
        doc.text(line.trim(), margin, yPosition);
        doc.setFontSize(10);
        doc.setFont(undefined, "normal");
        yPosition += lineHeight + 5;
      } else {
        // Regular text
        doc.text(line, margin, yPosition);
        yPosition += lineHeight;
      }
    }
    
    // Add footer with page numbers
    const totalPages = doc.internal.pages.length - 1;
    for (let i = 1; i <= totalPages; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.text(
        `Page ${i} of ${totalPages}`,
        pageWidth / 2,
        pageHeight - 20,
        { align: "center" }
      );
    }
    
    doc.save(`TradingAgents-${state.ticker}-${state.analysisDate}.pdf`);
  }

  function wait(duration) {
    return new Promise((resolve) => setTimeout(resolve, duration));
  }

  function deepClone(payload) {
    return JSON.parse(JSON.stringify(payload));
  }

  function toISODate() {
    return new Date().toISOString().split("T")[0];
  }
})();

