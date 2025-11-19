"""
Daily AI News Digest Agent

This script automatically:
1. Fetches AI/ML news articles from multiple RSS feeds
2. Filters articles published from yesterday until now
3. Removes duplicates across feeds
4. Summarizes and formats articles using Google's Gemini AI
5. Sends a formatted Hebrew-language digest via email

The script monitors various AI research sources including OpenAI, DeepMind, arXiv,
Hugging Face, and other leading AI/ML publications.
"""

import requests
from io import BytesIO
import feedparser
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

# --- RSS Feed Sources ---
# List of RSS feed URLs to scrape for AI/ML news articles
# Each feed is monitored for articles published within the last 24 hours
# Feeds are organized by category to focus on developer-relevant content
RSS_FEEDS = [
    # --- Filtered Tech News (AI Only) ---
    # These feeds are pre-filtered to only include AI-related content
    "https://techcrunch.com/category/artificial-intelligence/feed/",  # TechCrunch - AI category only (filters out general tech news)
    "https://www.theverge.com/rss/artificial-intelligence/index.xml",  # The Verge - AI category only (filters out general tech news)

    # --- Major AI Companies (Major Announcements Only) ---
    # Official blogs from leading AI companies - focuses on product releases, model launches, and significant updates
    "https://openai.com/blog/rss.xml",  # OpenAI - Official announcements, model releases, API updates
    "https://www.anthropic.com/atom.xml",  # Anthropic (Claude) - Claude model updates, safety research, product launches
    "https://blog.google/technology/ai/rss/",  # Google DeepMind - Research breakthroughs, model releases, AI safety
    "https://ai.meta.com/rss",  # Meta AI (Facebook) - Llama models, research publications, open-source releases
    "https://aws.amazon.com/blogs/machine-learning/feed/",  # AWS Machine Learning Blog - Important for developers: ML services, SageMaker updates, infrastructure tools

    # --- Developer Libraries and Tools (Code and Models) ---
    # Critical resources for software engineers working with AI/ML
    "https://huggingface.co/blog/feed.xml",  # Hugging Face Blog - New model releases, transformers library updates, datasets, and code examples
    "https://blog.langchain.dev/rss/",  # LangChain Blog - Critical library for developers: framework updates, integrations, best practices
    
    # --- Significant Research Only ---
    # Focuses on research that gains traction rather than all theoretical papers
    "http://export.arxiv.org/rss/cs.CL", 
]

