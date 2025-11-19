# Daily AI News Digest Agent — README

## Overview

This Python script automates the process of collecting, filtering, summarizing, and emailing a daily AI/ML news digest. It gathers articles from multiple AI-related RSS feeds, filters only items published within the last 24 hours, removes duplicates, summarizes them using Google Gemini, and sends a formatted Hebrew-language digest to your email inbox.

##  Features
- Fetches AI/ML news from curated RSS feeds (OpenAI, DeepMind, Hugging Face, arXiv, TechCrunch AI, The Verge AI, etc.).
- Extracts only articles published in the last 24 hours.
- Removes duplicate news items across feeds based on URL.
- Sends aggregated article data to Google Gemini for summarization.
- Produces a Hebrew, developer-focused digest: SOTA models, tools, new releases, frameworks, major updates.
- Sends an HTML email with RTL support, custom styling, and daily timestamp.
- Fully automated (intended to run daily via cron or scheduler).

## Requirements
- Python 3.9+ (3.10 or 3.11 recommended)
- Internet access for fetching RSS feeds and Gemini API calls
- A valid Gemini API Key
- An email account with SMTP access (Gmail example provided)

## Installation
1. Clone the repository
git clone https://github.com/your-repo/daily-ai-digest.git
cd daily-ai-digest
2. Install required Python packages
Required packages include:
- requests
- feedparser
- google-generativeai
- smtplib (standard library)
- email (standard library)

## Environment Variables

Set these environment variables before running the script:
- GEMINI_API_KEY	Your Google Gemini API key
- EMAIL_SENDER	Email address used to send messages
- EMAIL_PASSWORD	App password or SMTP password
- EMAIL_RECEIVER	Target email address to receive digest

## How It Works
1. Fetch News (fetch_news)
- Downloads RSS feeds using browser-like headers (prevents blocking from Meta/Google).
- Parses publication time from each entry.
- Keeps only items from the last 24 hours.
- Removes duplicates based on link.
- Outputs a large aggregated text block used for summarization.
2. Summarize with Gemini (summarize_news)
- Sends the aggregated raw text to Gemini (multiple fallback models).
- Generates a Hebrew developer-focused digest.
- Ensures: No intros, no outros. Each news item includes headline, date, summary, details, link. Items are not merged unless identical.
3. Email the Digest (send_email)
- Converts the LLM output to simple HTML.
- Adds a styled header with RTL alignment.
- Sends using Gmail SMTP (smtp.gmail.com:587).

## Running the Script
python main.py

If no news was found in the last 24 hours, it prints:
No news found.

## Scheduling (Optional)
Linux (cron)
0 8 * * * /usr/bin/python3 /path/to/main.py >> /path/to/log.txt 2>&1
Windows (Task Scheduler)

Create a daily task that runs:
python C:\path\to\main.py

## Troubleshooting
- 403 errors on RSS feeds — Some sources block bots; custom User-Agent solves this.
- Email not sending — Gmail often requires an app password if 2FA is enabled.
- Gemini model errors — The script automatically retries multiple model versions.

## Notes
- The output digest is automatically formatted in Hebrew even though the script/README are English.
- You can modify the prompt to change tone, target audience, or structure.
- To support Markdown → HTML conversion beyond simple replacements, consider adding a Markdown parser.

Enjoy :)
