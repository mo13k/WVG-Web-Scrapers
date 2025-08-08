from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import requests
import time
from datetime import datetime
import re
import random

class AdvancedStartupScraper:
    def __init__(self):
        self.founders_data = []
        self.setup_selenium()
        
    def setup_selenium(self):
        """Setup Selenium WebDriver with advanced options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"Error setting up Selenium: {e}")
            self.driver = None
    
    def scrape_angel_list(self):
        """Scrape AngelList for Waterloo region startups"""
        print("Scraping AngelList...")
        
        # AngelList requires search functionality
        try:
            if not self.driver:
                return
                
            self.driver.get("https://angel.co/companies")
            time.sleep(3)
            
            # Search for Waterloo region companies
            search_terms = ["Waterloo", "Kitchener", "Cambridge", "Guelph"]
            
            for term in search_terms:
                try:
                    # Look for search box
                    search_box = self.driver.find_element(By.CSS_SELECTOR, "input[type='search'], input[placeholder*='search'], input[name='q']")
                    search_box.clear()
                    search_box.send_keys(term)
                    search_box.send_keys(Keys.RETURN)
                    time.sleep(3)
                    
                    # Extract company information
                    companies = self.driver.find_elements(By.CSS_SELECTOR, ".company-card, .startup-card, .company-item")
                    
                    for company in companies:
                        founder_info = self.extract_angel_list_info(company)
                        if founder_info:
                            self.founders_data.append(founder_info)
                            
                except Exception as e:
                    print(f"Error searching for {term}: {e}")
                    
        except Exception as e:
            print(f"Error scraping AngelList: {e}")
    
    def scrape_f6s(self):
        """Scrape F6S for startup information"""
        print("Scraping F6S...")
        url = "https://www.f6s.com/startups"
        
        try:
            if not self.driver:
                return
                
            self.driver.get(url)
            time.sleep(3)
            
            # Look for startup listings
            startups = self.driver.find_elements(By.CSS_SELECTOR, ".startup-card, .company-card, .startup-item")
            
            for startup in startups:
                founder_info = self.extract_f6s_info(startup)
                if founder_info:
                    self.founders_data.append(founder_info)
                    
        except Exception as e:
            print(f"Error scraping F6S: {e}")
    
    def scrape_startup_ecosystem(self):
        """Scrape Startup Ecosystem Canada"""
        print("Scraping Startup Ecosystem Canada...")
        url = "https://www.startupecosystem.ca/"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for startup listings or company information
            companies = soup.find_all(['div', 'article'], class_=re.compile(r'startup|company|card'))
            
            for company in companies:
                founder_info = self.extract_ecosystem_info(company)
                if founder_info:
                    self.founders_data.append(founder_info)
                    
        except Exception as e:
            print(f"Error scraping Startup Ecosystem: {e}")
    
    def scrape_velocity_fund(self):
        """Scrape Velocity Fund portfolio"""
        print("Scraping Velocity Fund...")
        url = "https://velocityfund.ca/portfolio/"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for portfolio companies
            companies = soup.find_all(['div', 'article'], class_=re.compile(r'portfolio|company|startup'))
            
            for company in companies:
                founder_info = self.extract_velocity_fund_info(company)
                if founder_info:
                    self.founders_data.append(founder_info)
                    
        except Exception as e:
            print(f"Error scraping Velocity Fund: {e}")
    
    def scrape_dmz(self):
        """Scrape DMZ Startup Directory"""
        print("Scraping DMZ Startup Directory...")
        url = "https://dmz.torontomu.ca/startup-directory"
        
        try:
            if not self.driver:
                return
                
            self.driver.get(url)
            time.sleep(5)  # Give more time for dynamic content to load
            
            # Look for startup cards/entries
            startup_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='company'], [class*='startup'], [class*='card']")
            
            for element in startup_elements:
                founder_info = self.extract_dmz_info(element)
                if founder_info:
                    self.founders_data.append(founder_info)
                    
        except Exception as e:
            print(f"Error scraping DMZ: {e}")
    
    def extract_angel_list_info(self, company_element):
        """Extract information from AngelList company element"""
        try:
            # Extract company name
            company_name = ""
            name_elem = company_element.find_element(By.CSS_SELECTOR, "h1, h2, h3, .company-name, .startup-name")
            if name_elem:
                company_name = name_elem.text.strip()
            
            # Extract founder information
            founder_name = ""
            founder_elem = company_element.find_element(By.CSS_SELECTOR, ".founder, .ceo, .team-member")
            if founder_elem:
                founder_name = founder_elem.text.strip()
            
            # Extract contact information
            contact_info = {}
            
            # Look for website
            website_elem = company_element.find_element(By.CSS_SELECTOR, "a[href*='http']")
            if website_elem:
                contact_info['website'] = website_elem.get_attribute('href')
            
            return {
                'founder_name': founder_name,
                'company_name': company_name,
                'source': 'AngelList',
                'contact_info': contact_info,
                'scraped_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error extracting AngelList info: {e}")
            return None
    
    def extract_f6s_info(self, startup_element):
        """Extract information from F6S startup element"""
        try:
            # Extract company name
            company_name = ""
            name_elem = startup_element.find_element(By.CSS_SELECTOR, "h1, h2, h3, .startup-name, .company-name")
            if name_elem:
                company_name = name_elem.text.strip()
            
            # Extract founder information
            founder_name = ""
            founder_elem = startup_element.find_element(By.CSS_SELECTOR, ".founder, .team-member, .ceo")
            if founder_elem:
                founder_name = founder_elem.text.strip()
            
            # Extract contact information
            contact_info = {}
            
            # Look for website
            website_elem = startup_element.find_element(By.CSS_SELECTOR, "a[href*='http']")
            if website_elem:
                contact_info['website'] = website_elem.get_attribute('href')
            
            return {
                'founder_name': founder_name,
                'company_name': company_name,
                'source': 'F6S',
                'contact_info': contact_info,
                'scraped_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error extracting F6S info: {e}")
            return None
    
    def extract_ecosystem_info(self, element):
        """Extract information from Startup Ecosystem Canada"""
        try:
            # Extract company name
            company_name = ""
            company_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or element.find('div', class_=re.compile(r'company|startup|name'))
            if company_elem:
                company_name = company_elem.get_text().strip()
            
            # Extract founder name
            founder_name = ""
            founder_elem = element.find('div', class_=re.compile(r'founder|ceo|director'))
            if founder_elem:
                founder_name = founder_elem.get_text().strip()
            
            # Extract contact information
            contact_info = {}
            
            # Look for email
            email_elem = element.find('a', href=re.compile(r'mailto:'))
            if email_elem:
                contact_info['email'] = email_elem['href'].replace('mailto:', '')
            
            # Look for LinkedIn
            linkedin_elem = element.find('a', href=re.compile(r'linkedin\.com'))
            if linkedin_elem:
                contact_info['linkedin'] = linkedin_elem['href']
            
            # Look for website
            website_elem = element.find('a', href=re.compile(r'http'))
            if website_elem and not any(social in website_elem['href'] for social in ['linkedin.com', 'twitter.com', 'x.com']):
                contact_info['website'] = website_elem['href']
            
            if company_name or founder_name:
                return {
                    'founder_name': founder_name,
                    'company_name': company_name,
                    'source': 'Startup Ecosystem Canada',
                    'contact_info': contact_info,
                    'scraped_date': datetime.now().isoformat()
                }
            
        except Exception as e:
            print(f"Error extracting ecosystem info: {e}")
        
        return None
    
    def extract_velocity_fund_info(self, element):
        """Extract information from Velocity Fund portfolio"""
        try:
            # Extract company name
            company_name = ""
            company_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or element.find('div', class_=re.compile(r'company|startup|name'))
            if company_elem:
                company_name = company_elem.get_text().strip()
            
            # Extract founder name
            founder_name = ""
            founder_elem = element.find('div', class_=re.compile(r'founder|ceo|director'))
            if founder_elem:
                founder_name = founder_elem.get_text().strip()
            
            # Extract contact information
            contact_info = {}
            
            # Look for website
            website_elem = element.find('a', href=re.compile(r'http'))
            if website_elem:
                contact_info['website'] = website_elem['href']
            
            if company_name or founder_name:
                return {
                    'founder_name': founder_name,
                    'company_name': company_name,
                    'source': 'Velocity Fund',
                    'contact_info': contact_info,
                    'scraped_date': datetime.now().isoformat()
                }
            
        except Exception as e:
            print(f"Error extracting Velocity Fund info: {e}")
        
        return None
    
    def extract_dmz_info(self, element):
        """Extract information from DMZ Startup Directory"""
        try:
            # Extract company name
            company_name = ""
            try:
                # Look for company name in various selectors
                name_selectors = ["h1", "h2", "h3", "h4", "h5", "h6", "[class*='company-name']", "[class*='startup-name']"]
                for selector in name_selectors:
                    name_elem = element.find_element(By.CSS_SELECTOR, selector)
                    if name_elem and name_elem.text.strip():
                        company_name = name_elem.text.strip()
                        break
            except:
                pass
            
            # Extract founder information
            founder_names = []
            try:
                # Look for team members/founders
                team_selectors = ["[class*='team']", "[class*='founder']", "[class*='member']", "p"]
                for selector in team_selectors:
                    try:
                        team_elements = element.find_elements(By.CSS_SELECTOR, selector)
                        for team_elem in team_elements:
                            text = team_elem.text.strip()
                            if text and any(keyword in text.lower() for keyword in ['founder', 'ceo', 'co-founder', 'founder']):
                                founder_names.append(text)
                    except:
                        continue
            except:
                pass
            
            # Extract location
            location = ""
            try:
                location_elem = element.find_element(By.CSS_SELECTOR, "[class*='location'], [class*='city'], [class*='address']")
                if location_elem:
                    location = location_elem.text.strip()
            except:
                pass
            
            # Extract contact information
            contact_info = {}
            
            # Look for website
            try:
                website_elem = element.find_element(By.CSS_SELECTOR, "a[href*='http']")
                if website_elem:
                    href = website_elem.get_attribute('href')
                    if href and not any(social in href for social in ['linkedin.com', 'twitter.com', 'x.com', 'facebook.com']):
                        contact_info['website'] = href
            except:
                pass
            
            # Look for LinkedIn
            try:
                linkedin_elem = element.find_element(By.CSS_SELECTOR, "a[href*='linkedin.com']")
                if linkedin_elem:
                    contact_info['linkedin'] = linkedin_elem.get_attribute('href')
            except:
                pass
            
            # Combine founder names
            founder_name = " | ".join(founder_names) if founder_names else ""
            
            # Only return if we have meaningful data
            if company_name or founder_name:
                return {
                    'founder_name': founder_name,
                    'company_name': company_name,
                    'location': location,
                    'source': 'DMZ Startup Directory',
                    'contact_info': contact_info,
                    'scraped_date': datetime.now().isoformat()
                }
            
        except Exception as e:
            print(f"Error extracting DMZ info: {e}")
        
        return None
    
    def filter_waterloo_region(self):
        """Filter results to only include Waterloo region companies"""
        waterloo_keywords = ['waterloo', 'kitchener', 'cambridge', 'guelph', 'kw', 'kw region']
        filtered_data = []
        
        for founder in self.founders_data:
            # Check company name and source for Waterloo region keywords
            text_to_check = f"{founder['company_name']} {founder['source']}".lower()
            if any(keyword in text_to_check for keyword in waterloo_keywords):
                filtered_data.append(founder)
        
        self.founders_data = filtered_data
    
    def save_to_text(self, filename="waterloo_foundersv2.txt"):
        """Save the collected data to a simple text file"""
        if not self.founders_data:
            print("No data to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as textfile:
            textfile.write("WATERLOO REGION STARTUP FOUNDERS\n")
            textfile.write("=" * 50 + "\n\n")
            textfile.write(f"Total founders found: {len(self.founders_data)}\n")
            textfile.write(f"Scraped on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for i, founder in enumerate(self.founders_data, 1):
                textfile.write(f"FOUNDER #{i}\n")
                textfile.write("-" * 20 + "\n")
                textfile.write(f"Founder Name: {founder['founder_name']}\n")
                textfile.write(f"Company Name: {founder['company_name']}\n")
                if founder.get('location'):
                    textfile.write(f"Location: {founder['location']}\n")
                textfile.write(f"Source: {founder['source']}\n")
                
                # Contact information
                contact_info = founder['contact_info']
                if contact_info:
                    textfile.write("Contact Information:\n")
                    if contact_info.get('email'):
                        textfile.write(f"  Email: {contact_info['email']}\n")
                    if contact_info.get('linkedin'):
                        textfile.write(f"  LinkedIn: {contact_info['linkedin']}\n")
                    if contact_info.get('twitter'):
                        textfile.write(f"  Twitter/X: {contact_info['twitter']}\n")
                    if contact_info.get('website'):
                        textfile.write(f"  Website: {contact_info['website']}\n")
                
                textfile.write(f"Scraped Date: {founder['scraped_date']}\n")
                textfile.write("\n" + "=" * 50 + "\n\n")
        
        print(f"Data saved to {filename}")
    
    def run_advanced_scraping(self):
        """Run the advanced scraping process"""
        print("Starting Advanced Waterloo Region Startup Founder Scraping...")
        print("=" * 60)
        
        # Scrape all advanced sources
        self.scrape_angel_list()
        self.scrape_f6s()
        self.scrape_startup_ecosystem()
        self.scrape_velocity_fund()
        self.scrape_dmz()
        
        # Filter for Waterloo region
        self.filter_waterloo_region()
        
        # Save results
        self.save_to_text()
        
        print(f"\nAdvanced scraping completed! Found {len(self.founders_data)} founders in the Waterloo region.")
        
        # Display summary
        for founder in self.founders_data[:5]:  # Show first 5 results
            print(f"\nFounder: {founder['founder_name']}")
            print(f"Company: {founder['company_name']}")
            print(f"Source: {founder['source']}")
            print(f"Contact: {founder['contact_info']}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()

# Example usage
if __name__ == "__main__":
    scraper = AdvancedStartupScraper()
    try:
        scraper.run_advanced_scraping()
    finally:
        scraper.cleanup() 