#!/usr/bin/env python3
"""
Standalone scraper script for running Playwright in a separate process.
This avoids conflicts with Streamlit's event loop.
"""

import sys
import json
import time
from typing import List, Dict, Any
from urllib.parse import urljoin
import trafilatura
from bs4 import BeautifulSoup
import spacy

# Add the project root to the path
sys.path.insert(0, sys.path[0] + "/..")

from sem_plan.core.types import RawKeyword


def scrape_website(url: str, source_type: str) -> List[Dict[str, Any]]:
    """Scrape a single website using Playwright."""
    from playwright.sync_api import sync_playwright
    
    keywords = []
    
    # Known slow-loading sites that need special handling
    slow_sites = {
        "myfitnesspal.com",
        "blog.myfitnesspal.com", 
        "support.myfitnesspal.com"
    }
    
    is_slow_site = any(slow_site in url.lower() for slow_site in slow_sites)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_viewport_size({"width": 1920, "height": 1080})
            
            if is_slow_site:
                # For slow sites, use the most lenient settings
                page.goto(url, wait_until="load", timeout=90000)  # 90 seconds timeout
                time.sleep(5)  # Extra wait for dynamic content
                
                # Extract content from main page only
                content = page.content()
                keywords.extend(extract_keywords_from_content(content, url, f"{source_type}_main"))
                
            else:
                # For normal sites, scrape main page and important subpages
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(2)
                
                # Extract from main page
                content = page.content()
                keywords.extend(extract_keywords_from_content(content, url, f"{source_type}_main"))
                
                # Find and scrape important subpages
                important_pages = find_important_pages(page, url)
                for sub_url in important_pages[:3]:  # Limit to 3 subpages
                    try:
                        page.goto(sub_url, wait_until="domcontentloaded", timeout=20000)
                        time.sleep(1)
                        sub_content = page.content()
                        keywords.extend(extract_keywords_from_content(sub_content, sub_url, f"{source_type}_sub"))
                    except Exception as e:
                        print(f"Failed to scrape subpage {sub_url}: {e}", file=sys.stderr)
                        continue
            
            browser.close()
            
    except Exception as e:
        print(f"Playwright failed for {url}: {e}", file=sys.stderr)
        # Fallback to HTTP scraping
        keywords.extend(fallback_http_scrape(url, source_type))
    
    return keywords


def fallback_http_scrape(url: str, source_type: str) -> List[Dict[str, Any]]:
    """Fallback scraping using requests and BeautifulSoup."""
    import requests
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Extract text content
        extracted_text = trafilatura.extract(response.text)
        if not extracted_text:
            # Fallback to BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            extracted_text = soup.get_text()
        
        return extract_keywords_from_text(extracted_text, url, source_type)
        
    except Exception as e:
        print(f"HTTP fallback failed for {url}: {e}", file=sys.stderr)
        return []


def find_important_pages(page, base_url: str) -> List[str]:
    """Find important subpages to scrape."""
    important_pages = []
    
    try:
        # Look for navigation links
        links = page.query_selector_all('a[href]')
        
        for link in links:
            href = link.get_attribute('href')
            if href:
                full_url = urljoin(base_url, href)
                
                # Only include same-domain URLs
                if full_url.startswith(base_url):
                    page_type = classify_page_type(full_url)
                    if page_type in ['product', 'service', 'feature', 'about']:
                        important_pages.append(full_url)
        
        # Remove duplicates and limit
        important_pages = list(set(important_pages))[:5]
        
    except Exception as e:
        print(f"Error finding important pages: {e}", file=sys.stderr)
    
    return important_pages


def classify_page_type(url: str) -> str:
    """Classify the type of page based on URL."""
    url_lower = url.lower()
    
    if any(word in url_lower for word in ['product', 'feature', 'tool', 'app']):
        return 'product'
    elif any(word in url_lower for word in ['service', 'plan', 'pricing']):
        return 'service'
    elif any(word in url_lower for word in ['about', 'company', 'team']):
        return 'about'
    elif any(word in url_lower for word in ['blog', 'article', 'news']):
        return 'blog'
    else:
        return 'other'


def extract_keywords_from_content(html_content: str, url: str, source: str) -> List[Dict[str, Any]]:
    """Extract keywords from HTML content."""
    try:
        # Use trafilatura for better text extraction
        extracted_text = trafilatura.extract(html_content)
        if not extracted_text:
            # Fallback to BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            extracted_text = soup.get_text()
        
        return extract_keywords_from_text(extracted_text, url, source)
        
    except Exception as e:
        print(f"Error extracting keywords from {url}: {e}", file=sys.stderr)
        return []


def extract_keywords_from_text(text: str, url: str, source: str) -> List[Dict[str, Any]]:
    """Extract keywords from plain text."""
    try:
        # Load spaCy model
        nlp = spacy.load("en_core_web_sm")
        
        # Process text
        doc = nlp(text)
        
        keywords = []
        
        # Map source to expected Literal type
        source_mapping = {
            "brand_main": "brand_tool",
            "brand_sub": "brand_tool", 
            "competitor_main": "competitor_tool",
            "competitor_sub": "competitor_tool"
        }
        mapped_source = source_mapping.get(source, "brand_tool")
        
        # Extract noun phrases and important terms
        for chunk in doc.noun_chunks:
            if len(chunk.text.strip()) > 2 and len(chunk.text.strip()) < 50:
                keyword = chunk.text.strip().lower()
                if keyword and not keyword.isdigit():
                    keywords.append({
                        "keyword": keyword,
                        "origin_url": url,
                        "source": mapped_source,
                        "gkp_avg_monthly_searches": 0  # Will be filled later
                    })
        
        # Extract individual nouns and adjectives
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and len(token.text.strip()) > 2:
                keyword = token.text.strip().lower()
                if keyword and not keyword.isdigit() and keyword not in [kw["keyword"] for kw in keywords]:
                    keywords.append({
                        "keyword": keyword,
                        "origin_url": url,
                        "source": mapped_source,
                        "gkp_avg_monthly_searches": 0
                    })
        
        return keywords[:100]  # Limit to 100 keywords per source
        
    except Exception as e:
        print(f"Error processing text from {url}: {e}", file=sys.stderr)
        return []


def main():
    """Main entry point for the scraper script."""
    if len(sys.argv) != 3:
        print("Usage: python scraper_script.py <url> <source_type>", file=sys.stderr)
        sys.exit(1)
    
    url = sys.argv[1]
    source_type = sys.argv[2]
    
    try:
        keywords = scrape_website(url, source_type)
        print(json.dumps(keywords))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print(json.dumps([]))


if __name__ == "__main__":
    main()
