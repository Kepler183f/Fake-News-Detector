from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import os

# Download required NLTK data (run once)
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

app = Flask(__name__)

class FakeNewsDetector:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        
        # Known unreliable sources (simplified list)
        self.unreliable_domains = {
            'naturalnews.com', 'infowars.com', 'beforeitsnews.com',
            'worldnewsdailyreport.com', 'nationalreport.net',
            'empirenews.net', 'huzlers.com', 'clickhole.com'
        }
        
        # Reliable sources get bonus points
        self.reliable_domains = {
            'reuters.com', 'ap.org', 'bbc.com', 'npr.org',
            'nytimes.com', 'washingtonpost.com', 'cnn.com',
            'abcnews.go.com', 'cbsnews.com', 'nbcnews.com'
        }
        
        # Political bias detection keywords
        self.left_bias_keywords = [
            'progressive', 'social justice', 'inequality', 'systemic racism',
            'climate change', 'wealth gap', 'corporate greed', 'workers rights',
            'medicare for all', 'gun control', 'reproductive rights', 'diversity',
            'inclusion', 'marginalized', 'oppression', 'privilege', 'fascist',
            'far-right', 'extremist', 'nazi', 'white supremacist', 'resistance',
            'grassroots', 'community organizing', 'environmental justice'
        ]
        
        self.right_bias_keywords = [
            'traditional values', 'family values', 'constitutional rights', 'freedom',
            'liberty', 'patriot', 'america first', 'law and order', 'border security',
            'second amendment', 'pro-life', 'conservative', 'fiscal responsibility',
            'limited government', 'free market', 'socialism', 'communist', 'liberal elite',
            'mainstream media', 'deep state', 'establishment', 'radical left',
            'antifa', 'woke', 'cancel culture', 'religious freedom', 'military strong'
        ]
        
        # Neutral/centrist language indicators
        self.neutral_keywords = [
            'according to data', 'studies show', 'research indicates', 'experts say',
            'both sides', 'bipartisan', 'compromise', 'moderate', 'balanced approach',
            'evidence suggests', 'analysis reveals', 'factual', 'objective'
        ]
        
        # Emotional/polarizing language
        self.polarizing_keywords = [
            'outrageous', 'disgusting', 'terrible', 'disaster', 'crisis', 'emergency',
            'devastating', 'shocking', 'alarming', 'dangerous', 'threat', 'attack',
            'destroy', 'eliminate', 'radical', 'extreme', 'unprecedented', 'chaos'
        ]
        
        # Suspicious keywords that often appear in fake news
        self.suspicious_keywords = [
            'shocking', 'unbelievable', 'secret', 'they don\'t want you to know',
            'doctors hate', 'miracle cure', 'this will blow your mind',
            'absolutely incredible', 'must see', 'viral', 'breaking',
            'exclusive', 'leaked', 'exposed', 'bombshell'
        ]
        
        # Clickbait patterns
        self.clickbait_patterns = [
            r'\d+\s+(?:things|ways|reasons|facts)',
            r'you won\'t believe',
            r'what happens next',
            r'this \w+ will \w+ you',
            r'number \d+ will shock you'
        ]

    def extract_text_from_url(self, url):
        """Extract article text from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text from common article containers
            article_text = ""
            for tag in soup.find_all(['p', 'article', 'div']):
                if tag.get_text().strip():
                    article_text += tag.get_text() + " "
            
            # Get title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            # Clean up the article text
            article_text = article_text.strip()
            
            if not article_text:
                return title_text, "No article content could be extracted from this URL."
            
            return title_text, article_text[:5000]  # Limit text length
            
        except requests.exceptions.Timeout:
            return "", "Request timed out. The website may be slow or unresponsive."
        except requests.exceptions.ConnectionError:
            return "", "Could not connect to the website. Please check the URL and try again."
        except requests.exceptions.HTTPError as e:
            return "", f"HTTP error {e.response.status_code}: The website returned an error."
        except requests.exceptions.RequestException as e:
            return "", f"Request failed: {str(e)}"
        except Exception as e:
            return "", f"Error extracting text: {str(e)}"

    def analyze_source_credibility(self, url):
        """Analyze source credibility based on domain"""
        try:
            domain = urlparse(url).netloc.lower().replace('www.', '')
            
            if domain in self.unreliable_domains:
                return 0.1, f"Domain '{domain}' is flagged as unreliable"
            elif domain in self.reliable_domains:
                return 0.9, f"Domain '{domain}' is from a reputable source"
            else:
                return 0.5, f"Domain '{domain}' has neutral credibility"
                
        except:
            return 0.3, "Unable to analyze source domain"

    def analyze_political_bias(self, title, text):
        """Analyze political bias in content"""
        full_text = (title + " " + text).lower()
        
        # Count bias indicators
        left_score = 0
        right_score = 0
        neutral_score = 0
        polarizing_score = 0
        
        found_left_terms = []
        found_right_terms = []
        found_neutral_terms = []
        found_polarizing_terms = []
        
        # Check for left-leaning keywords
        for keyword in self.left_bias_keywords:
            count = full_text.count(keyword.lower())
            if count > 0:
                left_score += count
                found_left_terms.append(keyword)
        
        # Check for right-leaning keywords
        for keyword in self.right_bias_keywords:
            count = full_text.count(keyword.lower())
            if count > 0:
                right_score += count
                found_right_terms.append(keyword)
        
        # Check for neutral language
        for keyword in self.neutral_keywords:
            count = full_text.count(keyword.lower())
            if count > 0:
                neutral_score += count
                found_neutral_terms.append(keyword)
        
        # Check for polarizing language
        for keyword in self.polarizing_keywords:
            count = full_text.count(keyword.lower())
            if count > 0:
                polarizing_score += count
                found_polarizing_terms.append(keyword)
        
        # Calculate bias metrics
        total_bias_indicators = left_score + right_score
        
        if total_bias_indicators == 0:
            bias_direction = "Neutral"
            bias_strength = "Low"
            bias_score = 0.5  # Neutral
        else:
            # Determine bias direction
            if left_score > right_score:
                bias_direction = "Left-leaning"
                bias_ratio = left_score / total_bias_indicators
            elif right_score > left_score:
                bias_direction = "Right-leaning"
                bias_ratio = right_score / total_bias_indicators
            else:
                bias_direction = "Mixed/Balanced"
                bias_ratio = 0.5
            
            # Determine bias strength
            if bias_ratio >= 0.8:
                bias_strength = "Strong"
            elif bias_ratio >= 0.6:
                bias_strength = "Moderate"
            else:
                bias_strength = "Slight"
            
            # Calculate overall bias score (0 = strong left, 0.5 = neutral, 1 = strong right)
            if bias_direction == "Left-leaning":
                bias_score = 0.5 - (bias_ratio * 0.5)
            elif bias_direction == "Right-leaning":
                bias_score = 0.5 + (bias_ratio * 0.5)
            else:
                bias_score = 0.5
        
        # Calculate objectivity score (higher = more objective)
        total_words = len(full_text.split())
        if total_words > 0:
            objectivity_score = min(1.0, neutral_score / max(total_words * 0.01, 1))
            polarization_penalty = min(0.5, polarizing_score / max(total_words * 0.005, 1))
            objectivity_score = max(0, objectivity_score - polarization_penalty)
        else:
            objectivity_score = 0.5
        
        return {
            'bias_direction': bias_direction,
            'bias_strength': bias_strength,
            'bias_score': bias_score,
            'objectivity_score': objectivity_score,
            'left_indicators': {
                'count': left_score,
                'terms': found_left_terms[:5]  # Limit to first 5 found
            },
            'right_indicators': {
                'count': right_score,
                'terms': found_right_terms[:5]
            },
            'neutral_indicators': {
                'count': neutral_score,
                'terms': found_neutral_terms[:5]
            },
            'polarizing_indicators': {
                'count': polarizing_score,
                'terms': found_polarizing_terms[:5]
            }
        }

    def analyze_content(self, title, text):
        """Analyze content for suspicious patterns"""
        full_text = (title + " " + text).lower()
        
        # Check for suspicious keywords
        suspicious_score = 0
        found_keywords = []
        for keyword in self.suspicious_keywords:
            if keyword.lower() in full_text:
                suspicious_score += 1
                found_keywords.append(keyword)
        
        # Check for clickbait patterns
        clickbait_score = 0
        for pattern in self.clickbait_patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                clickbait_score += 1
        
        # Sentiment analysis
        sentiment = self.sia.polarity_scores(title + " " + text[:1000])
        
        # Political bias analysis
        bias_analysis = self.analyze_political_bias(title, text)
        
        # Calculate content credibility
        max_suspicious = len(self.suspicious_keywords)
        max_clickbait = len(self.clickbait_patterns)
        
        suspicious_penalty = min(suspicious_score / max_suspicious, 0.4)
        clickbait_penalty = min(clickbait_score / max_clickbait, 0.3)
        
        # Extreme sentiment can indicate bias
        sentiment_penalty = abs(sentiment['compound']) * 0.2
        
        content_score = max(0.1, 1.0 - suspicious_penalty - clickbait_penalty - sentiment_penalty)
        
        analysis = {
            'suspicious_keywords': found_keywords,
            'clickbait_patterns': clickbait_score,
            'sentiment': sentiment,
            'content_score': content_score,
            'bias_analysis': bias_analysis
        }
        
        return content_score, analysis

    def calculate_credibility_score(self, url, title, text):
        """Calculate overall credibility score"""
        source_score, source_analysis = self.analyze_source_credibility(url)
        content_score, content_analysis = self.analyze_content(title, text)
        
        # Weighted average (source credibility is very important)
        overall_score = (source_score * 0.6) + (content_score * 0.4)
        
        # Determine credibility level
        if overall_score >= 0.7:
            credibility_level = "HIGH"
            color = "green"
        elif overall_score >= 0.4:
            credibility_level = "MEDIUM"
            color = "yellow"
        else:
            credibility_level = "LOW"
            color = "red"
        
        return {
            'overall_score': overall_score,
            'credibility_level': credibility_level,
            'color': color,
            'source_analysis': source_analysis,
            'content_analysis': content_analysis,
            'source_score': source_score,
            'content_score': content_score
        }

# Initialize detector
detector = FakeNewsDetector()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url', '').strip()
    text_input = data.get('text', '').strip()
    
    if url:
        # Analyze URL
        title, article_text = detector.extract_text_from_url(url)
        if "Error extracting text" in article_text:
            return jsonify({'error': article_text})
        
        result = detector.calculate_credibility_score(url, title, article_text)
        result['title'] = title
        result['source_url'] = url
        
    elif text_input:
        # Analyze pasted text
        # For pasted text, we don't have a source URL, so we focus on content
        fake_url = "user_input.com"  # Placeholder for analysis
        result = detector.calculate_credibility_score(fake_url, "", text_input)
        result['title'] = "User Provided Text"
        result['source_url'] = None
        # Adjust score since we can't verify source
        result['overall_score'] = result['content_score']
        
    else:
        return jsonify({'error': 'Please provide either a URL or text to analyze'})
    
    # Format score as percentage
    result['score_percentage'] = int(result['overall_score'] * 100)
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