def fetch_news():
    """
    Fetch news articles from RSS feeds published within the last 24 hours.
    Returns aggregated text of all unique articles, sorted by publication date (newest first).
    Includes User-Agent headers to bypass anti-bot protections on sites like Google/Meta.
    """
    print("Fetching news from RSS feeds...")
    
    # Calculate time range: from 24 hours ago until now (exactly 24-hour window)
    now = datetime.now(timezone.utc)
    yesterday_start = now - timedelta(days=1)
    
    # Track unique articles by URL to prevent duplicates across different feeds
    seen_urls = set()
    all_entries = []

    # Headers to mimic a real browser (Crucial for DeepMind, Meta, etc.)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, application/atom+xml, text/xml;q=0.9, */*;q=0.8"
    }
    
    for url in RSS_FEEDS:
        try:
            # Step 1: Send HTTP request with browser-like headers to bypass anti-bot protections
            # The User-Agent header is crucial for sites like Google/Meta that block default Python user agents
            response = requests.get(url, headers=headers, timeout=10)
            
            # Step 2: Check HTTP status code (critical fix)
            # Raises an HTTPError exception if status is 403, 404, or any non-200 status
            # This helps identify blocked feeds early rather than parsing invalid responses
            response.raise_for_status() 
            
            # Step 3: Parse the RSS/Atom feed content (only if status is 200 OK)
            # Convert response content to BytesIO for feedparser compatibility
            content = BytesIO(response.content)
            feed = feedparser.parse(content)
            
            # Extract source name from feed metadata
            source_name = feed.feed.get('title', 'Unknown Source')
            print(f"Scraping {source_name}...")
            
            feed_count = 0
            for entry in feed.entries:
                # Extract publication date from RSS entry
                # Try multiple methods as different feeds may format dates differently
                published_time = None
                
                # Method 1: Use parsed date tuple (most reliable, already structured by feedparser)
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        pass
                
                # Method 2: Parse published date string (fallback for feeds without parsed dates)
                if published_time is None and hasattr(entry, 'published') and entry.published:
                    try:
                        published_time = parsedate_to_datetime(entry.published)
                        # Ensure timezone is set (default to UTC if missing)
                        if published_time.tzinfo is None:
                            published_time = published_time.replace(tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        pass
                
                # Skip entries without a valid publication date
                if published_time is None:
                    continue
                
                # Filter: Only include articles published within the last 24 hours
                if published_time >= yesterday_start and published_time <= now:
                    link = entry.link
                    
                    # Deduplication: Skip articles we've already seen (by URL)
                    if link in seen_urls:
                        continue
                    
                    seen_urls.add(link)
                    title = entry.title
                    # Get summary/description (some feeds use 'summary', others use 'description')
                    summary = entry.get('summary', entry.get('description', ''))
                    
                    all_entries.append({
                        'source': source_name,
                        'title': title,
                        'link': link,
                        'summary': summary,
                        'published': published_time
                    })
                    feed_count += 1
            
            print(f"Found {feed_count} unique articles from the last 24 hours in {source_name}")
        
        except requests.exceptions.HTTPError as err:
            # Handle HTTP errors (403 Forbidden, 404 Not Found, etc.)
            # Print clear message about blocking so we know which sources are blocking us
            print(f"Error fetching {url}: HTTP Error {err.response.status_code}. Likely blocked by the source.")

        except Exception as e:
            # Handle all other errors (parser errors, network connection issues, etc.)
            print(f"Error fetching {url}: {e}")
    
    # Sort all entries by publication date (newest articles first)
    all_entries.sort(key=lambda x: x['published'], reverse=True)
    
    # Build aggregated text string from all unique entries
    # Format: Source, Published Time, Title, Link, and Summary for each article
    aggregated_text = ""
    for entry in all_entries:
        aggregated_text += f"Source: {entry['source']}\nPublished Time: {entry['published'].strftime('%Y-%m-%d %H:%M:%S UTC')}\nTitle: {entry['title']}\nLink: {entry['link']}\nSummary: {entry['summary']}\n\n---\n\n"
    
    return aggregated_text

def summarize_news(news_text):
    """
    Summarize and format news articles using Gemini AI.
    Creates a Hebrew-language daily digest email from raw news text.
    
    Args:
        news_text: Aggregated text containing all news articles to summarize
        
    Returns:
        Formatted summary text in Hebrew, ready for email
    """
    print("Sending to LLM for summarization...")
    genai.configure(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    You are an expert AI Engineering Curator.
    I will provide you with a raw list of news articles (already deduplicated by URL).
    
    Your task is to create the body of a daily digest email in HEBREW (עברית) specifically tailored for **Software Engineers and AI Developers**.
    
    Instructions:
    1. **Target Audience:** Content must be relevant to developers. Focus on open-source libraries, new models (LLMs), APIs, developer tools, and performance improvements.
    2. **Strict "BIG NEWS" Filtering:**
       - **EXCLUDE:** General tech news, crypto, business/stock news, and purely theoretical research papers (unless it's a major breakthrough), Minor bug fixes, small version increments (v1.1 to v1.2), funding news, pure speculation/opinion pieces..
       - **INCLUDE:** GitHub repos, Hugging Face releases, new SOTA models that can be used/tested, Critical security vulnerabilities, major flaws in popular tools, or "breaking changes" and major updates to frameworks (PyTorch, TensorFlow, LangChain).
    3. **Structure:** Unified list of updates.
    4. **Format per item:**
       - **Headline:** The name of the innovation.
       - **Date:** The date of publication (YYYY-MM-DD). Include the time of publication in Israel time (HH:MM:SS).
       - **Description:** 2-3 sentences explaining what is new and why it matters.
       - **Details:** License (Open Source/Commercial), Price (Is it free?), Where to try (Link).
       - **Source Link:** Original link.
    5. **IMPORTANT:** - Do NOT include an opening sentence (like "Here is the summary"), Do NOT include a closing sentence, Start directly with the first news item. Include ALL relevant entries from the provided list. Do not summarize or combine entries unless they are truly about the exact same story.
    6. **Tone:** Friendly, Professional, concise, engaging, easy to read.
    
    Here is the raw data (all unique entries):
    {news_text}
    """
    
    # Try different Gemini models in order of preference
    # Falls back to next model if current one fails (e.g., rate limits, unavailable)
    model_names = ['gemini-pro', 'gemini-1.5-pro', 'gemini-2.0-flash', 'gemini-2.5-flash']
    
    for model_name in model_names:
        try:
            print(f"Trying model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            print(f"Successfully used model: {model_name}")
            return response.text
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            continue
    
    raise Exception("No available Gemini model found. Please check your API key and available models.")

def send_email(content):
    """
    Send the summarized news digest via email.
    Converts Markdown content to HTML and sends as an HTML email with RTL (right-to-left) support for Hebrew.
    
    Args:
        content: The formatted summary text (in Hebrew) to send
    """
    print("Sending email...")
    
    # Create multipart email message container
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"Daily AI Dev Update 🤖 - {datetime.now().strftime('%d/%m/%Y')}"

    # Fixed header section with greeting message in Hebrew
    # This header appears at the top of every email with a styled greeting
    fixed_header = """
    <div style="background-color: #f0f4f8; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        <h2 style="margin: 0; color: #2c3e50;">בוקר טוב! להלן העדכונים החמים מ24 השעות האחרונות ☕</h2>
    </div>
    """

    # Convert Markdown formatting from LLM output to basic HTML
    # Note: This is a simple conversion (bold markers and line breaks)
    # For advanced Markdown support, consider using a proper Markdown library
    formatted_content = content.replace('**', '<b>').replace('**', '</b>').replace('\n', '<br>')

    # Assemble the complete HTML email body
    # Includes: RTL direction for Hebrew, styled header, formatted content, and footer
    html_body = f"""
    <div dir="rtl" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto;">
        {fixed_header}
        
        <div style="padding: 0 10px;">
            {formatted_content}
        </div>

        <hr style="border: 0; border-top: 1px solid #eee; margin-top: 30px;">
        <p style="font-size: 12px; color: #999; text-align: center;">
            נשלח אוטומטית על ידי סוכן ה-AI האישי שלך
        </p>
    </div>
    """
    
    # Attach the HTML content to the email message
    msg.attach(MIMEText(html_body, 'html'))

    try:
        # Connect to Gmail SMTP server on port 587 (TLS port)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Enable TLS encryption for secure connection
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)  # Authenticate with Gmail credentials
        text = msg.as_string()  # Convert message object to string format
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, text)  # Send the email
        server.quit()  # Close the SMTP connection
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    """
    Main execution flow:
    1. Fetch news articles from RSS feeds (from yesterday until now)
    2. Summarize articles using Gemini AI
    3. Send summarized digest via email
    """
    raw_news = fetch_news()
    if not raw_news:
        print("No news found.")
    else:
        summary = summarize_news(raw_news)
        send_email(summary)