from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests
import time
from datetime import datetime
import re

class ImprovedStartupScraper:
    def __init__(self, max_companies=50):
        self.founders_data = []
        self.max_companies = max_companies
        self.setup_selenium()
        
    def setup_selenium(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Error setting up Selenium: {e}")
            self.driver = None
    
    def scrape_dmz_improved(self):
        print("Scraping DMZ Startup Directory...")
        
        try:
            if not self.driver:
                return
                
            self.driver.get("https://dmz.torontomu.ca/startup-directory")
            time.sleep(20)  # Give plenty of time for JavaScript to load
            
            # Wait for the page to fully load and look for the actual company structure
            # Based on the website content, companies appear to be in a specific layout
            
            # Get all text content to see if data is loading
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            print(f"Page text length: {len(page_text)} characters")
            
            # Try to find the actual container that holds company data
            potential_containers = [
                "main",
                "[role='main']",
                ".startup-directory",
                ".company-directory", 
                ".companies",
                ".startups",
                "div[class*='directory']",
                "div[class*='grid']",
                "div[class*='list']"
            ]
            
            main_container = None
            for container_selector in potential_containers:
                try:
                    container = self.driver.find_element(By.CSS_SELECTOR, container_selector)
                    if container and len(container.text) > 1000:  # Should have substantial content
                        main_container = container
                        print(f"Found main container: {container_selector}")
                        break
                except:
                    continue
            
            if not main_container:
                main_container = self.driver.find_element(By.TAG_NAME, "body")
                print("Using body as main container")
            
            # Now look for individual company elements within the container
            company_selectors = [
                "div:contains('Visit Company')",
                "div:contains('Our Team')",
                "article",
                "section",
                "[class*='card']",
                "[class*='item']",
                "[class*='company']",
                "[class*='startup']"
            ]
            
            found_companies = []
            
            # Try each selector
            for selector in company_selectors:
                try:
                    if "contains" in selector:
                        # Handle :contains() pseudo-selector with XPath
                        if "Visit Company" in selector:
                            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Visit Company')]/ancestor::div[1]")
                        elif "Our Team" in selector:
                            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Our Team')]/ancestor::div[1]")
                        else:
                            elements = []
                    else:
                        elements = main_container.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        print(f"Found {len(elements)} elements with selector: {selector}")
                        
                        for element in elements[:50]:  # Limit to prevent too much processing
                            try:
                                element_text = element.text.strip()
                                if len(element_text) < 20:  # Skip very short elements
                                    continue
                                
                                # Parse the element text to extract company info
                                lines = [line.strip() for line in element_text.split('\n') if line.strip()]
                                
                                company_name = ""
                                location = ""
                                founder_names = []
                                
                                # Look through lines for company info
                                for i, line in enumerate(lines):
                                    # Skip common non-company words
                                    if line.lower() in ['current', 'alumni', 'acquired', 'visit company', 'our team']:
                                        continue
                                    
                                    # First meaningful line is likely company name
                                    if not company_name and len(line) > 2 and len(line) < 100:
                                        # Check if it looks like a company name (not a category or description)
                                        if not any(category in line.lower() for category in ['b2b', 'b2c', 'saas', 'ai', 'fintech', 'healthtech', 'edtech']):
                                            company_name = line
                                    
                                    # Look for location (contains city names)
                                    elif any(city in line.lower() for city in ['toronto', 'kitchener', 'waterloo', 'cambridge', 'guelph', 'ontario', 'on', 'markham', 'etobicoke', 'ottawa', 'montreal', 'vancouver', 'calgary']):
                                        location = line
                                    
                                    # Look for founder information
                                    elif any(title in line.lower() for title in ['ceo', 'founder', 'co-founder', 'president']):
                                        founder_names.append(line)
                                
                                # Only save if we have a company name and it's in target regions
                                if company_name and location:
                                    if any(keyword in location.lower() for keyword in ['waterloo', 'kitchener', 'cambridge', 'guelph', 'hamilton']):
                                        # Check if we already found this company
                                        if not any(existing['company_name'] == company_name for existing in found_companies):
                                            company_data = {
                                                'founder_name': " | ".join(founder_names) if founder_names else "",
                                                'company_name': company_name,
                                                'location': location,
                                                'source': 'DMZ Startup Directory',
                                                # 'contact_info': {},
                                                'scraped_date': datetime.now().isoformat()
                                            }
                                            
                                            found_companies.append(company_data)
                                            self.founders_data.append(company_data)
                                            print(f"Found: {company_name} ({location})")
                                            
                                            # Check if we've reached the maximum
                                            if len(self.founders_data) >= self.max_companies:
                                                print(f"Reached maximum of {self.max_companies} companies. Stopping DMZ scraping.")
                                                return
                                
                            except Exception as e:
                                continue
                                
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")
                    continue
            
            print(f"DMZ scraping completed. Found {len(found_companies)} companies from DMZ.")
            
            # If we still haven't found anything, let's try a more aggressive text parsing approach
            if len(found_companies) == 0:
                print("No companies found with DOM parsing. Trying text parsing...")
                
                # Split the page text and look for company patterns
                text_lines = page_text.split('\n')
                
                i = 0
                while i < len(text_lines) and len(self.founders_data) < self.max_companies:
                    line = text_lines[i].strip()
                    
                    # Look for lines that might be company names (not too short, not common words)
                    if (len(line) > 3 and len(line) < 100 and 
                        not line.lower() in ['current', 'alumni', 'acquired', 'visit company', 'our team', 'ai', 'b2b', 'b2c', 'saas'] and
                        not line.startswith('#') and
                        any(char.isalpha() for char in line)):
                        
                        # Check next few lines for location
                        location = ""
                        for j in range(i+1, min(i+10, len(text_lines))):
                            next_line = text_lines[j].strip()
                            if any(city in next_line.lower() for city in ['toronto', 'kitchener', 'waterloo', 'cambridge', 'guelph', 'ontario', 'markham', 'etobicoke', 'ottawa']):
                                location = next_line
                                break
                        
                        # If we found a location in target regions, save it
                        if location and any(keyword in location.lower() for keyword in ['waterloo', 'kitchener', 'cambridge', 'guelph', 'hamilton']):
                            if not any(existing['company_name'] == line for existing in self.founders_data):
                                self.founders_data.append({
                                    'founder_name': "",
                                    'company_name': line,
                                    'location': location,
                                    'source': 'DMZ Startup Directory',
                                    # 'contact_info': {},
                                    'scraped_date': datetime.now().isoformat()
                                })
                                print(f"Text-parsed: {line} ({location})")
                    
                    i += 1
                    
        except Exception as e:
            print(f"Error scraping DMZ: {e}")
    
    def scrape_velocity_improved(self):
        """Scrape Velocity Incubator with specific filters"""
        print("Scraping Velocity Incubator with filters...")
        
        try:
            if not self.driver:
                return
                
            self.driver.get("https://velocityincubator.com/companies/")
            time.sleep(5)
            
            # Apply filters for Status = "Active" and specific years
            target_years = ["2025", "2024", "2023", "2022", "2021", "2020", "2019"]
            
            for year in target_years:
                try:
                    print(f"Filtering for year: {year}")
                    
                    # Look for year filter and click it
                    year_filters = self.driver.find_elements(By.CSS_SELECTOR, "button, select, option")
                    for filter_elem in year_filters:
                        if year in filter_elem.text:
                            filter_elem.click()
                            time.sleep(2)
                            break
                    
                    # Look for status filter and set to "Active"
                    status_filters = self.driver.find_elements(By.CSS_SELECTOR, "button, select, option")
                    for filter_elem in status_filters:
                        if "active" in filter_elem.text.lower():
                            filter_elem.click()
                            time.sleep(2)
                            break
                    
                    # Extract company information
                    company_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='company'], div[class*='startup'], article, [class*='card']")
                    print(f"Found {len(company_elements)} company elements for year {year}")
                    
                    for element in company_elements:
                        try:
                            # Extract company name
                            company_name = ""
                            name_selectors = ["h1", "h2", "h3", "h4", "h5", "h6", "[class*='company-name']", "[class*='startup-name']", "strong", "b"]
                            for selector in name_selectors:
                                try:
                                    name_elem = element.find_element(By.CSS_SELECTOR, selector)
                                    if name_elem and name_elem.text.strip():
                                        text = name_elem.text.strip()
                                        if len(text) > 2 and len(text) < 100:
                                            company_name = text
                                            break
                                except:
                                    continue
                            
                            # Extract founder information
                            founder_name = ""
                            try:
                                founder_elements = element.find_elements(By.CSS_SELECTOR, "p, span, div")
                                for founder_elem in founder_elements:
                                    text = founder_elem.text.strip()
                                    if text and any(keyword in text.lower() for keyword in ['founder', 'ceo', 'co-founder', 'founder &', 'co-founder &']):
                                        founder_name = text
                                        break
                            except:
                                pass
                            
                            '''
                            # Extract contact information
                            contact_info = {}
                            
                            # Look for website
                            try:
                                website_elements = element.find_elements(By.CSS_SELECTOR, "a[href*='http']")
                                for web_elem in website_elements:
                                    href = web_elem.get_attribute('href')
                                    if href and not any(social in href for social in ['linkedin.com', 'twitter.com', 'x.com', 'facebook.com']):
                                        contact_info['website'] = href
                                        break
                            except:
                                pass
                            '''
                            
                            # Only save if we have meaningful data
                            if company_name:
                                self.founders_data.append({
                                    'founder_name': founder_name,
                                    'company_name': company_name,
                                    'source': f'Velocity Incubator ({year})',
                                    # 'contact_info': contact_info,
                                    'scraped_date': datetime.now().isoformat()
                                })
                                
                                # Check if we've reached the maximum
                                if len(self.founders_data) >= self.max_companies:
                                    print(f"Reached maximum of {self.max_companies} companies. Stopping Velocity scraping.")
                                    return
                                
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    print(f"Error processing year {year}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error scraping Velocity: {e}")
    
    def scrape_boundless_accelerator(self):
        print("Scraping Boundless Accelerator Business Directory...")
        
        try:
            if not self.driver:
                return
                
            self.driver.get("https://onlinebusinessdirectory.boundlessaccelerator.ca/")
            time.sleep(8)  # Give time for dynamic content
            
            # Look for company listings
            company_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='company'], div[class*='business'], div[class*='startup'], article, [class*='card'], [class*='listing']")
            print(f"Found {len(company_elements)} potential company elements")
            
            for element in company_elements:
                try:
                    # Extract company name
                    company_name = ""
                    name_selectors = ["h1", "h2", "h3", "h4", "h5", "h6", "[class*='company-name']", "[class*='business-name']", "[class*='startup-name']", "strong", "b"]
                    for selector in name_selectors:
                        try:
                            name_elem = element.find_element(By.CSS_SELECTOR, selector)
                            if name_elem and name_elem.text.strip():
                                text = name_elem.text.strip()
                                if len(text) > 2 and len(text) < 100:
                                    company_name = text
                                    break
                        except:
                            continue
                    
                    # Extract location
                    location = ""
                    try:
                        location_elements = element.find_elements(By.CSS_SELECTOR, "p, span, div")
                        for loc_elem in location_elements:
                            text = loc_elem.text.strip()
                            if text and any(city in text.lower() for city in ['toronto', 'kitchener', 'waterloo', 'cambridge', 'guelph', 'ontario', 'on']):
                                location = text
                                break
                    except:
                        pass
                    
                    # Extract founder information
                    founder_names = []
                    try:
                        founder_elements = element.find_elements(By.CSS_SELECTOR, "p, span, div")
                        for founder_elem in founder_elements:
                            text = founder_elem.text.strip()
                            if text and any(keyword in text.lower() for keyword in ['founder', 'ceo', 'co-founder', 'founder &', 'co-founder &', 'owner', 'president']):
                                founder_names.append(text)
                    except:
                        pass
                    
                    '''
                    # Extract contact information
                    contact_info = {}
                    
                    # Look for website
                    try:
                        website_elements = element.find_elements(By.CSS_SELECTOR, "a[href*='http']")
                        for web_elem in website_elements:
                            href = web_elem.get_attribute('href')
                            if href and not any(social in href for social in ['linkedin.com', 'twitter.com', 'x.com', 'facebook.com']):
                                contact_info['website'] = href
                                break
                    except:
                        pass
                    
                    # Look for email
                    try:
                        email_elements = element.find_elements(By.CSS_SELECTOR, "a[href*='mailto:']")
                        for email_elem in email_elements:
                            href = email_elem.get_attribute('href')
                            if href and 'mailto:' in href:
                                contact_info['email'] = href.replace('mailto:', '')
                                break
                    except:
                        pass
                    '''
                    
                    # Only save if we have meaningful data
                    if company_name:
                        founder_name = " | ".join(founder_names) if founder_names else ""
                        
                        # Check if it's Waterloo region
                        text_to_check = f"{company_name} {location}".lower()
                        if any(keyword in text_to_check for keyword in ['waterloo', 'kitchener', 'cambridge', 'guelph']):
                            self.founders_data.append({
                                'founder_name': founder_name,
                                'company_name': company_name,
                                'location': location,
                                'source': 'Boundless Accelerator',
                                # 'contact_info': contact_info,
                                'scraped_date': datetime.now().isoformat()
                            })
                            
                            # Check if we've reached the maximum
                            if len(self.founders_data) >= self.max_companies:
                                print(f"Reached maximum of {self.max_companies} companies. Stopping Boundless Accelerator scraping.")
                                return
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error scraping Boundless Accelerator: {e}")
    
    def save_to_text(self, filename="waterloo_foundersv3.txt"):
        """Save the collected data to a text file"""
        if not self.founders_data:
            print("No data to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as textfile:
            textfile.write("IMPROVED WATERLOO REGION STARTUP FOUNDERS\n")
            textfile.write("=" * 60 + "\n\n")
            textfile.write(f"Total founders found: {len(self.founders_data)}\n")
            textfile.write(f"Scraped on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for i, founder in enumerate(self.founders_data, 1):
                textfile.write(f"FOUNDER #{i}\n")
                textfile.write("-" * 30 + "\n")
                textfile.write(f"Founder Name: {founder['founder_name']}\n")
                textfile.write(f"Company Name: {founder['company_name']}\n")
                if founder.get('location'):
                    textfile.write(f"Location: {founder['location']}\n")
                textfile.write(f"Source: {founder['source']}\n")
                
                '''
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
                '''
                
                textfile.write(f"Scraped Date: {founder['scraped_date']}\n")
                textfile.write("\n" + "=" * 60 + "\n\n")
        
        print(f"Data saved to {filename}")
    
    def run_improved_scraping(self):
        print(f"Starting Waterloo Region Startup Founder Scraping (Max: 50 companies)...")
        print("=" * 70)
        
        # Scrape all three websites, then returns progress, more for my own reference
        self.scrape_dmz_improved()
        print(f"After DMZ: {len(self.founders_data)} companies found")
        
        #if len(self.founders_data) < self.max_companies:
            #self.scrape_velocity_improved()
            #print(f"After Velocity: {len(self.founders_data)} companies found")
        
        #if len(self.founders_data) < self.max_companies:
            #self.scrape_boundless_accelerator()
            #print(f"After Boundless: {len(self.founders_data)} companies found")
        
        # Save results
        self.save_to_text()
        
        print(f"\nScraping completed! Found {len(self.founders_data)} founders in the Waterloo region.")
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()

scraper = ImprovedStartupScraper()
try:
    scraper.run_improved_scraping()
finally:
    scraper.cleanup() 