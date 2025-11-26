// Popup script for Privacy Policy Analyzer Extension

document.addEventListener('DOMContentLoaded', async function() {
    console.log('Privacy Policy Analyzer: Popup loaded');
    
    // Get current tab info
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Update popup based on current page
    updatePopupContent(tab);
    
    // Add event listeners
    setupEventListeners(tab);
});

function updatePopupContent(tab) {
    const url = tab.url;
    const title = tab.title;
    
    // Check if current page is a privacy policy
    const isPrivacyPage = isPrivacyPolicyPage(url, title);
    
    if (isPrivacyPage) {
        showPrivacyPageContent(url);
    } else {
        showGeneralContent();
    }
}

function isPrivacyPolicyPage(url, title) {
    const privacyKeywords = ['privacy', 'policy', 'terms', 'conditions', 'personvern'];
    const urlLower = url.toLowerCase();
    const titleLower = title.toLowerCase();
    
    return privacyKeywords.some(keyword => 
        urlLower.includes(keyword) || titleLower.includes(keyword)
    );
}

function showPrivacyPageContent(url) {
    const platform = extractPlatformName(url);
    
    document.getElementById('summary').innerHTML = `
        <div style="text-align: center; margin-bottom: 1rem;">
            <div style="font-size: 2em; margin-bottom: 0.5rem;">🔍</div>
            <h3 style="margin: 0; color: #333;">Privacy Policy Detected!</h3>
            <p style="margin: 0.5rem 0; color: #666; font-size: 0.9em;">
                Platform: <strong>${platform}</strong>
            </p>
        </div>
    `;
    
    // Update analyze button
    const analyzeBtn = document.getElementById('analyzeBtn');
    analyzeBtn.textContent = '🤖 Analyze This Policy';
    analyzeBtn.style.display = 'block';
}

function showGeneralContent() {
    document.getElementById('summary').innerHTML = `
        <div style="text-align: center; margin-bottom: 1rem;">
            <div style="font-size: 2em; margin-bottom: 0.5rem;">🔒</div>
            <h3 style="margin: 0; color: #333;">Privacy Analyzer</h3>
            <p style="margin: 0.5rem 0; color: #666; font-size: 0.9em;">
                Navigate to a privacy policy page to analyze it
            </p>
        </div>
        
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
            <h4 style="margin: 0 0 0.5rem 0; color: #495057; font-size: 0.9em;">Quick Access:</h4>
            <div style="display: grid; gap: 0.5rem;">
                <button class="quick-link" data-url="https://www.facebook.com/privacy/policy">
                    📘 Facebook Privacy
                </button>
                <button class="quick-link" data-url="https://help.instagram.com/519522125107875">
                    📷 Instagram Privacy
                </button>
                <button class="quick-link" data-url="https://www.tiktok.com/legal/page/row/privacy-policy/en">
                    🎵 TikTok Privacy
                </button>
            </div>
        </div>
    `;
    
    // Hide analyze button for non-privacy pages
    document.getElementById('analyzeBtn').style.display = 'none';
}

function setupEventListeners(tab) {
    // Analyze button
    document.getElementById('analyzeBtn').addEventListener('click', async () => {
        await analyzeCurrentPage(tab);
    });
    
    // Compare button
    document.getElementById('compareBtn').addEventListener('click', () => {
        chrome.tabs.create({ url: 'http://localhost:8501' });
    });
    
    // Settings button
    document.getElementById('settingsBtn').addEventListener('click', () => {
        showSettings();
    });
    
    // Quick links (if they exist)
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('quick-link')) {
            const url = e.target.getAttribute('data-url');
            chrome.tabs.create({ url: url });
        }
    });
}

async function analyzeCurrentPage(tab) {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const originalText = analyzeBtn.textContent;
    
    try {
        // Show loading state
        analyzeBtn.textContent = '🤖 Analyzing...';
        analyzeBtn.disabled = true;
        
        // Inject content script to extract policy text
        const [result] = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            function: extractPolicyText
        });
        
        const policyText = result.result;
        const platform = extractPlatformName(tab.url);
        
        // Analyze with our API or fallback
        let analysis;
        try {
            const response = await fetch('http://localhost:8502/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: tab.url,
                    text: policyText,
                    platform: platform
                })
            });
            
            if (response.ok) {
                analysis = await response.json();
            } else {
                throw new Error('API unavailable');
            }
        } catch (error) {
            // Use fallback analysis
            analysis = getFallbackAnalysis(platform);
        }
        
        // Show results
        showAnalysisResults(analysis);
        
    } catch (error) {
        console.error('Analysis failed:', error);
        
        // Show error message
        document.getElementById('summary').innerHTML = `
            <div style="text-align: center; color: #dc3545;">
                <div style="font-size: 2em; margin-bottom: 0.5rem;">⚠️</div>
                <h3>Analysis Failed</h3>
                <p style="font-size: 0.9em;">Please try again or visit our web app.</p>
        </div>
        
        <!-- Chat Interface -->
        <div style="margin-top: 20px; padding: 15px; border-top: 1px solid #eee;">
            <h4 style="margin: 0 0 10px 0; color: #333;">💬 Ask About This Policy</h4>
            <div style="display: flex; gap: 8px; margin-bottom: 10px;">
                <input type="text" id="chatInput" placeholder="e.g., Do they track location?" 
                       style="flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px;">
                <button id="askBtn" style="padding: 8px 12px; background: #007bff; color: white; border: none; border-radius: 4px; font-size: 12px;">Ask</button>
            </div>
            <div id="chatResponse" style="font-size: 12px; color: #666; min-height: 20px;"></div>
        </div>
    `;
    
    // Add chat functionality
    const chatInput = document.getElementById('chatInput');
    const askBtn = document.getElementById('askBtn');
    const chatResponse = document.getElementById('chatResponse');
    
    askBtn.addEventListener('click', async () => {
        const question = chatInput.value.trim();
        if (!question) return;
        
        askBtn.textContent = '🤖';
        askBtn.disabled = true;
        chatResponse.innerHTML = '<div style="color: #666;">🤖 Thinking...</div>';
        
        try {
            const response = await fetch('http://localhost:8502/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: question,
                    platform: analysis.platform || 'Unknown'
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                chatResponse.innerHTML = `<div style="background: #f8f9fa; padding: 8px; border-radius: 4px; margin-top: 5px;">${result.response}</div>`;
            } else {
                throw new Error('API unavailable');
            }
        } catch (error) {
            chatResponse.innerHTML = '<div style="color: #dc3545;">Chat temporarily unavailable. Please use the main app.</div>';
        } finally {
            askBtn.textContent = 'Ask';
            askBtn.disabled = false;
            chatInput.value = '';
        }
    });
    
    // Enter key support
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') askBtn.click();
    });
} finally {
        // Reset button
        analyzeBtn.textContent = originalText;
        analyzeBtn.disabled = false;
    }
}

