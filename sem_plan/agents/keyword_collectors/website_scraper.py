from __future__ import annotations

import subprocess
import json
import os
import sys
from typing import List
from urllib.parse import urljoin

import trafilatura
from bs4 import BeautifulSoup
import spacy

from ...core.types import RawKeyword, Config
from ...utils.http import get, polite_delay


class WebsiteScraper:
    """Scrapes brand and competitor websites using subprocess calls to avoid Streamlit conflicts."""
    
    def __init__(self, config: Config):
        self.config = config
        self.nlp = spacy.load("en_core_web_sm")
        
        # Get the path to the scraper script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        self.scraper_script_path = os.path.join(project_root, "scraper_script.py")
        
        # Known slow-loading sites that need special handling
        self.slow_sites = {
            "myfitnesspal.com",
            "blog.myfitnesspal.com", 
            "support.myfitnesspal.com"
        }
        
    def __enter__(self):
        # No need to initialize Playwright here anymore
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # No cleanup needed for subprocess approach
        pass
    
    def scrape_all_websites(self) -> List[RawKeyword]:
        """Scrape brand and competitor websites using subprocess calls."""
        keywords = []
        
        # Scrape brand website
        keywords.extend(self._scrape_single_website(self.config.brand_url, "brand"))
        
        # Scrape competitor websites
        for comp_url in self.config.competitor_urls:
            keywords.extend(self._scrape_single_website(comp_url, "competitor"))
            
        return keywords
    
    def _scrape_single_website(self, url: str, source_type: str) -> List[RawKeyword]:
        """Scrape a single website using subprocess call to scraper script."""
        try:
            # Call the standalone scraper script
            result = subprocess.run(
                [sys.executable, self.scraper_script_path, url, source_type],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                cwd=os.path.dirname(self.scraper_script_path)
            )
            
            if result.returncode == 0:
                # Parse the JSON output
                keywords_data = json.loads(result.stdout)
                return [RawKeyword(**kw_data) for kw_data in keywords_data]
            else:
                print(f"Scraper script failed for {url}: {result.stderr}")
                return self._fallback_scrape(url, source_type)
                
        except subprocess.TimeoutExpired:
            print(f"Scraper script timed out for {url}")
            return self._fallback_scrape(url, source_type)
        except Exception as e:
            print(f"Error calling scraper script for {url}: {e}")
            return self._fallback_scrape(url, source_type)
    
    def _fallback_scrape(self, url: str, source_type: str) -> List[RawKeyword]:
        """Fallback scraping using HTTP requests when subprocess fails."""
        try:
            # Use the existing HTTP utility
            response = get(url)
            if not response:
                return []
            
            # Extract text content - response is already the text content
            extracted_text = trafilatura.extract(response)
            if not extracted_text:
                # Fallback to BeautifulSoup
                soup = BeautifulSoup(response, 'html.parser')
                extracted_text = soup.get_text()
            
            return self._extract_keywords_from_text(extracted_text, url, source_type)
            
        except Exception as e:
            print(f"Fallback scraping failed for {url}: {e}")
            return []
    
    def _extract_keywords_from_content(self, html_content: str, url: str, source: str) -> List[RawKeyword]:
        """Extract keywords from HTML content."""
        try:
            # Use trafilatura for better text extraction
            extracted_text = trafilatura.extract(html_content)
            if not extracted_text:
                # Fallback to BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                extracted_text = soup.get_text()
            
            return self._extract_keywords_from_text(extracted_text, url, source)
            
        except Exception as e:
            print(f"Error extracting keywords from {url}: {e}")
            return []
    
    def _extract_keywords_from_text(self, text: str, url: str, source: str) -> List[RawKeyword]:
        """Extract keywords from plain text."""
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            keywords = []
            
            # Extract noun phrases and important terms
            for chunk in doc.noun_chunks:
                if len(chunk.text.strip()) > 2 and len(chunk.text.strip()) < 50:
                    keyword = chunk.text.strip().lower()
                    if keyword and not keyword.isdigit():
                        keywords.append(RawKeyword(
                            keyword=keyword,
                            url=url,
                            source=source,
                            match_type="broad",
                            gkp_avg_monthly_searches=0,  # Will be filled later
                            cluster="extracted"
                        ))
            
            # Extract individual nouns and adjectives
            for token in doc:
                if token.pos_ in ['NOUN', 'PROPN', 'ADJ'] and len(token.text.strip()) > 2:
                    keyword = token.text.strip().lower()
                    if keyword and not keyword.isdigit() and keyword not in [kw.keyword for kw in keywords]:
                        keywords.append(RawKeyword(
                            keyword=keyword,
                            url=url,
                            source=source,
                            match_type="broad",
                            gkp_avg_monthly_searches=0,
                            cluster="extracted"
                        ))
            
            return keywords[:100]  # Limit to 100 keywords per source
            
        except Exception as e:
            print(f"Error processing text from {url}: {e}")
            return []
