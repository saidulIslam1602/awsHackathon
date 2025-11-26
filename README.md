# 🕵️ They Just Clicked 'Accept' - Privacy Policy Assistant

> **🏆 AWS Experience North GenAI Hackathon 2025 - Oslo**  
> *Making privacy policies human-readable with AI*

[![Demo](https://img.shields.io/badge/🚀-Live%20Demo-blue)](https://streamlit.io) [![AWS](https://img.shields.io/badge/⚡-AWS%20Bedrock-orange)](https://aws.amazon.com/bedrock/) [![License](https://img.shields.io/badge/📄-MIT-green)](LICENSE)

## 🚨 The Problem

**91% of people** accept terms & conditions without reading them. Meanwhile:
- Apps collect **3,000+ data points** per person daily
- Privacy policies average **2,500+ words** (8-minute read)
- Legal language is incomprehensible to most users
- **$4.4 billion** in GDPR fines issued due to privacy violations

## 💡 Our Solution

An **AI-powered privacy assistant** that transforms complex legal documents into actionable insights:

### ✨ Key Features
- 🤖 **AI Chat Assistant** - Ask questions about any privacy policy
- 📊 **Visual Data Maps** - See exactly what data is collected
- ⚖️ **Risk Assessment** - AI-generated privacy scores (0-100)
- 🔍 **Platform Comparison** - Compare privacy practices side-by-side
- 📈 **Real-time Analysis** - Instant policy summarization (<3 seconds)

## 🏗️ Architecture

```
┌─────────────────┐
│   Streamlit UI  │  (Interactive Dashboard + Chat)
└────────┬────────┘
         │
┌────────▼────────┐
│  MCP Server     │  (Policy Retrieval & Processing)
│  + RAG Engine   │
└────────┬────────┘
         │
┌────────▼────────┐
│  AWS Bedrock    │  (Claude LLM)
│  + Vector DB    │
└────────┬────────┘
         │
┌────────▼────────┐
│  Policy Store   │  (Pre-scraped policies)
└─────────────────┘
```

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/your-username/privacy-policy-assistant
cd privacy-policy-assistant

# Install dependencies
pip install -r requirements.txt

# Set up AWS credentials (optional - works with demo mode)
cp .env.example .env
# Add your AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

# Run the app
streamlit run app.py
```

🌐 **Live Demo**: [privacy-assistant.streamlit.app](https://privacy-assistant.streamlit.app)

## 📸 Screenshots

### 🤖 AI-Powered Analysis
![AI Analysis](docs/screenshots/ai-analysis.png)
*Get instant, human-readable summaries of complex privacy policies*

### 📊 Interactive Data Visualization  
![Data Visualization](docs/screenshots/data-viz.png)
*See exactly what data each platform collects with interactive charts*

### ⚖️ Privacy Risk Assessment
![Risk Assessment](docs/screenshots/risk-assessment.png)
*AI-generated privacy scores and risk analysis*

### 🔍 Platform Comparison
![Platform Comparison](docs/screenshots/comparison.png)
*Compare privacy practices across multiple platforms*

## 🛠️ Tech Stack
- **LLM**: AWS Bedrock (Claude)
- **Backend**: Python + MCP Server
- **Frontend**: Streamlit
- **Data**: Pre-scraped privacy policies (JSON)
- **Visualization**: Plotly/NetworkX

## 📊 Features
1. **Policy Summarizer**: Upload or select a platform → get instant summary
2. **Data Map**: Visual graph showing what data each platform collects
3. **Comparison Tool**: Compare privacy practices across platforms
4. **Risk Score**: AI-generated privacy risk assessment

## 👥 Team
- Almaz Ermilov
- Saidul

## 📅 Hackathon: 26 November 2025
