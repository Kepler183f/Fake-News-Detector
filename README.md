
# 🔍 Fake News Detector

AI-powered web application that analyzes news articles for credibility and political bias using Machine Learning and Natural Language Processing.



## Features

- **AI-Powered Source Analysis** - Evaluates domain reputation using trained models
- **Political Bias Detection** - Machine learning classification of left/right leaning language 
- **Sentiment Analysis** - NLTK VADER pre-trained model for emotional tone detection
- **Pattern Recognition** - Automated clickbait and suspicious keyword detection
- **Visual AI Scoring** - Color-coded credibility ratings (Green/Yellow/Red)
- **Dual Input** - Analyze by URL or paste text directly

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install flask requests beautifulsoup4 nltk
   ```

2. **Create project structure:**
   ```
   fake-news-detector/
   ├── app.py
   └── templates/
       └── index.html
   ```

3. **Run application:**
   ```bash
   python app.py
   ```

4. **Open:** `http://localhost:5000`

## How It Works

- **Source Check (60%)** - Compares against reliable/unreliable domain lists
- **AI Content Analysis (40%)** - Uses NLTK's pre-trained VADER model for sentiment analysis
- **Political Bias Detection** - Machine learning-based keyword classification
- **Pattern Recognition** - Automated detection of clickbait and suspicious language patterns
- **Final Score** - AI-weighted algorithm combines all factors into credibility percentage

## Scoring

- **70-100%** 🟢 High credibility
- **40-69%** 🟡 Medium credibility  
- **0-39%** 🔴 Low credibility

## Tech Stack

- **Backend:** Python Flask
- **AI/NLP:** NLTK VADER sentiment analysis (pre-trained model)
- **Frontend:** HTML/CSS/JavaScript
- **Web Scraping:** BeautifulSoup4
- **Machine Learning:** Pattern recognition and classification algorithms

## Testing

Try with different news sources:
- **Reliable:** BBC, Reuters, AP News
- **Mixed:** Opinion pieces, blog posts
- **Suspicious:** Known misinformation sites
=======
# Fake-News-Detector
