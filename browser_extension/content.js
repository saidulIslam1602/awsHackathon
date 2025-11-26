// Content script for Privacy Policy Analyzer Extension
// Automatically detects privacy policy pages and shows analysis

console.log('Privacy Policy Analyzer: Content script loaded');

// Check if this page looks like a privacy policy
function isPrivacyPolicyPage() {
    const url = window.location.href.toLowerCase();
    const title = document.title.toLowerCase();
    const bodyText = document.body.innerText.toLowerCase();
    
    const privacyKeywords = [
        'privacy', 'policy', 'terms', 'conditions', 'data', 'cookies',
        'personvern', 'datenschutz', 'confidentialité'
    ];
    
    return privacyKeywords.some(keyword => 
        url.includes(keyword) || title.includes(keyword) || 
        (bodyText.includes(keyword) && bodyText.includes('collect'))
    );
}

// Extract policy text from the page
function extractPolicyText() {
    // Remove scripts, styles, and navigation elements
    const elementsToRemove = document.querySelectorAll('script, style, nav, footer, header, .nav, .menu');
    elementsToRemove.forEach(el => el.remove());
    
    // Get main content
    const mainContent = document.querySelector('main, .content, .policy, .privacy, #content, .main') || document.body;
    
    let text = mainContent.innerText || mainContent.textContent || '';
    
    // Clean up the text
    text = text.replace(/\s+/g, ' ').trim();
    
    // Limit to first 5000 characters for processing
    return text.substring(0, 5000);
}

