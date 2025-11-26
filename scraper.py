"""
Enhanced Privacy Policy Scraper
Automatically finds and scrapes privacy policies from any company website
"""

import requests
from bs4 import BeautifulSoup
import json
from pathlib import Path
from typing import Dict, List
import re
from urllib.parse import urljoin, urlparse
import time

class PolicyScraper:
    """Enhanced scraper that finds and analyzes privacy policies from any company website"""
    
    # Known privacy policy URLs for major platforms
    KNOWN_PRIVACY_URLS = {
        'spotify.com': 'https://www.spotify.com/legal/privacy-policy/',
        'netflix.com': 'https://help.netflix.com/legal/privacy',
        'github.com': 'https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement',
        'airbnb.com': 'https://www.airbnb.com/terms/privacy_policy',
        'discord.com': 'https://discord.com/privacy'
    }
    
    # Common privacy policy URL patterns
    PRIVACY_URL_PATTERNS = [
        '/privacy',
        '/privacy-policy',
        '/privacy-notice',
        '/privacy.html',
        '/legal/privacy',
        '/legal/privacy-policy',
        '/terms/privacy',
        '/policy/privacy',
        '/about/privacy',
        '/help/privacy',
        '/support/privacy',
        '/info/privacy',
        '/personvern',  # Norwegian
        '/datenschutz',  # German
        '/confidentialite'  # French
    ]
    
    # Keywords to look for in links
    PRIVACY_KEYWORDS = [
        'privacy', 'policy', 'personvern', 'datenschutz', 
        'confidentialité', 'privacidad', 'privacidade'
    ]
    
    def __init__(self):
        self.output_dir = Path("data/policies")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def scrape_policy(self, platform: str, url: str) -> Dict:
        """Scrape a single privacy policy"""
        print(f"Scraping {platform}...")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            text = ' '.join(text.split())
            
            # Limit to first 5000 chars for processing
            text = text[:5000]
            
            return {
                "platform": platform,
                "url": url,
                "text": text,
                "scraped": True
            }
            
        except Exception as e:
            print(f"Error scraping {platform}: {e}")
            return {
                "platform": platform,
                "url": url,
                "text": f"Failed to scrape policy for {platform}",
                "scraped": False,
                "error": str(e)
            }
    
    def scrape_all(self):
        """Scrape all policies"""
        results = {}
        
        for platform, url in self.POLICY_URLS.items():
            result = self.scrape_policy(platform, url)
            results[platform] = result
            
            # Save individual file
            output_file = self.output_dir / f"{platform}_raw.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Saved {platform} to {output_file}")
        
        return results
    
    def scrape_company_website(self, company_website: str) -> Dict:
        """
        Automatically find and scrape privacy policy from any company website
        
        Args:
            company_website: The main company website URL (e.g., "https://example.com")
            
        Returns:
            Dict containing scraped policy data and metadata
        """
        print(f"🔍 Analyzing {company_website}...")
        
        # Normalize URL
        if not company_website.startswith(('http://', 'https://')):
            company_website = 'https://' + company_website
        
        try:
            # Step 1: Find privacy policy URL
            privacy_urls = self._find_privacy_policy_urls(company_website)
            
            if not privacy_urls:
                return {
                    "company_website": company_website,
                    "company_name": self._extract_company_name(company_website),
                    "privacy_url": None,
                    "scraped": False,
                    "error": "No privacy policy URL found",
                    "text": "Could not locate privacy policy on this website"
                }
            
            # Step 2: Try to scrape privacy policy URLs in order of preference
            policy_data = None
            successful_url = None
            
            for url in privacy_urls[:3]:  # Try top 3 URLs
                print(f"📄 Trying privacy policy: {url}")
                policy_data = self._scrape_privacy_content(url)
                
                if policy_data.get('scraped'):
                    successful_url = url
                    print(f"✅ Successfully scraped from: {url}")
                    break
                else:
                    print(f"❌ Failed to scrape from: {url} - {policy_data.get('error')}")
            
            # If no URL worked, use the last attempt's data
            if not policy_data:
                policy_data = {"scraped": False, "error": "No privacy policy URLs accessible", "text": ""}
                successful_url = privacy_urls[0] if privacy_urls else None
            
            # Step 3: Extract company information
            company_name = self._extract_company_name(company_website)
            
            return {
                "company_website": company_website,
                "company_name": company_name,
                "privacy_url": successful_url,
                "scraped": policy_data.get('scraped', False),
                "text": policy_data.get('text', ''),
                "error": policy_data.get('error'),
                "found_urls": privacy_urls,
                "scraped_at": time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"❌ Error analyzing {company_website}: {e}")
            return {
                "company_website": company_website,
                "company_name": self._extract_company_name(company_website),
                "privacy_url": None,
                "scraped": False,
                "error": str(e),
                "text": f"Failed to analyze {company_website}"
            }
    
    def _find_privacy_policy_urls(self, website_url: str) -> List[str]:
        """Find all possible privacy policy URLs for a website"""
        privacy_urls = []
        
        # Check if we have a known URL for this domain
        domain = urlparse(website_url).netloc.replace('www.', '')
        if domain in self.KNOWN_PRIVACY_URLS:
            known_url = self.KNOWN_PRIVACY_URLS[domain]
            privacy_urls.append(known_url)
            print(f"✓ Using known privacy URL: {known_url}")
        
        try:
            # Get the main page
            response = self.session.get(website_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            base_url = f"{urlparse(website_url).scheme}://{urlparse(website_url).netloc}"
            
            # Method 1: Look for links containing privacy keywords
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').lower()
                text = link.get_text().lower()
                
                # Check if link text or href contains privacy keywords
                if any(keyword in href or keyword in text for keyword in self.PRIVACY_KEYWORDS):
                    full_url = urljoin(base_url, link['href'])
                    if full_url not in privacy_urls:
                        privacy_urls.append(full_url)
            
            # Method 2: Try common privacy policy URL patterns
            for pattern in self.PRIVACY_URL_PATTERNS:
                test_url = base_url + pattern
                try:
                    test_response = self.session.head(test_url, timeout=5, allow_redirects=True)
                    if test_response.status_code == 200:
                        if test_url not in privacy_urls:
                            privacy_urls.append(test_url)
                            print(f"✓ Found via pattern: {test_url}")
                except Exception as e:
                    continue
            
            # Method 2.5: Try with /legal/ prefix
            legal_patterns = ['/legal/privacy-policy', '/legal/privacy', '/help/privacy', '/support/privacy']
            for pattern in legal_patterns:
                test_url = base_url + pattern
                try:
                    test_response = self.session.head(test_url, timeout=5, allow_redirects=True)
                    if test_response.status_code == 200:
                        if test_url not in privacy_urls:
                            privacy_urls.append(test_url)
                            print(f"✓ Found via legal pattern: {test_url}")
                except:
                    continue
            
            # Method 3: Look in footer links
            footer = soup.find('footer') or soup.find(class_=re.compile('footer', re.I))
            if footer:
                for link in footer.find_all('a', href=True):
                    href = link.get('href', '').lower()
                    text = link.get_text().lower()
                    
                    if any(keyword in href or keyword in text for keyword in self.PRIVACY_KEYWORDS):
                        full_url = urljoin(base_url, link['href'])
                        if full_url not in privacy_urls:
                            privacy_urls.append(full_url)
            
            # Sort by relevance (exact matches first)
            def url_relevance(url):
                url_lower = url.lower()
                if 'privacy-policy' in url_lower:
                    return 0
                elif 'privacy' in url_lower:
                    return 1
                else:
                    return 2
            
            privacy_urls.sort(key=url_relevance)
            
            print(f"🔗 Found {len(privacy_urls)} potential privacy policy URLs")
            return privacy_urls[:5]  # Return top 5 candidates
            
        except Exception as e:
            print(f"❌ Error finding privacy URLs: {e}")
            return []
    
    def _scrape_privacy_content(self, privacy_url: str) -> Dict:
        """Scrape content from a privacy policy URL"""
        try:
            response = self.session.get(privacy_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Try to find main content area
            main_content = (
                soup.find('main') or 
                soup.find('article') or 
                soup.find(class_=re.compile('content|policy|privacy|main', re.I)) or
                soup.find('div', class_=re.compile('container|wrapper', re.I)) or
                soup.body
            )
            
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)
            
            # Clean up text
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Validate that this looks like a privacy policy
            privacy_indicators = ['privacy', 'personal data', 'information', 'collect', 'use', 'share']
            text_lower = text.lower()
            
            if len(text) < 500:
                return {
                    "scraped": False,
                    "error": "Content too short to be a privacy policy",
                    "text": text[:500]
                }
            
            if not any(indicator in text_lower for indicator in privacy_indicators):
                return {
                    "scraped": False,
                    "error": "Content doesn't appear to be a privacy policy",
                    "text": text[:500]
                }
            
            return {
                "scraped": True,
                "text": text[:10000],  # Limit to 10k characters
                "length": len(text),
                "url": privacy_url
            }
            
        except Exception as e:
            return {
                "scraped": False,
                "error": str(e),
                "text": f"Failed to scrape {privacy_url}"
            }
    
    def _extract_company_name(self, website_url: str) -> str:
        """Extract company name from website URL or content"""
        try:
            # Try to get company name from domain
            domain = urlparse(website_url).netloc
            domain = domain.replace('www.', '').replace('.com', '').replace('.no', '').replace('.org', '')
            
            # Capitalize first letter
            company_name = domain.split('.')[0].capitalize()
            
            # Try to get better name from website title
            try:
                response = self.session.get(website_url, timeout=5)
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find('title')
                if title:
                    title_text = title.get_text().strip()
                    # Extract company name from title (usually before | or - )
                    for separator in [' | ', ' - ', ' – ', ' — ']:
                        if separator in title_text:
                            company_name = title_text.split(separator)[0].strip()
                            break
                    else:
                        company_name = title_text.strip()
            except:
                pass
            
            return company_name
            
        except:
            return "Unknown Company"
    
    def process_with_llm(self, platform: str, raw_text: str):
        """
        Use this with Bedrock to extract structured data from raw policy text
        
        Prompt example:
        "Analyze this privacy policy and extract:
        1. List of data types collected
        2. How data is shared
        3. Data retention policy
        4. User rights
        5. Main concerns
        6. Positive aspects
        
        Return as JSON."
        """
        # This would call your Bedrock client
        # For now, just a placeholder
        pass

if __name__ == "__main__":
    scraper = PolicyScraper()
    
    print("🕵️ Privacy Policy Scraper")
    print("=" * 50)
    
    # Scrape all policies
    results = scraper.scrape_all()
    
    print("\n" + "=" * 50)
    print(f"✓ Scraped {len(results)} policies")
    print(f"✓ Saved to {scraper.output_dir}")
    print("\nNext steps:")
    print("1. Review the raw files")
    print("2. Use Bedrock to process them into structured format")
    print("3. Replace the mock JSON files with real data")