// Function to inject into page for text extraction
function extractPolicyText() {
    // Remove unwanted elements
    const unwanted = document.querySelectorAll('script, style, nav, footer, header');
    unwanted.forEach(el => el.remove());
    
    // Get main content
    const main = document.querySelector('main, .content, .policy, #content') || document.body;
    let text = main.innerText || main.textContent || '';
    
    // Clean and limit text
    text = text.replace(/\s+/g, ' ').trim();
    return text.substring(0, 3000);
}

function extractPlatformName(url) {
    const domain = new URL(url).hostname.toLowerCase();
    
    if (domain.includes('facebook')) return 'Facebook';
    if (domain.includes('instagram')) return 'Instagram';
    if (domain.includes('tiktok')) return 'TikTok';
    if (domain.includes('tinder')) return 'Tinder';
    if (domain.includes('whatsapp')) return 'WhatsApp';
    if (domain.includes('finn.no')) return 'Finn.no';
    
    return 'Unknown Platform';
}

function getFallbackAnalysis(platform) {
    const fallbackData = {
        'Facebook': {
            score: 25,
            harmful_points: "Tracks your activity across the entire internet and uses psychological manipulation techniques.",
            recommendation: "Use in a separate browser and turn off location tracking."
        },
        'Instagram': {
            score: 30,
            harmful_points: "Analyzes your photos with AI and tracks viewing patterns to manipulate your feed.",
            recommendation: "Limit photo uploads and use time limits."
        },
        'TikTok': {
            score: 15,
            harmful_points: "Collects biometric data and may share with foreign governments.",
            recommendation: "Avoid for sensitive communications and consider geopolitical risks."
        }
    };
    
    return fallbackData[platform] || {
        score: 50,
        harmful_points: "Collects personal data and shares with third parties.",
        recommendation: "Review privacy settings carefully."
    };
}

function showAnalysisResults(analysis) {
    const scoreColor = analysis.score >= 70 ? '#28a745' : analysis.score >= 50 ? '#ffc107' : '#dc3545';
    const riskLevel = analysis.score >= 70 ? 'Low Risk' : analysis.score >= 50 ? 'Medium Risk' : 'High Risk';
    
    document.getElementById('summary').innerHTML = `
        <div style="text-align: center; margin-bottom: 1rem;">
            <div style="font-size: 2.5em; font-weight: bold; color: ${scoreColor};">
                ${analysis.score}/100
            </div>
            <div style="color: ${scoreColor}; font-weight: 600; margin-bottom: 1rem;">
                ${riskLevel}
            </div>
        </div>
    `;
    
    // Show concerns
    document.getElementById('concerns').style.display = 'block';
    document.getElementById('concernsList').innerHTML = `
        <li style="margin-bottom: 0.5rem; font-size: 0.9em;">
            ${analysis.harmful_points}
        </li>
    `;
    
    // Show recommendation
    document.getElementById('positives').style.display = 'block';
    document.getElementById('positivesList').innerHTML = `
        <li style="margin-bottom: 0.5rem; font-size: 0.9em;">
            ${analysis.recommendation}
        </li>
    `;
}

function showSettings() {
    document.getElementById('summary').innerHTML = `
        <div>
            <h3 style="margin: 0 0 1rem 0;">⚙️ Settings</h3>
            <div style="margin-bottom: 1rem;">
                <label style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <input type="checkbox" id="autoAnalyze" style="margin-right: 0.5rem;">
                    Auto-analyze privacy policies
                </label>
                <label style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <input type="checkbox" id="showNotifications" style="margin-right: 0.5rem;">
                    Show privacy notifications
                </label>
            </div>
            <button onclick="location.reload()" style="
                background: #6c757d; color: white; border: none; border-radius: 4px;
                padding: 0.5rem 1rem; cursor: pointer; width: 100%;
            ">
                ← Back
            </button>
        </div>
    `;
    
    // Load saved settings
    chrome.storage.sync.get(['autoAnalyze', 'showNotifications'], (result) => {
        document.getElementById('autoAnalyze').checked = result.autoAnalyze || false;
        document.getElementById('showNotifications').checked = result.showNotifications || true;
    });
    
    // Save settings on change
    document.getElementById('autoAnalyze').addEventListener('change', (e) => {
        chrome.storage.sync.set({ autoAnalyze: e.target.checked });
    });
    
    document.getElementById('showNotifications').addEventListener('change', (e) => {
        chrome.storage.sync.set({ showNotifications: e.target.checked });
    });
}
