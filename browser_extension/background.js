// Background service worker for Privacy Policy Analyzer Extension

console.log('Privacy Policy Analyzer: Background script loaded');

// Install event
chrome.runtime.onInstalled.addListener((details) => {
    console.log('Privacy Policy Analyzer: Extension installed');
    
    // Set default settings
    chrome.storage.sync.set({
        autoAnalyze: true,
        showNotifications: true,
        extensionEnabled: true
    });
    
    // Show welcome notification
    if (details.reason === 'install') {
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon48.png',
            title: 'Privacy Policy Analyzer Installed!',
            message: 'Navigate to any privacy policy page to see instant analysis.'
        });
    }
});

// Tab update event - detect privacy policy pages
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url) {
        const settings = await chrome.storage.sync.get(['autoAnalyze', 'showNotifications']);
        
        if (settings.autoAnalyze && isPrivacyPolicyUrl(tab.url)) {
            // Show notification for privacy policy detection
            if (settings.showNotifications) {
                chrome.notifications.create({
                    type: 'basic',
                    iconUrl: 'icons/icon48.png',
                    title: 'Privacy Policy Detected!',
                    message: `Click the extension icon to analyze ${extractDomain(tab.url)}'s privacy policy.`
                });
            }
            
            // Update badge
            chrome.action.setBadgeText({
                tabId: tabId,
                text: '!'
            });
            
            chrome.action.setBadgeBackgroundColor({
                color: '#dc3545'
            });
        } else {
            // Clear badge for non-privacy pages
            chrome.action.setBadgeText({
                tabId: tabId,
                text: ''
            });
        }
    }
});

// Message handling from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Background received message:', request);
    
    if (request.action === 'analyzePolicy') {
        handlePolicyAnalysis(request.data, sendResponse);
        return true; // Keep message channel open for async response
    }
    
    if (request.action === 'updateBadge') {
        chrome.action.setBadgeText({
            tabId: sender.tab.id,
            text: request.text
        });
    }
    
    if (request.action === 'openFullAnalysis') {
        // Open full analysis in new tab
        chrome.tabs.create({
            url: request.url,
            active: true
        });
        sendResponse({ success: true });
    }
    
    if (request.action === 'analyzeCompany') {
        handleCompanyAnalysis(request.website, sendResponse);
        return true; // Keep message channel open for async response
    }
});

// Handle policy analysis requests
async function handlePolicyAnalysis(data, sendResponse) {
    try {
        // Try to connect to local API first
        const response = await fetch('http://localhost:8502/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const analysis = await response.json();
            sendResponse({ success: true, data: analysis });
        } else {
            throw new Error('API unavailable');
        }
        
    } catch (error) {
        console.log('API unavailable, using fallback analysis');
        
        // Use fallback analysis
        const fallbackAnalysis = getFallbackAnalysis(data.platform);
        sendResponse({ success: true, data: fallbackAnalysis });
    }
}

// Check if URL is a privacy policy page
function isPrivacyPolicyUrl(url) {
    const urlLower = url.toLowerCase();
    const privacyKeywords = [
        'privacy', 'policy', 'terms', 'conditions', 'personvern', 
        'datenschutz', 'confidentialité', 'legal'
    ];
    
    return privacyKeywords.some(keyword => urlLower.includes(keyword));
}

// Extract domain from URL
function extractDomain(url) {
    try {
        const domain = new URL(url).hostname;
        return domain.replace('www.', '');
    } catch {
        return 'this site';
    }
}

