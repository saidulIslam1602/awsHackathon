import streamlit as st
import json
from pathlib import Path
from policy_analyzer import PolicyAnalyzer
from scraper import PolicyScraper
from database import db
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time

# Page config
st.set_page_config(
    page_title="Privacy Policy Analyzer",
    page_icon="🔒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Clean white background with black text
st.markdown("""
<style>
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* White background for everything */
    .stApp {
        background-color: white !important;
    }
    
    .main {
        background-color: white !important;
        padding: 2rem;
        max-width: 800px;
        margin: 0 auto;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Clean buttons */
    .stButton > button {
        background: #dc3545;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
        margin: 1rem 0;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: #c82333;
        transform: translateY(-1px);
    }
    
    /* Platform cards */
    .platform-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #e0e0e0;
        margin: 0.75rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .platform-card:hover {
        border-color: #dc3545;
        box-shadow: 0 4px 12px rgba(220, 53, 69, 0.15);
    }
    
    /* Warning box */
    .warning-box {
        background: white;
        border: 2px solid #ffc107;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }
    
    /* Danger box */
    .danger-box {
        background: white;
        border: 2px solid #dc3545;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }
    
    /* Score styling */
    .score-bad { color: #dc3545; font-weight: bold; font-size: 2em; }
    .score-ok { color: #ffc107; font-weight: bold; font-size: 2em; }
    .score-good { color: #28a745; font-weight: bold; font-size: 2em; }
    
    /* Black text for everything */
    h1, h2, h3, h4, h5, h6 {
        color: black !important;
        font-weight: 600 !important;
    }
    
    p, li, div, span {
        color: black !important;
        line-height: 1.6 !important;
        font-size: 1rem !important;
    }
    
    .big-text {
        color: black !important;
        font-size: 1.1rem !important;
        font-weight: 500 !important;
    }
    
    /* Ensure all content areas have white background */
    .element-container {
        background-color: white !important;
    }
    
    /* Header styling with white background */
    .header-section {
        background-color: white !important;
        color: black !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
@st.cache_resource
def get_analyzer():
    return PolicyAnalyzer()

analyzer = get_analyzer()

# Flask API for browser extension
flask_app = Flask(__name__)
CORS(flask_app)

@flask_app.route('/api/analyze', methods=['POST'])
def api_analyze():
    try:
        data = request.json
        analysis_type = data.get('analysis_type', 'policy')
        
        if analysis_type == 'company':
            # Company website analysis
            company_website = data.get('company_website') or data.get('url', '')
            
            if not company_website:
                return jsonify({'error': 'No company website provided'}), 400
            
            # Clean up URL
            if company_website.startswith('https://'):
                company_website = company_website.replace('https://', '')
            if company_website.startswith('http://'):
                company_website = company_website.replace('http://', '')
            
            # Use scraper to analyze company website
            scraper = PolicyScraper()
            scrape_result = scraper.scrape_company_website(company_website)
            
            if scrape_result['scraped']:
                # Successfully scraped - analyze with AI
                analysis = analyzer.analyze_scraped_policy(
                    scrape_result['text'], 
                    scrape_result['company_name']
                )
                analysis['source'] = 'live_scraping'
                analysis['privacy_url'] = scrape_result['privacy_url']
                analysis['website'] = company_website
            else:
                # Scraping failed - use generic analysis
                analysis = analyzer.get_generic_analysis(scrape_result['company_name'])
                analysis['source'] = 'generic'
                analysis['website'] = company_website
            
            # Save to database
            try:
                db.save_analysis(analysis, 'browser_extension')
                db.update_user_session('browser_extension', scrape_result['company_name'])
            except Exception as e:
                print(f"Database save error: {e}")
            
            return jsonify(analysis)
        
        else:
            # Regular policy text analysis
            platform = data.get('platform', 'Unknown Platform')
            policy_text = data.get('text', '')
            
            if policy_text:
                # Analyze provided text
                analysis = analyzer.analyze_text_for_harmful_points(policy_text, platform)
            else:
                # Use predefined platform analysis
                analysis = analyzer.get_harmful_points(platform)
            
            return jsonify(analysis)
        
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/health', methods=['GET'])
def api_health():
    return jsonify({'status': 'ok', 'message': 'Privacy Policy Analyzer API is running'})

@flask_app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        data = request.json
        question = data.get('question', '')
        platform = data.get('platform', 'Unknown Platform')
        
        if not question.strip():
            return jsonify({'error': 'Question is required'}), 400
        
        # Use the analyzer's chat functionality
        response = analyzer.chat_with_ai(question, platform)
        
        return jsonify({
            'response': response,
            'platform': platform,
            'question': question
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Start Flask API in background thread
def start_flask_api():
    flask_app.run(host='0.0.0.0', port=8502, debug=False)

# Start API server
if 'flask_started' not in st.session_state:
    st.session_state.flask_started = True
    api_thread = threading.Thread(target=start_flask_api, daemon=True)
    api_thread.start()
    time.sleep(1)  # Give Flask time to start

# Platform data - simplified
PLATFORMS = {
    "Tinder": {"icon": "🔥", "category": "Dating"},
    "Facebook": {"icon": "📘", "category": "Social Media"},
    "Instagram": {"icon": "📷", "category": "Social Media"},
    "TikTok": {"icon": "🎵", "category": "Social Media"},
    "WhatsApp": {"icon": "💬", "category": "Messaging"},
    "Finn.no": {"icon": "🏠", "category": "Marketplace"},
}

# Session state
if 'selected_platform' not in st.session_state:
    st.session_state.selected_platform = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'session_id' not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

# Header
st.markdown("""
<div style="text-align: center; padding: 2rem 0; background-color: white;">
    <h1 style="font-size: 2.5rem; margin: 0; color: black;">🔒 Privacy Analyzer</h1>
    <p style="font-size: 1.2rem; color: black; margin: 0.5rem 0 0 0;">
        Find out what's actually dangerous in privacy policies
    </p>
</div>
""", unsafe_allow_html=True)

# Main content
if st.session_state.selected_platform is None:
    # Add company website input section
    st.markdown("### 🌐 Analyze Any Company's Privacy Policy")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        company_website = st.text_input(
            "Enter company website:",
            placeholder="e.g., spotify.com, netflix.com, airbnb.com",
            help="Enter any company website and we'll automatically find and analyze their privacy policy"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
        if st.button("🔍 Analyze Website", type="primary"):
            if company_website:
                st.session_state.selected_platform = "custom"
                st.session_state.custom_website = company_website
                st.rerun()
            else:
                st.error("Please enter a website URL")
    
    st.markdown("---")
    
    # Platform selection
    st.markdown("### Or choose a popular platform:")
    
    cols = st.columns(3)
    for i, (platform, info) in enumerate(PLATFORMS.items()):
        with cols[i % 3]:
            if st.button(f"{info['icon']} {platform}", key=platform):
                st.session_state.selected_platform = platform
                st.rerun()

else:
    # Individual platform analysis
    platform = st.session_state.selected_platform
    
    # Back button
    if st.button("← Back to selection"):
        st.session_state.selected_platform = None
        st.session_state.analysis_results = None
        if 'custom_website' in st.session_state:
            del st.session_state.custom_website
        st.rerun()
    
    # Handle custom website vs predefined platform
    if platform == "custom" and 'custom_website' in st.session_state:
        # Custom website analysis
        website = st.session_state.custom_website
        
        # Extract company name from website
        try:
            from urllib.parse import urlparse
            domain = urlparse(f"https://{website}" if not website.startswith('http') else website).netloc
            company_name = domain.replace('www.', '').split('.')[0].capitalize()
        except:
            company_name = website
        
        # Custom website header
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border: 2px solid #e0e0e0; border-radius: 12px; margin: 2rem 0;">
            <h1 style="font-size: 3rem; margin: 0;">🌐</h1>
            <h2 style="margin: 0.5rem 0; color: black;">{company_name}</h2>
            <p style="color: black; margin: 0;">{website}</p>
        </div>
        """, unsafe_allow_html=True)
        
        platform_display_name = company_name
        
    else:
        # Predefined platform
        platform_info = PLATFORMS[platform]
        
        # Platform header
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border: 2px solid #e0e0e0; border-radius: 12px; margin: 2rem 0;">
            <h1 style="font-size: 3rem; margin: 0;">{platform_info['icon']}</h1>
            <h2 style="margin: 0.5rem 0; color: black;">{platform}</h2>
            <p style="color: black; margin: 0;">{platform_info['category']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        platform_display_name = platform
    
    # Analyze button
    if st.button("🔍 Analyze Privacy Risks"):
        if platform == "custom" and 'custom_website' in st.session_state:
            # Custom website analysis with real scraping
            website = st.session_state.custom_website
            
            with st.spinner(f"🌐 Finding privacy policy on {website}..."):
                # Use scraper to find and analyze privacy policy
                scraper = PolicyScraper()
                scrape_result = scraper.scrape_company_website(website)
                
                if scrape_result['scraped']:
                    # Successfully scraped - analyze with AI
                    with st.spinner("🤖 AI is analyzing the privacy policy..."):
                        analysis = analyzer.analyze_scraped_policy(
                            scrape_result['text'], 
                            scrape_result['company_name']
                        )
                        analysis['source'] = 'live_scraping'
                        analysis['privacy_url'] = scrape_result['privacy_url']
                        analysis['company_website'] = scrape_result['company_website']
                        analysis['website'] = website
                        
                        # Save to database
                        try:
                            db.save_analysis(analysis, st.session_state.get('session_id', 'web_user'))
                            db.update_user_session(st.session_state.get('session_id', 'web_user'), 
                                                 scrape_result['company_name'])
                        except Exception as e:
                            print(f"Database save error: {e}")
                        
                        st.session_state.analysis_results = analysis
                else:
                    # Scraping failed - show error with fallback
                    st.error(f"❌ Could not find or access privacy policy on {website}")
                    st.info(f"Error: {scrape_result.get('error', 'Unknown error')}")
                    
                    # Offer fallback analysis
                    if st.button("📋 Use Generic Analysis Instead"):
                        analysis = analyzer.get_generic_analysis(scrape_result['company_name'])
                        analysis['source'] = 'generic'
                        st.session_state.analysis_results = analysis
        else:
            # Predefined platform analysis
            with st.spinner("🤖 AI is reading the privacy policy..."):
                analysis = analyzer.get_harmful_points(platform)
                analysis['source'] = 'predefined'
                st.session_state.analysis_results = analysis
    
    # Show results
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        
        # Show data source indicator
        source = results.get('source', 'unknown')
        if source == 'live_scraping':
            st.success(f"✅ **Live Analysis** - Scraped from: {results.get('privacy_url', 'privacy policy')}")
        elif source == 'predefined':
            st.info("📋 **Cached Analysis** - Using our curated data")
        elif source == 'generic':
            st.warning("⚠️ **Generic Analysis** - Privacy policy not accessible")
        
        # Privacy Score - Big and prominent
        score = results['score']
        if score >= 70:
            score_class = "score-good"
            score_text = "Low Risk"
            score_color = "#28a745"
        elif score >= 50:
            score_class = "score-ok"
            score_text = "Medium Risk"
            score_color = "#ffc107"
        else:
            score_class = "score-bad"
            score_text = "High Risk"
            score_color = "#dc3545"
        
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 12px; 
                    border: 3px solid {score_color}; margin: 2rem 0;">
            <h3 style="margin: 0; color: #212529;">Privacy Risk Score</h3>
            <div class="{score_class}">{score}/100</div>
            <p style="font-size: 1.2rem; color: {score_color}; font-weight: 600; margin: 0;">
                {score_text}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Main harmful points - This is what users need to see
        if results.get('harmful_points'):
            st.markdown(f"""
            <div class="danger-box">
                <h3 style="color: #721c24; margin-top: 0;">🚨 What You Should Worry About</h3>
                <div class="big-text">
                    {results['harmful_points']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Quick summary of most concerning data
        if results.get('worst_data'):
            st.markdown(f"""
            <div class="warning-box">
                <h4 style="color: #856404; margin-top: 0;">📊 Most Concerning Data They Collect</h4>
                <div class="big-text">
                    {results['worst_data']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Simple recommendation
        if results.get('recommendation'):
            st.markdown(f"""
            <div style="background: white; border: 2px solid #17a2b8; border-radius: 8px; 
                        padding: 1.5rem; margin: 1.5rem 0;">
                <h4 style="color: black; margin-top: 0;">💡 What Should You Do?</h4>
                <div class="big-text" style="color: black;">
                    {results['recommendation']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Add Chat Interface after analysis results
        st.markdown("---")
        st.markdown("### 💬 Ask Questions About This Privacy Policy")
        
        # Initialize chat history in session state
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Chat input
        user_question = st.text_input(
            "Ask anything about this privacy policy:",
            placeholder="e.g., 'Does this app track my location?', 'Who do they share my data with?', 'What are my rights?'",
            key="chat_input"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🤖 Ask AI", key="ask_button"):
                if user_question.strip():
                    # Get AI response
                    with st.spinner("🤖 AI is thinking..."):
                        try:
                            ai_response = analyzer.chat_with_ai(user_question, platform_display_name)
                            
                            # Add to chat history
                            st.session_state.chat_history.append({
                                'question': user_question,
                                'response': ai_response,
                                'platform': platform_display_name
                            })
                            
                            # Clear input
                            st.session_state.chat_input = ""
                            st.rerun()
                        except Exception as e:
                            st.error(f"Chat error: {e}")
                else:
                    st.warning("Please enter a question first!")
        
        with col2:
            if st.button("🗑️ Clear Chat", key="clear_chat"):
                st.session_state.chat_history = []
                st.rerun()
        
        # Display chat history
        if st.session_state.chat_history:
            st.markdown("#### 💭 Chat History")
            
            # Show recent chats (last 5)
            recent_chats = st.session_state.chat_history[-5:]
            
            for i, chat in enumerate(reversed(recent_chats)):
                with st.expander(f"Q: {chat['question'][:50]}{'...' if len(chat['question']) > 50 else ''}", expanded=(i==0)):
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;">
                        <strong>❓ Your Question:</strong><br>
                        {chat['question']}
                    </div>
                    <div style="background: #e3f2fd; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;">
                        <strong>🤖 AI Response:</strong><br>
                        {chat['response']}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Suggested questions
        st.markdown("#### 💡 Suggested Questions")
        suggested_questions = [
            "What's the riskiest data they collect?",
            "Who do they share my data with?", 
            "Do they track my location?",
            "How can I delete my data?",
            "What are my privacy rights?",
            "Do they use my data for advertising?"
        ]
        
        cols = st.columns(2)
        for i, suggestion in enumerate(suggested_questions):
            with cols[i % 2]:
                if st.button(f"💬 {suggestion}", key=f"suggest_{i}"):
                    # Auto-fill the question
                    st.session_state.chat_input = suggestion
                    st.rerun()
    
    else:
        # Call to action
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background-color: white; color: black;">
            <h3 style="color: black;">👆 Click the button above to see what's dangerous</h3>
            <p style="font-size: 1.1rem; color: black;">
                Our AI will read the privacy policy and highlight only the concerning parts.
            </p>
        </div>
        """, unsafe_allow_html=True)

# Database Statistics (Admin Section)
if st.checkbox("🔧 Show Admin Statistics", value=False):
    st.markdown("---")
    st.markdown("### 📊 Database Statistics")
    
    try:
        stats = db.get_dashboard_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Analyses", stats['total_analyses'])
        with col2:
            st.metric("Unique Websites", stats['unique_websites'])
        with col3:
            st.metric("Avg Risk Score", "{}/100".format(stats['avg_risk_score']))
        with col4:
            st.metric("Today's Analyses", stats['analyses_today'])
        
        # Recent analysis history
        st.markdown("#### 📈 Recent Analysis History")
        history = db.get_analysis_history(10)
        
        if history:
            import pandas as pd
            df = pd.DataFrame(history)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No analysis history yet")
        
        # Platform statistics
        st.markdown("#### 🏆 Platform Statistics")
        platform_stats = db.get_platform_stats()
        
        if platform_stats:
            df_platforms = pd.DataFrame(platform_stats)
            st.dataframe(df_platforms, use_container_width=True)
        else:
            st.info("No platform statistics yet")
            
    except Exception as e:
        st.error(f"Database error: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; background-color: white; color: black;">
    <p style="margin: 0; color: black;">🏆 AWS Hackathon 2025 | Built by Saidul and Almaz and Sakib</p>
</div>
""", unsafe_allow_html=True)