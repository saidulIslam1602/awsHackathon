# 🔒 Privacy Policy Analyzer - Browser Extension

## Installation Instructions

### Chrome/Edge Installation

1. **Open Extension Management**
   - Go to `chrome://extensions/` (Chrome) or `edge://extensions/` (Edge)
   - Enable "Developer mode" (toggle in top right)

2. **Load Extension**
   - Click "Load unpacked"
   - Select the `browser_extension` folder from your project
   - The extension should now appear in your extensions list

3. **Pin Extension**
   - Click the puzzle piece icon in your browser toolbar
   - Find "Privacy Policy Analyzer" and click the pin icon
   - The 🔒 icon should now be visible in your toolbar

### Firefox Installation

1. **Open Add-ons Manager**
   - Go to `about:debugging#/runtime/this-firefox`
   - Click "Load Temporary Add-on"

2. **Load Extension**
   - Navigate to the `browser_extension` folder
   - Select the `manifest.json` file
   - The extension will be loaded temporarily

## How to Use

### Automatic Detection
- Navigate to any privacy policy page
- The extension will automatically detect it and show a widget
- Click "🤖 Analyze Risks" for instant analysis

### Manual Analysis
- Click the 🔒 extension icon in your toolbar
- If on a privacy policy page, click "Analyze This Policy"
- For other sites, use the quick links to popular platforms

### Features
- **Real-time Analysis**: Instant privacy risk assessment
- **Visual Indicators**: Color-coded risk levels
- **Smart Detection**: Automatically finds privacy policies
- **Offline Capable**: Works even when main app is offline
- **Multi-language**: Supports Norwegian, German, French privacy pages

## API Integration

The extension connects to your local Privacy Policy Analyzer app:
- **Main App**: `http://localhost:8501` (Streamlit interface)
- **API Endpoint**: `http://localhost:8502/api/analyze` (Flask API)

Make sure both are running for full functionality.

## Troubleshooting

### Extension Not Working
1. Check that both Streamlit app (port 8501) and Flask API (port 8502) are running
2. Refresh the page after installing the extension
3. Check browser console for any error messages

### Privacy Policy Not Detected
1. The extension looks for keywords like "privacy", "policy", "terms"
2. Some sites may have non-standard privacy page structures
3. Use the manual analysis feature via the extension popup

### Analysis Fails
1. Extension will fall back to cached analysis if API is unavailable
2. Check network connectivity
3. Ensure the main app is running on localhost:8501

## Development

### File Structure
```
browser_extension/
├── manifest.json       # Extension configuration
├── popup.html         # Extension popup interface
├── popup.js          # Popup functionality
├── content.js        # Page content analysis
├── background.js     # Background service worker
├── styles.css        # Extension styling
└── icons/           # Extension icons
```

### Testing
1. Load extension in developer mode
2. Navigate to test privacy policy pages
3. Check browser developer tools for console logs
4. Test both automatic and manual analysis modes

## Privacy & Security

- **No Data Storage**: Extension doesn't store any personal data
- **Local Processing**: All analysis happens locally or on your server
- **No Tracking**: Extension doesn't track your browsing
- **Open Source**: All code is visible and auditable