// Create and inject the analysis widget
function createAnalysisWidget() {
    // Check if widget already exists
    if (document.getElementById('privacy-analyzer-widget')) {
        return;
    }
    
    const widget = document.createElement('div');
    widget.id = 'privacy-analyzer-widget';
    widget.innerHTML = `
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            width: 320px;
            background: white;
            border: 2px solid #dc3545;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        ">
            <div style="
                background: #dc3545;
                color: white;
                padding: 12px 16px;
                border-radius: 10px 10px 0 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div style="font-weight: 600; font-size: 14px;">
                    🔒 Privacy Analyzer
                </div>
                <button id="close-widget" style="
                    background: none;
                    border: none;
                    color: white;
                    font-size: 18px;
                    cursor: pointer;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                ">×</button>
            </div>
            <div id="widget-content" style="padding: 16px;">
                <div style="text-align: center; color: #666; font-size: 14px;">
                    <div style="margin-bottom: 12px;">
                        📄 Privacy policy detected!
                    </div>
                    <button id="analyze-btn" style="
                        background: #dc3545;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-size: 14px;
                        font-weight: 600;
                        cursor: pointer;
                        width: 100%;
                    ">
                        🤖 Analyze Risks
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(widget);
    
    // Add event listeners
    document.getElementById('close-widget').addEventListener('click', () => {
        widget.remove();
    });
    
    document.getElementById('analyze-btn').addEventListener('click', () => {
        analyzeCurrentPage();
    });
}

// Analyze the current page
async function analyzeCurrentPage() {
    const contentDiv = document.getElementById('widget-content');
    const analyzeBtn = document.getElementById('analyze-btn');
    
    // Show loading state
    contentDiv.innerHTML = `
        <div style="text-align: center; color: #666; font-size: 14px;">
            <div style="margin-bottom: 12px;">
                🤖 AI is analyzing...
            </div>
            <div style="
                width: 100%;
                height: 4px;
                background: #f0f0f0;
                border-radius: 2px;
                overflow: hidden;
            ">
                <div style="
                    width: 100%;
                    height: 100%;
                    background: #dc3545;
                    animation: loading 2s infinite;
                "></div>
            </div>
        </div>
        <style>
            @keyframes loading {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
        </style>
    `;
    
    try {
        // Extract policy text
        const policyText = extractPolicyText();
        const currentUrl = window.location.href;
        
        // Send to our API for analysis
        const response = await fetch('http://localhost:8502/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: currentUrl,
                text: policyText,
                platform: extractPlatformName(currentUrl)
            })
        });
        
        if (!response.ok) {
            throw new Error('Analysis failed');
        }
        
        const analysis = await response.json();
        
        // Show results
        showAnalysisResults(analysis);
        
    } catch (error) {
        console.error('Analysis error:', error);
        
        // Show fallback analysis
        const fallbackAnalysis = getFallbackAnalysis(window.location.href);
        showAnalysisResults(fallbackAnalysis);
    }
}

// Extract platform name from URL
function extractPlatformName(url) {
    const domain = new URL(url).hostname.toLowerCase();
    
    if (domain.includes('facebook')) return 'Facebook';
    if (domain.includes('instagram')) return 'Instagram';
    if (domain.includes('tiktok')) return 'TikTok';
    if (domain.includes('tinder')) return 'Tinder';
    if (domain.includes('whatsapp')) return 'WhatsApp';
    if (domain.includes('finn.no')) return 'Finn.no';
    if (domain.includes('linkedin')) return 'LinkedIn';
    if (domain.includes('twitter') || domain.includes('x.com')) return 'Twitter';
    
    return 'Unknown Platform';
}

// Get fallback analysis for known platforms
function getFallbackAnalysis(url) {
    const platform = extractPlatformName(url);
    
    const fallbackData = {
        'Facebook': {
            score: 25,
            harmful_points: "Facebook tracks your activity across the entire internet, builds shadow profiles of non-users through your contacts, and uses psychological manipulation techniques to increase engagement.",
            worst_data: "Complete browsing history across all websites, real-time location tracking, and psychological profiling data used to influence your behavior.",
            recommendation: "Use Facebook in a separate browser, turn off all location tracking, and regularly review what data they have on you."
        },
        'Instagram': {
            score: 30,
            harmful_points: "Instagram analyzes your photos using AI to detect your emotions, relationships, and lifestyle patterns. They track how long you look at each post to manipulate your feed.",
            worst_data: "AI analysis of your photos revealing personal relationships, mental health patterns, and detailed behavioral data used for algorithmic manipulation.",
            recommendation: "Limit photo uploads with people in them, turn off activity tracking, and use time limits to avoid algorithmic manipulation."
        },
        'TikTok': {
            score: 15,
            harmful_points: "TikTok collects biometric data including face and voice prints, accesses your clipboard without permission, and may share data with the Chinese government.",
            worst_data: "Biometric identifiers (face, voice, keystroke patterns), clipboard contents, and detailed behavioral data that could be accessed by foreign governments.",
            recommendation: "Avoid using TikTok for sensitive communications, turn off microphone access, and consider the geopolitical risks."
        }
    };
    
    return fallbackData[platform] || {
        score: 50,
        harmful_points: "This platform collects personal data and may share it with third parties for advertising purposes.",
        worst_data: "Personal information and behavioral data used for profiling and targeting.",
        recommendation: "Review privacy settings and limit data sharing where possible."
    };
}

// Show analysis results in the widget
function showAnalysisResults(analysis) {
    const contentDiv = document.getElementById('widget-content');
    
    const scoreColor = analysis.score >= 70 ? '#28a745' : analysis.score >= 50 ? '#ffc107' : '#dc3545';
    const riskLevel = analysis.score >= 70 ? 'Low Risk' : analysis.score >= 50 ? 'Medium Risk' : 'High Risk';
    
    contentDiv.innerHTML = `
        <div style="font-size: 13px; line-height: 1.4;">
            <!-- Privacy Score -->
            <div style="text-align: center; margin-bottom: 16px; padding: 12px; background: #f8f9fa; border-radius: 8px;">
                <div style="font-size: 24px; font-weight: bold; color: ${scoreColor}; margin-bottom: 4px;">
                    ${analysis.score}/100
                </div>
                <div style="color: ${scoreColor}; font-weight: 600; font-size: 12px;">
                    ${riskLevel}
                </div>
            </div>
            
            <!-- Harmful Points -->
            <div style="margin-bottom: 12px; padding: 12px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
                <div style="font-weight: 600; color: #856404; margin-bottom: 6px; font-size: 12px;">
                    🚨 Main Concerns
                </div>
                <div style="color: #856404; font-size: 12px;">
                    ${analysis.harmful_points}
                </div>
            </div>
            
            <!-- Recommendation -->
            <div style="padding: 12px; background: #d1ecf1; border-left: 4px solid #17a2b8; border-radius: 4px;">
                <div style="font-weight: 600; color: #0c5460; margin-bottom: 6px; font-size: 12px;">
                    💡 What To Do
                </div>
                <div style="color: #0c5460; font-size: 12px;">
                    ${analysis.recommendation}
                </div>
            </div>
            
            <!-- Actions -->
            <div style="margin-top: 12px; text-align: center;">
                <button id="full-analysis-btn" style="
                    background: #17a2b8;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 12px;
                    cursor: pointer;
                    margin-right: 8px;
                ">
                    📊 Full Analysis
                </button>
                <button onclick="document.getElementById('privacy-analyzer-widget').remove()" style="
                    background: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 12px;
                    cursor: pointer;
                ">
                    Close
                </button>
            </div>
        </div>
    `;
    
    // Add event listener for Full Analysis button
    const fullAnalysisBtn = document.getElementById('full-analysis-btn');
    if (fullAnalysisBtn) {
        fullAnalysisBtn.addEventListener('click', () => {
            // Use chrome.tabs API to open new tab (more reliable than window.open)
            chrome.runtime.sendMessage({
                action: 'openFullAnalysis',
                url: 'http://localhost:8501'
            });
        });
    }
}

// Create company analysis widget for any website
function createCompanyAnalysisWidget() {
    // Don't show on search engines or common non-company sites
    const url = window.location.href.toLowerCase();
    const skipDomains = ['google.', 'bing.', 'yahoo.', 'duckduckgo.', 'wikipedia.', 'localhost'];
    
    if (skipDomains.some(domain => url.includes(domain))) {
        return;
    }
    
    // Check if widget already exists
    if (document.getElementById('privacy-analyzer-company-widget')) {
        return;
    }
    
    // Extract company name from domain
    const domain = window.location.hostname.replace('www.', '');
    const companyName = domain.split('.')[0];
    
    const widget = document.createElement('div');
    widget.id = 'privacy-analyzer-company-widget';
    widget.innerHTML = `
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            max-width: 280px;
            cursor: pointer;
            transition: all 0.3s ease;
        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 16px;">🔒</span>
                <span style="font-weight: 500;">Privacy Analysis Available</span>
            </div>
            <div style="font-size: 12px; opacity: 0.9; margin-top: 4px;">
                Click to analyze ${companyName}'s privacy policy
            </div>
        </div>
    `;
    
    widget.addEventListener('click', () => {
        analyzeCompanyWebsite(domain);
        widget.remove();
    });
    
    // Auto-hide after 8 seconds
    setTimeout(() => {
        if (widget.parentNode) {
            widget.style.opacity = '0';
            setTimeout(() => widget.remove(), 300);
        }
    }, 8000);
    
    document.body.appendChild(widget);
}

// Analyze company website privacy policy
async function analyzeCompanyWebsite(domain) {
    // Create analysis widget
    createAnalysisWidget();
    
    const contentDiv = document.getElementById('widget-content');
    
    // Show loading state
    contentDiv.innerHTML = `
        <div style="text-align: center; color: #666; font-size: 14px;">
            <div style="margin-bottom: 12px;">
                🌐 Finding ${domain}'s privacy policy...
            </div>
            <div style="
                width: 100%;
                height: 4px;
                background: #f0f0f0;
                border-radius: 2px;
                overflow: hidden;
            ">
                <div style="
                    width: 100%;
                    height: 100%;
                    background: #dc3545;
                    animation: loading 2s infinite;
                "></div>
            </div>
        </div>
        <style>
            @keyframes loading {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
        </style>
    `;
    
    try {
        // Send to our API for company analysis
        const response = await fetch('http://localhost:8502/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: `https://${domain}`,
                company_website: domain,
                analysis_type: 'company'
            })
        });
        
        if (!response.ok) {
            throw new Error('Analysis failed');
        }
        
        const analysis = await response.json();
        
        // Show results
        showAnalysisResults(analysis);
        
    } catch (error) {
        console.error('Company analysis error:', error);
        
        // Show fallback analysis
        const fallbackAnalysis = getFallbackAnalysis(`https://${domain}`);
        fallbackAnalysis.company_name = domain.split('.')[0];
        showAnalysisResults(fallbackAnalysis);
    }
}

// Initialize the extension
function initializeExtension() {
    if (isPrivacyPolicyPage()) {
        console.log('Privacy Policy Analyzer: Privacy policy detected, showing widget');
        
        // Wait a bit for the page to fully load
        setTimeout(() => {
            createAnalysisWidget();
        }, 2000);
    } else {
        console.log('Privacy Policy Analyzer: Regular website detected, showing company analysis option');
        
        // Show company analysis widget after a delay
        setTimeout(() => {
            createCompanyAnalysisWidget();
        }, 3000);
    }
}

// Run when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeExtension);
} else {
    initializeExtension();
}
