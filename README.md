# Daily AI News Digest Agent — README

## Overview

This Python script automates the process of collecting, filtering, summarizing, and emailing a daily AI/ML news digest.
It gathers articles from multiple AI-related RSS feeds, filters items published within the last 24 hours, removes duplicates, summarizes them using Google Gemini, and sends a formatted Hebrew-language digest directly to your inbox.

##  Features
- Fetches AI/ML news from curated RSS feeds (OpenAI, DeepMind, Hugging Face, arXiv, TechCrunch AI, The Verge AI, etc.).
- Extracts only articles published in the last 24 hours.
- Removes duplicate news items across feeds using URL-based deduplication.
- Uses Google Gemini to generate a clean, structured Hebrew summary.
- Developer-focused digest: SOTA models, tools, new releases, frameworks, major updates.
- Sends an HTML email with RTL support, custom styling, and timestamp.
- Fully automated — can be run locally, via cron, or through GitHub Actions.

## Requirements
- Python 3.9+ (3.10 or 3.11 recommended)
- Internet access for RSS fetching + Gemini API calls
- Valid Gemini API Key
- Email account with SMTP access (Gmail recommended)

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

## Automation (Optional) — GitHub Actions
You can fully automate the daily digest using GitHub Actions.
1. Configure Secrets
Inside your GitHub repository:
- Go to: Settings → Secrets and variables → Actions
- Click New repository secret
- Add the following secrets:

GEMINI_API_KEY	Your Gemini API key
EMAIL_SENDER	Email used to send messages
EMAIL_PASSWORD	App password (recommended)
EMAIL_RECEIVER	Recipient email

2. Create the Workflow
- Go to the Actions tab
- Click set up a workflow yourself
- Name the file: daily_run.yml
- Paste the following:

```
name: Daily AI News Aggregator

on:
  schedule:
    # Runs every day at 06:00 UTC (08:00–09:00 Israel time depending on DST)
    - cron: '0 6 * * *'
  workflow_dispatch: # Allows manual runs for testing

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run script
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        EMAIL_SENDER: ${{ secrets.EMAIL_SENDER }}
        EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
        EMAIL_RECEIVER: ${{ secrets.EMAIL_RECEIVER }}
      run: python daily_ai_agent.py
```

- Click Commit changes

Your digest will now be generated and emailed automatically every day.

## Troubleshooting
- 403 errors on RSS feeds — Some sources block bots; custom User-Agent solves this.
- Email not sending — Gmail often requires an app password if 2FA is enabled.
- Gemini model errors — The script automatically retries multiple model versions.

Enjoy :)
