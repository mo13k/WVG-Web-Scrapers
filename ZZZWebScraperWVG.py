from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import time
from datetime import datetime
import re

class StartupFounderScraper:
    def __init__(self):
        self.founders_data = []
        self.setup_selenium()
        
    def setup_selenium(self):
        """Setup Selenium WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"Error setting up Selenium: {e}")
            self.driver = None
    
    def scrape_velocity_incubator(self):
        """Scrape Velocity Incubator companies"""
        print("Scraping Velocity Incubator...")
        url = "https://velocityincubator.com/companies/"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for company listings
            companies = soup.find_all('div', class_=re.compile(r'company|startup|card'))
            
            for company in companies:
                founder_info = self.extract_founder_info(company, "Velocity Incubator")
                if founder_info:
                    self.founders_data.append(founder_info)
                    
        except Exception as e:
            print(f"Error scraping Velocity Incubator: {e}")
    
    def scrape_communitech(self):
        """Scrape Communitech startups"""
        print("Scraping Communitech...")
        url = "https://communitech.ca/startups/"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for startup listings
            startups = soup.find_all('div', class_=re.compile(r'startup|company|card'))
            
            for startup in startups:
                founder_info = self.extract_founder_info(startup, "Communitech")
                if founder_info:
                    self.founders_data.append(founder_info)
                    
        except Exception as e:
            print(f"Error scraping Communitech: {e}")
    
    def scrape_betakit(self):
        """Scrape BetaKit for Waterloo region startups"""
        print("Scraping BetaKit...")
        url = "https://betakit.com/"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for articles about Waterloo startups
            articles = soup.find_all('article')
            
            for article in articles:
                # Check if article mentions Waterloo region
                text = article.get_text().lower()
                if any(region in text for region in ['waterloo', 'kitchener', 'cambridge', 'guelph']):
                    founder_info = self.extract_founder_info(article, "BetaKit")
                    if founder_info:
                        self.founders_data.append(founder_info)
                        
        except Exception as e:
            print(f"Error scraping BetaKit: {e}")
    
    def scrape_innovation_guelph(self):
        """Scrape Innovation Guelph startups"""
        print("Scraping Innovation Guelph...")
        url = "https://innovationguelph.ca/startups/"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for startup listings
            startups = soup.find_all('div', class_=re.compile(r'startup|company|card'))
            
            for startup in startups:
                founder_info = self.extract_founder_info(startup, "Innovation Guelph")
                if founder_info:
                    self.founders_data.append(founder_info)
                    
        except Exception as e:
            print(f"Error scraping Innovation Guelph: {e}")
    
    def extract_founder_info(self, element, source):
        """Extract founder information from HTML element"""
        try:
            # Extract company name
            company_name = ""
            company_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) or element.find('div', class_=re.compile(r'company|startup|name'))
            if company_elem:
                company_name = company_elem.get_text().strip()
            
            # Extract founder name (this is challenging without specific structure)
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
            
            # Look for Twitter/X
            twitter_elem = element.find('a', href=re.compile(r'twitter\.com|x\.com'))
            if twitter_elem:
                contact_info['twitter'] = twitter_elem['href']
            
            # Look for website
            website_elem = element.find('a', href=re.compile(r'http'))
            if website_elem and not any(social in website_elem['href'] for social in ['linkedin.com', 'twitter.com', 'x.com']):
                contact_info['website'] = website_elem['href']
            
            # Only return if we have meaningful data
            if company_name or founder_name:
                return {
                    'founder_name': founder_name,
                    'company_name': company_name,
                    'source': source,
                    'contact_info': contact_info,
                    'scraped_date': datetime.now().isoformat()
                }
            
        except Exception as e:
            print(f"Error extracting founder info: {e}")
        
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
    
    def save_to_text(self, filename="waterloo_founders.txt"):
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
    
    def run_scraping(self):
        """Run the complete scraping process"""
        print("Starting Waterloo Region Startup Founder Scraping...")
        print("=" * 50)
        
        # Scrape all sources
        self.scrape_velocity_incubator()
        self.scrape_communitech()
        self.scrape_betakit()
        self.scrape_innovation_guelph()
        
        # Filter for Waterloo region
        self.filter_waterloo_region()
        
        # Save results
        self.save_to_text()
        
        print(f"\nScraping completed! Found {len(self.founders_data)} founders in the Waterloo region.")
        
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
    scraper = StartupFounderScraper()
    try:
        scraper.run_scraping()
    finally:
        scraper.cleanup()
