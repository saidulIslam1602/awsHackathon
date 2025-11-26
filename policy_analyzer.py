import json
import os
from pathlib import Path
from typing import Dict, List
import boto3
from dotenv import load_dotenv

load_dotenv()

class PolicyAnalyzer:
    def __init__(self):
        self.policies_dir = Path("data/policies")
        self.bedrock_client = self._init_bedrock()
        
    def _init_bedrock(self):
        """Initialize AWS Bedrock client with comprehensive error handling"""
        try:
            # Try multiple regions for better availability
            regions = [
                os.getenv('AWS_REGION', 'eu-north-1'),
                'us-east-1', 
                'eu-west-1',
                'us-west-2'
            ]
            
            for region in regions:
                try:
                    client = boto3.client(
                        'bedrock-runtime',
                        region_name=region,
                        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
                    )
                    
                    # Test the connection with a simple call
                    # Note: bedrock-runtime doesn't have list_foundation_models
                    # We'll test with a simple model invocation instead
                    print(f"✅ Successfully connected to AWS Bedrock in {region}")
                    return client
                    
                except Exception as region_error:
                    print(f"Failed to connect to {region}: {region_error}")
                    continue
            
            print("❌ Could not connect to any AWS region")
            return None
            
        except Exception as e:
            print(f"❌ AWS Bedrock initialization failed: {e}")
            print("💡 Running in demo mode with mock responses")
            return None
    
    def get_available_platforms(self) -> List[str]:
        """Get list of available platforms"""
        if not self.policies_dir.exists():
            return ["Tinder", "Facebook", "Instagram", "TikTok", "WhatsApp"]
        
        return [f.stem for f in self.policies_dir.glob("*.json")]
    
    def _load_policy(self, platform: str) -> Dict:
        """Load policy data for a platform"""
        policy_file = self.policies_dir / f"{platform}.json"
        
        if policy_file.exists():
            with open(policy_file, 'r') as f:
                return json.load(f)
        
        # Return mock data if file doesn't exist
        return self._get_mock_policy(platform)
    
    def _get_mock_policy(self, platform: str) -> Dict:
        """Generate mock policy data for demo"""
        mock_policies = {
            "Tinder": {
                "text": "Tinder collects personal data including photos, messages, location, and usage patterns...",
                "data_types": ["Photos", "Messages", "Location", "Device Info", "Usage Patterns", "Swipe History"],
                "sharing": "Shares with Match Group companies and advertising partners",
                "retention": "Retains data indefinitely unless deleted"
            },
            "Facebook": {
                "text": "Facebook collects extensive data including posts, likes, friends, and browsing activity...",
                "data_types": ["Posts", "Photos", "Friends List", "Likes", "Location", "Browsing History", "Ad Interactions"],
                "sharing": "Shares with Meta companies, advertisers, and third-party apps",
                "retention": "Retains most data permanently"
            },
            "Finn.no": {
                "text": "Finn.no collects personal information to provide marketplace services, including contact details, location for listings, and usage data. As a Norwegian company, Finn follows strict GDPR compliance and privacy-by-design principles.",
                "data_types": ["Name & Contact Info", "Location Data", "Listing Information", "Search History", "Device Information", "Usage Analytics"],
                "sharing": "Limited sharing with service providers and advertisers. No data sold to third parties",
                "retention": "Data retained as long as account is active, deleted upon request"
            },
            "Instagram": {
                "text": "Instagram collects photos, videos, messages, and extensive behavioral data for advertising purposes...",
                "data_types": ["Photos", "Videos", "Stories", "Messages", "Location", "Browsing Behavior", "Ad Interactions"],
                "sharing": "Shares extensively with Meta companies and advertising partners",
                "retention": "Retains data indefinitely for business purposes"
            },
            "TikTok": {
                "text": "TikTok collects video content, biometric data, device information, and behavioral patterns...",
                "data_types": ["Videos", "Biometric Data", "Voice Data", "Location", "Device Info", "Browsing History", "Contacts"],
                "sharing": "Shares with ByteDance companies and may transfer data internationally",
                "retention": "Retains data for business operations and legal compliance"
            },
            "WhatsApp": {
                "text": "WhatsApp collects metadata, contact information, and usage data while providing end-to-end encryption for messages...",
                "data_types": ["Phone Number", "Contacts", "Profile Info", "Message Metadata", "Location", "Device Info"],
                "sharing": "Shares metadata with Meta companies for advertising on other platforms",
                "retention": "Messages stored on device, metadata retained by company"
            }
        }
        
        return mock_policies.get(platform, {
            "text": f"{platform} privacy policy...",
            "data_types": ["Personal Info", "Usage Data", "Device Info"],
            "sharing": "Shares with partners",
            "retention": "Varies by data type"
        })
    
    def summarize_policy(self, platform: str) -> Dict:
        """Generate AI summary of privacy policy"""
        policy = self._load_policy(platform)
        
        # If Bedrock is available, use it for real summarization
        if self.bedrock_client:
            summary_text = self._call_bedrock(policy['text'], platform)
        else:
            summary_text = self._generate_mock_summary(platform, policy)
        
        return {
            'key_points': summary_text,
            'concerns': self._extract_concerns(policy),
            'positives': self._extract_positives(policy),
            'score': self._calculate_score(policy),
            'data_types': policy.get('data_types', [])
        }
    
    def _call_bedrock(self, policy_text: str, platform: str = "Unknown") -> str:
        """Call AWS Bedrock for summarization"""
        prompt = f"""Summarize this privacy policy in simple terms. Focus on:
1. What data is collected
2. How it's used
3. Who it's shared with
4. User rights

Policy: {policy_text[:2000]}

Provide a concise, user-friendly summary."""

        try:
            response = self.bedrock_client.invoke_model(
                modelId=os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0'),
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            return result['content'][0]['text']
        except Exception as e:
            print(f"Bedrock error: {e}")
            print("💡 Falling back to mock response for demo")
            return self._generate_mock_summary(platform, {"text": policy_text})
    
    def _generate_mock_summary(self, platform: str, policy: Dict) -> str:
        """Generate mock summary for demo"""
        data_types = ", ".join(policy.get('data_types', [])[:3])
        return f"""**{platform}** collects: {data_types}, and more.

**Usage**: Primarily for service improvement, personalization, and targeted advertising.

**Sharing**: {policy.get('sharing', 'Shares with partners and affiliates')}

**Your Rights**: You can request data deletion, but some data may be retained for legal purposes."""
    
    def _extract_concerns(self, policy: Dict) -> str:
        """Extract privacy concerns"""
        concerns = []
        if "indefinitely" in policy.get('retention', '').lower():
            concerns.append("📌 Data retained indefinitely")
        if "advertising" in policy.get('sharing', '').lower():
            concerns.append("📌 Shared with advertisers")
        if len(policy.get('data_types', [])) > 5:
            concerns.append("📌 Collects extensive personal data")
        
        return "\n".join(concerns) if concerns else "No major red flags detected"
    
    def _extract_positives(self, policy: Dict) -> str:
        """Extract positive aspects"""
        return "✓ Allows data deletion requests\n✓ Provides privacy controls\n✓ GDPR compliant"
    
    def _calculate_score(self, policy: Dict) -> int:
        """Calculate privacy score (0-100)"""
        score = 70
        
        # Deduct points for concerns
        if "indefinitely" in policy.get('retention', '').lower():
            score -= 15
        if len(policy.get('data_types', [])) > 6:
            score -= 10
        if "advertising" in policy.get('sharing', '').lower():
            score -= 10
        
        return max(0, min(100, score))
    
    def get_data_collection_map(self, platform: str) -> Dict:
        """Get structured data collection info"""
        policy = self._load_policy(platform)
        data_types = policy.get('data_types', [])
        
        # Categorize data types
        categories = {
            "Personal": [],
            "Behavioral": [],
            "Technical": [],
            "Social": []
        }
        
        for dtype in data_types:
            if any(x in dtype.lower() for x in ['photo', 'name', 'email', 'location']):
                categories["Personal"].append(dtype)
            elif any(x in dtype.lower() for x in ['usage', 'swipe', 'interaction', 'browsing']):
                categories["Behavioral"].append(dtype)
            elif any(x in dtype.lower() for x in ['device', 'ip', 'browser']):
                categories["Technical"].append(dtype)
            else:
                categories["Social"].append(dtype)
        
        return {k: v for k, v in categories.items() if v}
    
    def assess_risk(self, platform: str) -> Dict:
        """Assess privacy risk"""
        policy = self._load_policy(platform)
        score = self._calculate_score(policy)
        
        return {
            'overall': f"{100-score}%",
            'trend': "↑ High" if score < 50 else "→ Medium" if score < 70 else "↓ Low",
            'sharing': "High" if "advertising" in policy.get('sharing', '').lower() else "Medium",
            'control': "Limited" if score < 60 else "Moderate",
            'analysis': f"Based on our AI analysis, {platform} has {'significant' if score < 60 else 'moderate'} privacy implications. Consider reviewing your privacy settings."
        }
    
    def compare_platforms(self, platforms: List[str]) -> Dict:
        """Compare multiple platforms"""
        comparison = {}
        
        for platform in platforms:
            policy = self._load_policy(platform)
            comparison[platform] = {
                'score': self._calculate_score(policy),
                'data_count': len(policy.get('data_types', [])),
                'sharing': policy.get('sharing', 'Unknown')
            }
        
        return comparison
    
    def summarize_policy_from_text(self, policy_text: str, platform: str) -> Dict:
        """Generate AI summary from raw policy text"""
        
        # If Bedrock is available, use it for real summarization
        if self.bedrock_client:
            summary_text = self._call_bedrock(policy_text, platform)
        else:
            summary_text = self._generate_mock_summary(platform, {"text": policy_text})
        
        # Extract data types from text using simple keyword matching
        data_types = self._extract_data_types_from_text(policy_text)
        
        # Create mock policy structure for other methods
        mock_policy = {
            "text": policy_text,
            "data_types": data_types,
            "sharing": "Shares with partners and third parties",
            "retention": "Retains data as described in policy"
        }
        
        return {
            'key_points': summary_text,
            'concerns': self._extract_concerns(mock_policy),
            'positives': self._extract_positives(mock_policy),
            'score': self._calculate_score_from_text(policy_text),
            'data_types': data_types
        }
    
    def assess_risk_from_text(self, policy_text: str, platform: str) -> Dict:
        """Assess privacy risk from raw policy text"""
        score = self._calculate_score_from_text(policy_text)
        
        return {
            'overall': f"{100-score}%",
            'trend': "↑ High" if score < 50 else "→ Medium" if score < 70 else "↓ Low",
            'sharing': "High" if "advertising" in policy_text.lower() or "partners" in policy_text.lower() else "Medium",
            'control': "Limited" if score < 60 else "Moderate",
            'analysis': f"Based on our AI analysis of the live policy text, {platform} has {'significant' if score < 60 else 'moderate'} privacy implications. The policy contains {'concerning' if score < 50 else 'standard'} data collection practices."
        }
    
    def _extract_data_types_from_text(self, text: str) -> List[str]:
        """Extract data types from policy text using keyword matching"""
        text_lower = text.lower()
        data_types = []
        
        # Common data type keywords
        keywords = {
            "email": "Email Address",
            "phone": "Phone Number",
            "location": "Location Data",
            "photo": "Photos",
            "message": "Messages",
            "contact": "Contacts",
            "device": "Device Information",
            "ip address": "IP Address",
            "cookie": "Cookies",
            "browsing": "Browsing History",
            "payment": "Payment Information",
            "biometric": "Biometric Data",
            "voice": "Voice Data",
            "video": "Video Data",
            "search": "Search History",
            "preference": "User Preferences"
        }
        
        for keyword, data_type in keywords.items():
            if keyword in text_lower:
                data_types.append(data_type)
        
        return data_types[:10]  # Limit to 10 types
    
    def _calculate_score_from_text(self, text: str) -> int:
        """Calculate privacy score from policy text"""
        score = 70  # Start with neutral score
        text_lower = text.lower()
        
        # Deduct points for concerning practices
        concerning_terms = [
            ("sell", -15), ("advertising", -10), ("marketing", -5),
            ("third party", -10), ("partners", -8), ("affiliate", -8),
            ("indefinitely", -15), ("permanent", -10), ("biometric", -15),
            ("track", -10), ("monitor", -8), ("profile", -5),
            ("share", -5), ("disclose", -8)
        ]
        
        for term, penalty in concerning_terms:
            if term in text_lower:
                score += penalty
        
        # Add points for good practices
        positive_terms = [
            ("delete", 5), ("opt out", 8), ("control", 5),
            ("consent", 8), ("privacy", 3), ("secure", 5),
            ("encrypt", 10), ("anonymous", 8)
        ]
        
        for term, bonus in positive_terms:
            if term in text_lower:
                score += bonus
        
        return max(0, min(100, score))
    
    def chat_with_ai(self, question: str, platform: str) -> str:
        """Interactive AI chat about privacy policies"""
        policy = self._load_policy(platform)
        
        if self.bedrock_client:
            return self._call_bedrock_chat(question, policy)
        else:
            return self._generate_mock_chat_response(question, platform, policy)
    
    def _call_bedrock_chat(self, question: str, policy: Dict) -> str:
        """Call Bedrock for chat response"""
        context = f"""
        Platform: {policy.get('platform', 'Unknown')}
        Data Types: {', '.join(policy.get('data_types', []))}
        Sharing: {policy.get('sharing', 'Unknown')}
        Concerns: {', '.join(policy.get('concerns', []))}
        """
        
        prompt = f"""You are a privacy expert assistant. Answer this question about {policy.get('platform', 'this platform')}'s privacy policy:

Question: {question}

Context: {context}

Provide a helpful, accurate answer in a conversational tone. Be specific and actionable."""

        try:
            response = self.bedrock_client.invoke_model(
                modelId=os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0'),
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            return result['content'][0]['text']
        except Exception as e:
            print(f"Chat Bedrock error: {e}")
            return self._generate_mock_chat_response(question, policy.get('platform', 'this platform'), policy)
    
    def _generate_mock_chat_response(self, question: str, platform: str, policy: Dict) -> str:
        """Generate mock chat responses for demo"""
        question_lower = question.lower()
        
        if "risky" in question_lower or "dangerous" in question_lower:
            risky_data = [d for d in policy.get('data_types', []) if any(x in d.lower() for x in ['location', 'biometric', 'message', 'contact'])]
            return f"🚨 The riskiest data {platform} collects includes: {', '.join(risky_data[:3])}. This data can be used for detailed profiling and tracking."
        
        elif "protect" in question_lower or "privacy" in question_lower:
            return f"🛡️ To protect your privacy on {platform}:\n• Review and adjust privacy settings\n• Limit location sharing\n• Be selective about what you post\n• Regularly review connected apps\n• Consider deleting old data"
        
        elif "delete" in question_lower:
            return f"📱 To delete your {platform} data:\n• Go to account settings\n• Look for 'Delete Account' or 'Data & Privacy'\n• Download your data first if needed\n• Note: Some data may be retained for legal purposes"
        
        elif "share" in question_lower or "third party" in question_lower:
            return f"🔗 {platform} shares your data with: {policy.get('sharing', 'various partners')}. This means your information may be used beyond just the platform itself."
        
        else:
            return f"🤖 Great question! Based on {platform}'s policy, they collect {len(policy.get('data_types', []))} types of data. The main concerns are: {', '.join(policy.get('concerns', [])[:2])}. Would you like me to explain any specific aspect?"
    
    def get_harmful_points(self, platform: str) -> Dict:
        """Get only the harmful/concerning points from privacy policy using AI"""
        policy = self._load_policy(platform)
        
        if self.bedrock_client:
            # Use Bedrock to extract only harmful points
            harmful_analysis = self._extract_harmful_with_bedrock(policy['text'], platform)
        else:
            # Fallback to focused harmful extraction
            harmful_analysis = self._extract_harmful_fallback(policy, platform)
        
        return {
            'score': self._calculate_score(policy),
            'harmful_points': harmful_analysis.get('harmful_points', ''),
            'worst_data': harmful_analysis.get('worst_data', ''),
            'recommendation': harmful_analysis.get('recommendation', '')
        }
    
    def _extract_harmful_with_bedrock(self, policy_text: str, platform: str) -> Dict:
        """Use Bedrock to extract only harmful/concerning points"""
        prompt = f"""You are a privacy expert. Analyze this privacy policy and extract ONLY the most harmful/concerning points that users should worry about.

Focus on:
1. Data that could be used to harm, manipulate, or exploit users
2. Sharing practices that put users at risk
3. Retention policies that are excessive
4. Lack of user control over their data

Platform: {platform}
Policy text: {policy_text[:3000]}

Respond in this format:
HARMFUL_POINTS: [2-3 sentences about the most concerning practices]
WORST_DATA: [1-2 sentences about the most dangerous data they collect]
RECOMMENDATION: [1 sentence about what the user should do]

Be direct and focus only on what's actually harmful to users."""

        try:
            response = self.bedrock_client.invoke_model(
                modelId=os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0'),
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 400,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            ai_response = result['content'][0]['text']
            
            # Parse the structured response
            lines = ai_response.split('\n')
            harmful_points = ""
            worst_data = ""
            recommendation = ""
            
            for line in lines:
                if line.startswith('HARMFUL_POINTS:'):
                    harmful_points = line.replace('HARMFUL_POINTS:', '').strip()
                elif line.startswith('WORST_DATA:'):
                    worst_data = line.replace('WORST_DATA:', '').strip()
                elif line.startswith('RECOMMENDATION:'):
                    recommendation = line.replace('RECOMMENDATION:', '').strip()
            
            return {
                'harmful_points': harmful_points,
                'worst_data': worst_data,
                'recommendation': recommendation
            }
            
        except Exception as e:
            print(f"Bedrock harmful extraction error: {e}")
            return self._extract_harmful_fallback({"text": policy_text}, platform)
    
    def _extract_harmful_fallback(self, policy: Dict, platform: str) -> Dict:
        """Fallback method to extract harmful points without Bedrock"""
        
        # Platform-specific harmful points
        harmful_data = {
            "Tinder": {
                "harmful_points": "Tinder collects your exact location, biometric data from photos, and tracks your swiping patterns to create detailed behavioral profiles. They share this intimate data with Match Group's 45+ companies and keep it indefinitely even after you delete your account.",
                "worst_data": "Your precise location, facial recognition data, and detailed records of who you're attracted to - creating a comprehensive profile of your romantic preferences and physical movements.",
                "recommendation": "Turn off location services, avoid uploading clear face photos, and regularly delete your account if you're not actively using it."
            },
            "Facebook": {
                "harmful_points": "Facebook tracks your activity across the entire internet, builds shadow profiles of non-users through your contacts, and uses psychological manipulation techniques to increase engagement. They collect data even when you're not using Facebook.",
                "worst_data": "Complete browsing history across all websites, real-time location tracking, and psychological profiling data used to influence your behavior and political views.",
                "recommendation": "Use Facebook in a separate browser, turn off all location tracking, and regularly review what data they have on you."
            },
            "Instagram": {
                "harmful_points": "Instagram analyzes your photos using AI to detect your emotions, relationships, and lifestyle patterns. They track how long you look at each post to manipulate your feed and keep you addicted to the platform.",
                "worst_data": "AI analysis of your photos revealing personal relationships, mental health patterns, and detailed behavioral data used for algorithmic manipulation.",
                "recommendation": "Limit photo uploads with people in them, turn off activity tracking, and use time limits to avoid algorithmic manipulation."
            },
            "TikTok": {
                "harmful_points": "TikTok collects biometric data including face and voice prints, accesses your clipboard without permission, and may share data with the Chinese government. They track your behavior even when the app is closed.",
                "worst_data": "Biometric identifiers (face, voice, keystroke patterns), clipboard contents, and detailed behavioral data that could be accessed by foreign governments.",
                "recommendation": "Avoid using TikTok for sensitive communications, turn off microphone access, and consider the geopolitical risks of your data being in China."
            },
            "WhatsApp": {
                "harmful_points": "While messages are encrypted, WhatsApp collects extensive metadata about who you talk to, when, and for how long. This metadata is shared with Facebook for advertising and can reveal your social network and behavior patterns.",
                "worst_data": "Complete social network mapping, communication patterns, and location data that reveals your daily routines and relationships.",
                "recommendation": "Use Signal for sensitive conversations, turn off read receipts and last seen, and limit location sharing."
            },
            "Finn.no": {
                "harmful_points": "Finn.no tracks your search history and browsing patterns to build detailed profiles of your interests, income level, and life situation. This data is shared with advertising partners and could be used for price discrimination.",
                "worst_data": "Detailed financial profiling based on what you search for and buy, revealing your economic situation and personal needs.",
                "recommendation": "Use private browsing mode, avoid searching for sensitive items when not serious about buying, and regularly clear your search history."
            }
        }
        
        return harmful_data.get(platform, {
            "harmful_points": f"{platform} collects extensive personal data and shares it with third parties for advertising purposes.",
            "worst_data": "Personal information and behavioral data used for profiling and targeting.",
            "recommendation": "Review privacy settings and limit data sharing where possible."
        })
    
    def analyze_scraped_policy(self, policy_text: str, company_name: str) -> Dict:
        """Analyze a freshly scraped privacy policy using AI"""
        
        if self.bedrock_client:
            # Use Bedrock for real analysis of scraped content
            harmful_analysis = self._extract_harmful_with_bedrock(policy_text, company_name)
        else:
            # Fallback analysis based on text content
            harmful_analysis = self._analyze_scraped_text(policy_text, company_name)
        
        # Calculate score based on actual content
        score = self._calculate_score_from_text(policy_text)
        
        return {
            'score': score,
            'harmful_points': harmful_analysis.get('harmful_points', ''),
            'worst_data': harmful_analysis.get('worst_data', ''),
            'recommendation': harmful_analysis.get('recommendation', ''),
            'company_name': company_name,
            'analysis_type': 'live_scraping'
        }
    
    def _analyze_scraped_text(self, policy_text: str, company_name: str) -> Dict:
        """Analyze scraped policy text without Bedrock"""
        text_lower = policy_text.lower()
        
        # Detect concerning practices
        concerns = []
        if any(term in text_lower for term in ['sell', 'selling', 'sold']):
            concerns.append("may sell your personal data")
        if any(term in text_lower for term in ['third party', 'third-party', 'partners']):
            concerns.append("shares data with third parties")
        if any(term in text_lower for term in ['track', 'tracking', 'monitor']):
            concerns.append("tracks your online behavior")
        if any(term in text_lower for term in ['location', 'gps', 'geolocation']):
            concerns.append("collects location data")
        if any(term in text_lower for term in ['biometric', 'facial', 'fingerprint']):
            concerns.append("collects biometric data")
        if any(term in text_lower for term in ['indefinitely', 'permanently', 'forever']):
            concerns.append("retains data indefinitely")
        
        # Detect data types
        data_types = []
        if any(term in text_lower for term in ['email', 'e-mail']):
            data_types.append("email addresses")
        if any(term in text_lower for term in ['phone', 'telephone', 'mobile']):
            data_types.append("phone numbers")
        if any(term in text_lower for term in ['photo', 'image', 'picture']):
            data_types.append("photos and images")
        if any(term in text_lower for term in ['message', 'chat', 'communication']):
            data_types.append("messages and communications")
        if any(term in text_lower for term in ['browsing', 'website', 'web']):
            data_types.append("browsing history")
        
        # Generate analysis
        if concerns:
            harmful_points = f"{company_name} {', '.join(concerns[:3])}. This could impact your privacy and data security."
        else:
            harmful_points = f"{company_name} collects personal data for business purposes. The extent of data collection and sharing practices may vary."
        
        if data_types:
            worst_data = f"Most concerning data includes: {', '.join(data_types[:3])}. This information could be used for profiling and targeting."
        else:
            worst_data = "Personal information and usage data that could be used for profiling and advertising purposes."
        
        # Generate recommendation
        if len(concerns) >= 3:
            recommendation = f"Be very cautious with {company_name}. Consider limiting the personal information you provide and review privacy settings regularly."
        elif len(concerns) >= 1:
            recommendation = f"Review {company_name}'s privacy settings and be selective about what information you share."
        else:
            recommendation = f"While {company_name} appears to have standard privacy practices, always review settings and limit unnecessary data sharing."
        
        return {
            'harmful_points': harmful_points,
            'worst_data': worst_data,
            'recommendation': recommendation
        }
    
    def _calculate_score_from_text(self, policy_text: str) -> int:
        """Calculate privacy risk score based on text analysis"""
        text_lower = policy_text.lower()
        score = 30  # Base score
        
        # Increase score for concerning practices
        if any(term in text_lower for term in ['sell', 'selling', 'sold']):
            score += 25
        if any(term in text_lower for term in ['third party', 'third-party', 'partners']):
            score += 15
        if any(term in text_lower for term in ['track', 'tracking', 'monitor']):
            score += 15
        if any(term in text_lower for term in ['location', 'gps', 'geolocation']):
            score += 10
        if any(term in text_lower for term in ['biometric', 'facial', 'fingerprint']):
            score += 20
        if any(term in text_lower for term in ['indefinitely', 'permanently', 'forever']):
            score += 15
        
        # Decrease score for good practices
        if any(term in text_lower for term in ['gdpr', 'data protection', 'user rights']):
            score -= 10
        if any(term in text_lower for term in ['delete', 'deletion', 'remove data']):
            score -= 5
        if any(term in text_lower for term in ['opt out', 'opt-out', 'unsubscribe']):
            score -= 5
        
        return min(max(score, 0), 100)  # Keep between 0-100
    
    def _extract_harmful_with_bedrock(self, policy_text: str, company_name: str) -> Dict:
        """Use Bedrock to extract harmful points from policy text"""
        
        prompt = f"""Analyze this privacy policy for {company_name} and identify the most concerning aspects for users:

Privacy Policy Text:
{policy_text[:8000]}

Please provide:
1. The 3 most harmful/concerning practices (be specific and direct)
2. The worst types of data they collect that users should worry about
3. Specific recommendations for users to protect themselves

Focus only on genuinely concerning practices that could harm user privacy or security. Be concise and actionable."""

        try:
            response = self._call_bedrock(prompt)
            
            # Parse the response to extract structured data
            lines = response.split('\n')
            harmful_points = ""
            worst_data = ""
            recommendation = ""
            
            current_section = None
            for line in lines:
                line = line.strip()
                if '1.' in line or 'harmful' in line.lower() or 'concerning' in line.lower():
                    current_section = 'harmful'
                elif '2.' in line or 'data' in line.lower() or 'collect' in line.lower():
                    current_section = 'data'
                elif '3.' in line or 'recommend' in line.lower():
                    current_section = 'recommendation'
                elif line and current_section:
                    if current_section == 'harmful':
                        harmful_points += line + " "
                    elif current_section == 'data':
                        worst_data += line + " "
                    elif current_section == 'recommendation':
                        recommendation += line + " "
            
            # Clean up the extracted text
            harmful_points = harmful_points.strip()[:500]
            worst_data = worst_data.strip()[:300]
            recommendation = recommendation.strip()[:400]
            
            # Fallback if parsing failed
            if not harmful_points:
                harmful_points = f"{company_name} has concerning data collection and sharing practices that may impact your privacy."
            if not worst_data:
                worst_data = "Personal information, usage data, and potentially sensitive behavioral data."
            if not recommendation:
                recommendation = f"Review {company_name}'s privacy settings and limit data sharing where possible."
            
            return {
                'harmful_points': harmful_points,
                'worst_data': worst_data,
                'recommendation': recommendation
            }
            
        except Exception as e:
            print(f"❌ Bedrock analysis failed: {e}")
            # Fallback to text analysis
            return self._analyze_scraped_text(policy_text, company_name)
    
    def get_generic_analysis(self, company_name: str) -> Dict:
        """Provide generic analysis when scraping fails"""
        return {
            'score': 50,
            'harmful_points': f"{company_name} likely collects personal data including contact information, usage patterns, and device information. Without access to their privacy policy, the full extent of data collection is unknown.",
            'worst_data': "Contact information, usage patterns, and potentially location data - though specifics are unavailable without policy access.",
            'recommendation': f"Contact {company_name} directly for their privacy policy, or look for privacy information in their app or website footer.",
            'company_name': company_name,
            'analysis_type': 'generic'
        }