// Fallback analysis for when API is unavailable
function getFallbackAnalysis(platform) {
    const fallbackData = {
        'Facebook': {
            score: 25,
            harmful_points: "Facebook tracks your activity across the entire internet, builds shadow profiles of non-users through your contacts, and uses psychological manipulation techniques to increase engagement. They collect data even when you're not using Facebook.",
            worst_data: "Complete browsing history across all websites, real-time location tracking, and psychological profiling data used to influence your behavior and political views.",
            recommendation: "Use Facebook in a separate browser, turn off all location tracking, and regularly review what data they have on you."
        },
        'Instagram': {
            score: 30,
            harmful_points: "Instagram analyzes your photos using AI to detect your emotions, relationships, and lifestyle patterns. They track how long you look at each post to manipulate your feed and keep you addicted to the platform.",
            worst_data: "AI analysis of your photos revealing personal relationships, mental health patterns, and detailed behavioral data used for algorithmic manipulation.",
            recommendation: "Limit photo uploads with people in them, turn off activity tracking, and use time limits to avoid algorithmic manipulation."
        },
        'TikTok': {
            score: 15,
            harmful_points: "TikTok collects biometric data including face and voice prints, accesses your clipboard without permission, and may share data with the Chinese government. They track your behavior even when the app is closed.",
            worst_data: "Biometric identifiers (face, voice, keystroke patterns), clipboard contents, and detailed behavioral data that could be accessed by foreign governments.",
            recommendation: "Avoid using TikTok for sensitive communications, turn off microphone access, and consider the geopolitical risks of your data being in China."
        },
        'Tinder': {
            score: 35,
            harmful_points: "Tinder collects your exact location, biometric data from photos, and tracks your swiping patterns to create detailed behavioral profiles. They share this intimate data with Match Group's 45+ companies and keep it indefinitely.",
            worst_data: "Your precise location, facial recognition data, and detailed records of who you're attracted to - creating a comprehensive profile of your romantic preferences.",
            recommendation: "Turn off location services, avoid uploading clear face photos, and regularly delete your account if you're not actively using it."
        },
        'WhatsApp': {
            score: 60,
            harmful_points: "While messages are encrypted, WhatsApp collects extensive metadata about who you talk to, when, and for how long. This metadata is shared with Facebook for advertising and can reveal your social network and behavior patterns.",
            worst_data: "Complete social network mapping, communication patterns, and location data that reveals your daily routines and relationships.",
            recommendation: "Use Signal for sensitive conversations, turn off read receipts and last seen, and limit location sharing."
        },
        'Finn.no': {
            score: 70,
            harmful_points: "Finn.no tracks your search history and browsing patterns to build detailed profiles of your interests, income level, and life situation. This data is shared with advertising partners and could be used for price discrimination.",
            worst_data: "Detailed financial profiling based on what you search for and buy, revealing your economic situation and personal needs.",
            recommendation: "Use private browsing mode, avoid searching for sensitive items when not serious about buying, and regularly clear your search history."
        }
    };
    
    return fallbackData[platform] || {
        score: 50,
        harmful_points: "This platform collects personal data and shares it with third parties for advertising purposes. The extent of data collection and sharing practices may pose privacy risks.",
        worst_data: "Personal information and behavioral data used for profiling and targeted advertising.",
        recommendation: "Review privacy settings carefully, limit data sharing where possible, and consider using privacy-focused alternatives."
    };
}

// Context menu for quick analysis
chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: 'analyzePrivacyPolicy',
        title: 'Analyze Privacy Policy',
        contexts: ['page'],
        documentUrlPatterns: [
            '*://*/*privacy*',
            '*://*/*terms*',
            '*://*/*policy*'
        ]
    });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === 'analyzePrivacyPolicy') {
        // Inject content script to show analysis widget
        chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['content.js']
        });
    }
});

// Handle company website analysis requests
async function handleCompanyAnalysis(website, sendResponse) {
    try {
        // Try to connect to local API for company analysis
        const response = await fetch('http://localhost:8502/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                analysis_type: 'company',
                company_website: website
            })
        });
        
        if (response.ok) {
            const analysis = await response.json();
            sendResponse({
                success: true,
                analysis: analysis
            });
        } else {
            throw new Error(`API returned ${response.status}`);
        }
        
    } catch (error) {
        console.error('Company analysis failed:', error);
        
        // Fallback analysis
        const fallbackAnalysis = {
            score: 50,
            harmful_points: `${website} likely collects personal data for business purposes. Without access to their privacy policy, the full extent of data collection is unknown.`,
            worst_data: "Contact information, usage patterns, and potentially location data.",
            recommendation: `Contact ${website} directly for their privacy policy, or look for privacy information in their app or website footer.`,
            source: 'fallback'
        };
        
        sendResponse({
            success: true,
            analysis: fallbackAnalysis
        });
    }
}
