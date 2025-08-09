"""
Velocity Incubator Web Scraper
===============================

A comprehensive web scraping bot using Playwright and pandas to gather startup data
from the Velocity incubator website and LinkedIn. Extracts company names, founder names,
and founder LinkedIn profile URLs for companies founded in 2023 or later.

Requirements:
- playwright
- pandas
- openpyxl

Install with: pip install playwright pandas openpyxl
Then run: playwright install
"""

import asyncio
import re
import time
from typing import List, Dict, Optional
import pandas as pd
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VelocityLinkedInScraper:
    """Main scraper class for extracting startup data from Velocity and LinkedIn."""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.companies_data: List[Dict] = []
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.setup_browser()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
        
    async def setup_browser(self):
        """Initialize Playwright browser and context."""
        logger.info("Setting up browser...")
        self.playwright = await async_playwright().start()
        
        # Use Chromium with realistic user agent
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage'
            ]
        )
        
        # Try to load saved LinkedIn session
        storage_state = None
        try:
            import json
            with open('linkedin_session.json', 'r') as f:
                storage_state = json.load(f)
            logger.info("✅ Loaded saved LinkedIn session")
        except FileNotFoundError:
            logger.warning("⚠️ No LinkedIn session found. LinkedIn features may not work.")
            logger.info("💡 Run 'python capture_linkedin_session.py' to set up LinkedIn access")
        except Exception as e:
            logger.warning(f"⚠️ Could not load LinkedIn session: {e}")
        
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            storage_state=storage_state  # This loads the saved session
        )
        
    async def cleanup(self):
        """Clean up browser resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
            
    async def wait_for_page_load(self, page: Page, timeout: int = 30000):
        """Wait for page to fully load with multiple strategies."""
        try:
            await page.wait_for_load_state('networkidle', timeout=timeout)
            await asyncio.sleep(1)  # Additional buffer
        except Exception as e:
            logger.warning(f"Network idle timeout, continuing: {e}")
            await page.wait_for_load_state('domcontentloaded', timeout=10000)
            
    async def extract_velocity_join_year(self, page: Page) -> Optional[int]:
        """Extract year company joined Velocity program from company page."""
        # Look for Velocity-specific join year indicators
        join_year_selectors = [
            'text=/year joined/i',
            'text=/joined.*202[3-5]/i',  # Specifically look for 2023-2025
            'text=/velocity.*202[3-5]/i',
            '[class*="year"]',
            '[class*="joined"]'
        ]
        
        # First, try to find explicit "Year joined" information
        for selector in join_year_selectors:
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    text = await element.text_content()
                    if text and ('joined' in text.lower() or 'velocity' in text.lower()):
                        # Look for years 2023-2025 specifically
                        years = re.findall(r'\b(202[3-5])\b', text)
                        if years:
                            return int(years[0])
            except Exception:
                continue
        
        # Look for any mention of recent years (2023-2025) in the context of joining/starting
        try:
            content = await page.content()
            
            # Look for patterns like "Year joined: 2024" or "Joined Velocity in 2023"
            join_patterns = [
                r'year\s+joined[:\s]+(\d{4})',
                r'joined[:\s]+(\d{4})',
                r'velocity[:\s]+(\d{4})',
                r'since[:\s]+(\d{4})',
                r'(\d{4})[:\s]*(?:joined|velocity|program)'
            ]
            
            for pattern in join_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    year = int(match)
                    if 2023 <= year <= 2025:
                        return year
            
            # Fallback: look for any years 2023-2025 in the content
            recent_years = re.findall(r'\b(202[3-5])\b', content)
            if recent_years:
                # Return the earliest year found (likely join year)
                return min(int(year) for year in recent_years)
                
        except Exception:
            pass
            
        return None
        
    async def scrape_velocity_companies(self, max_companies: int = 5) -> List[Dict]:
        """Main method to scrape companies from Velocity website."""
        logger.info(f"Starting Velocity website scraping (stopping after {max_companies} successful companies)...")
        
        page = await self.context.new_page()
        
        try:
            # Navigate to Velocity companies page
            logger.info("Navigating to Velocity companies page...")
            await page.goto('https://www.velocityincubator.com/companies', timeout=60000)
            await self.wait_for_page_load(page)
            
            # Find all company cards/links
            company_selectors = [
                'a[href*="/company/"]',
                'a[href*="/companies/"]',
                '.company-card a',
                '[class*="company"] a',
                'a:has-text("View")',
                'a:has-text("Company")'
            ]
            
            company_links = []
            for selector in company_selectors:
                try:
                    links = await page.locator(selector).all()
                    for link in links:
                        href = await link.get_attribute('href')
                        if href and ('company' in href.lower() or 'view' in href.lower()):
                            if href.startswith('/'):
                                href = f"https://www.velocityincubator.com{href}"
                            company_links.append(href)
                    if company_links:
                        break
                except Exception:
                    continue
            
            if not company_links:
                # Fallback: look for any links that might be companies
                all_links = await page.locator('a').all()
                for link in all_links:
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    if href and text and ('company' in text.lower() or 'view' in text.lower()):
                        if href.startswith('/'):
                            href = f"https://www.velocityincubator.com{href}"
                        company_links.append(href)
            
            logger.info(f"Found {len(company_links)} potential company links")
            
            # Remove duplicates
            company_links = list(set(company_links))
            
            # Process each company until we reach max_companies successful ones
            successful_companies = 0
            for i, company_url in enumerate(company_links, 1):
                if successful_companies >= max_companies:
                    logger.info(f"✅ Reached target of {max_companies} companies! Stopping scraping.")
                    break
                    
                logger.info(f"Processing company {i}/{len(company_links)} (Success: {successful_companies}/{max_companies}): {company_url}")
                
                try:
                    company_data = await self.process_company(company_url)
                    if company_data:
                        self.companies_data.append(company_data)
                        successful_companies += 1
                        logger.info(f"✅ Successfully processed ({successful_companies}/{max_companies}): {company_data['Company']}")
                        
                        # Save progress incrementally so data isn't lost if interrupted
                        await self.save_progress()
                    else:
                        logger.info(f"⏭️ Skipped company (joined Velocity before 2023): {company_url}")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing company {company_url}: {e}")
                    continue
                    
                # Small delay between requests
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Error scraping Velocity companies: {e}")
            
        finally:
            await page.close()
            
        return self.companies_data
        
    async def process_company(self, company_url: str) -> Optional[Dict]:
        """Process individual company page."""
        page = await self.context.new_page()
        
        try:
            await page.goto(company_url, timeout=60000)
            await self.wait_for_page_load(page)
            
            # Extract Velocity join year first
            join_year = await self.extract_velocity_join_year(page)
            
            # If we can determine the join year, check if it's 2023 or later
            if join_year is not None:
                if join_year < 2023:
                    logger.info(f"Company joined Velocity in {join_year} (before 2023) - skipping")
                    await page.close()
                    return None
                else:
                    logger.info(f"Company joined Velocity in {join_year} - proceeding with extraction")
            else:
                # If we can't determine join year, include it anyway (better to be inclusive)
                logger.info(f"Could not determine Velocity join year - including company anyway")
            
            # Extract company name
            company_name = await self.extract_company_name(page)
            
            # Extract founders
            founders = await self.extract_founders(page)
            
            # Extract LinkedIn URL
            linkedin_url = await self.extract_company_linkedin(page)
            
            if not company_name:
                logger.warning("Could not extract company name, skipping")
                return None
                
            company_data = {
                'Company': company_name,
                'Founders': founders,
                'Linkedins': []
            }
            
            # If we have LinkedIn URL and founders, get founder LinkedIn profiles
            if linkedin_url and founders:
                founder_linkedins = await self.extract_founder_linkedins(linkedin_url, founders)
                company_data['Linkedins'] = founder_linkedins
                
            return company_data
            
        except Exception as e:
            logger.error(f"Error processing company page {company_url}: {e}")
            return None
            
        finally:
            await page.close()
            
    async def extract_company_name(self, page: Page) -> str:
        """Extract company name from company page."""
        name_selectors = [
            'h1',
            '.company-name',
            '[class*="company"][class*="name"]',
            '[class*="title"]',
            'title'
        ]
        
        for selector in name_selectors:
            try:
                element = await page.locator(selector).first
                if element:
                    text = await element.text_content()
                    if text and len(text.strip()) > 0:
                        return text.strip()
            except Exception:
                continue
                
        # Fallback: extract from page title
        try:
            title = await page.title()
            if title and '|' in title:
                return title.split('|')[0].strip()
            elif title:
                return title.strip()
        except Exception:
            pass
            
        return "Unknown Company"
        
    async def extract_founders(self, page: Page) -> List[str]:
        """Extract founder names from company page."""
        founders = []
        
        founder_selectors = [
            'text=/founder/i',
            'text=/co-founder/i',
            'text=/ceo/i',
            '[class*="founder"]',
            '[class*="team"]',
            '[class*="leadership"]'
        ]
        
        for selector in founder_selectors:
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    text = await element.text_content()
                    if text:
                        # Extract names using patterns
                        names = self.extract_names_from_text(text)
                        founders.extend(names)
            except Exception:
                continue
                
        # Remove duplicates and clean up
        founders = list(set([name.strip() for name in founders if name.strip()]))
        return founders
        
    def extract_names_from_text(self, text: str) -> List[str]:
        """Extract person names from text using patterns."""
        names = []
        
        # Pattern for names (First Last, possibly with middle initial)
        name_pattern = r'\b([A-Z][a-z]+ (?:[A-Z]\. )?[A-Z][a-z]+)\b'
        matches = re.findall(name_pattern, text)
        
        for match in matches:
            # Filter out common false positives
            if not any(word in match.lower() for word in ['company', 'inc', 'llc', 'corp', 'ltd']):
                names.append(match)
                
        return names
        
    async def extract_company_linkedin(self, page: Page) -> Optional[str]:
        """Extract company LinkedIn URL from company page."""
        linkedin_selectors = [
            'a[href*="linkedin.com/company"]',
            'a[href*="linkedin.com/in"]',
            '[href*="linkedin"]'
        ]
        
        for selector in linkedin_selectors:
            try:
                elements = await page.locator(selector).all()
                for element in elements:
                    href = await element.get_attribute('href')
                    if href and 'linkedin.com/company' in href:
                        return href
            except Exception:
                continue
                
        return None
        
    async def extract_founder_linkedins(self, company_linkedin_url: str, founders: List[str]) -> List[str]:
        """Extract founder LinkedIn profiles from company LinkedIn page."""
        if not company_linkedin_url or not founders:
            return []
            
        page = await self.context.new_page()
        founder_linkedins = []
        
        try:
            logger.info(f"Navigating to LinkedIn: {company_linkedin_url}")
            await page.goto(company_linkedin_url, timeout=60000)
            await self.wait_for_page_load(page)
            
            # Try to click on People tab
            people_selectors = [
                'a:has-text("People")',
                'button:has-text("People")',
                '[data-control-name*="people"]',
                'text=/people/i'
            ]
            
            people_clicked = False
            for selector in people_selectors:
                try:
                    people_tab = await page.locator(selector).first
                    if people_tab:
                        await people_tab.click()
                        await self.wait_for_page_load(page)
                        people_clicked = True
                        break
                except Exception:
                    continue
                    
            if not people_clicked:
                logger.warning("Could not find or click People tab")
                return []
                
            # Look for founder profiles
            for founder in founders:
                try:
                    # Search for founder name in various ways
                    founder_selectors = [
                        f'a:has-text("{founder}")',
                        f'[title*="{founder}"]',
                        f'text=/{re.escape(founder)}/i'
                    ]
                    
                    for selector in founder_selectors:
                        try:
                            elements = await page.locator(selector).all()
                            for element in elements:
                                href = await element.get_attribute('href')
                                if href and 'linkedin.com/in/' in href:
                                    founder_linkedins.append(href)
                                    logger.info(f"Found LinkedIn for {founder}: {href}")
                                    break
                        except Exception:
                            continue
                            
                except Exception as e:
                    logger.warning(f"Error finding LinkedIn for {founder}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting founder LinkedIns: {e}")
            
        finally:
            await page.close()
            
        return list(set(founder_linkedins))  # Remove duplicates
        
    async def save_progress(self):
        """Save current progress to avoid losing data on interruption."""
        if not self.companies_data:
            return
            
        try:
            import json
            progress_filename = 'velocity_scraper_progress.json'
            with open(progress_filename, 'w', encoding='utf-8') as f:
                json.dump(self.companies_data, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Progress saved: {len(self.companies_data)} companies")
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
        
    def export_to_excel(self, filename: str = 'velocity_startups_data.xlsx'):
        """Export collected data to Excel file."""
        if not self.companies_data:
            logger.warning("No data to export")
            return
            
        logger.info(f"Exporting {len(self.companies_data)} companies to {filename}")
        
        # Prepare data for DataFrame
        export_data = []
        for company in self.companies_data:
            # Convert lists to strings for Excel export
            founders_str = '; '.join(company['Founders']) if company['Founders'] else ''
            linkedins_str = '; '.join(company['Linkedins']) if company['Linkedins'] else ''
            
            export_data.append({
                'Company': company['Company'],
                'Founders': founders_str,
                'Linkedins': linkedins_str
            })
            
        # Create DataFrame and export
        df = pd.DataFrame(export_data)
        df.to_excel(filename, index=False, engine='openpyxl')
        logger.info(f"Data exported successfully to {filename}")
        
        # Also save as JSON for backup
        import json
        json_filename = filename.replace('.xlsx', '.json')
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.companies_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Backup JSON saved to {json_filename}")


async def main():
    """Main execution function."""
    logger.info("Starting Velocity LinkedIn Scraper...")
    
    async with VelocityLinkedInScraper(headless=False) as scraper:
        # Scrape companies data (limit to 5 successful companies)
        companies_data = await scraper.scrape_velocity_companies(max_companies=5)
        
        # Export results
        scraper.export_to_excel()
        
        # Print summary
        logger.info(f"\n{'='*50}")
        logger.info(f"SCRAPING COMPLETED")
        logger.info(f"{'='*50}")
        logger.info(f"Total companies processed: {len(companies_data)}")
        
        for i, company in enumerate(companies_data, 1):
            logger.info(f"\n{i}. {company['Company']}")
            logger.info(f"   Founders: {', '.join(company['Founders']) if company['Founders'] else 'None found'}")
            logger.info(f"   LinkedIn profiles: {len(company['Linkedins'])} found")


if __name__ == "__main__":
    asyncio.run(main())