from playwright.sync_api import sync_playwright
import pandas as pd
import time

def scrape_dmz(page):
    print("Scraping DMZ Startup Directory...")
    data = []
    page.goto("https://dmz.torontomu.ca/startup-directory", timeout=60000)
    page.wait_for_load_state("networkidle")  # Wait for page to fully load instead of specific selector

    startup_cards = page.query_selector_all("a.card")
    for card in startup_cards:
        name = card.query_selector("h3.card-title").inner_text().strip()
        link = card.get_attribute("href")

        if link.startswith("/"):
            link = "https://dmz.torontomu.ca" + link

        # Visit detail page
        page.goto(link, timeout=60000)
        time.sleep(1)
        founders = []

        founder_elements = page.query_selector_all("p, li, span, div")
        for el in founder_elements:
            text = el.inner_text().strip()
            if "Founder" in text or "Co-Founder" in text:
                founders.append(text)

        data.append({"Startup Name": name, "Founders": ", ".join(set(founders))})

        # Go back to directory
        page.goto("https://dmz.torontomu.ca/startup-directory", timeout=60000)
        page.wait_for_selector("h3.card-title")

    return data


def scrape_velocity(page):
    print("Scraping Velocity Incubator...")
    data = []
    page.goto("https://velocityincubator.com/companies/", timeout=60000)
    time.sleep(10)  # Simple wait instead of waiting for specific state

    startup_cards = page.query_selector_all("div")  # Use generic div selector since specific class doesn't exist
    for card in startup_cards:
        name_el = card.query_selector("h3")
        link_el = card.query_selector("a")
        if not name_el or not link_el:
            continue

        name = name_el.inner_text().strip()
        link = link_el.get_attribute("href")

        # Visit detail page
        page.goto(link, timeout=60000)
        time.sleep(1)
        founders = []

        founder_elements = page.query_selector_all("p, li, span, div")
        for el in founder_elements:
            text = el.inner_text().strip()
            if "Founder" in text or "Co-Founder" in text:
                founders.append(text)

        data.append({"Startup Name": name, "Founders": ", ".join(set(founders))})

        # Go back to main page
        page.goto("https://velocityincubator.com/companies/", timeout=60000)
        page.wait_for_selector("div.company-item")

    return data


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        dmz_data = scrape_dmz(page)
        velocity_data = scrape_velocity(page)

        browser.close()

        # Combine results and save to Excel
        all_data = dmz_data + velocity_data
        df = pd.DataFrame(all_data)
        df.to_csv("WVG Tech Week - Founders List.csv", index=False)
        print("✅ Scraping complete! Saved to startups_dmz_velocity.xlsx")

print("Starting Waterloo Region Startup Founder Scraping.")
print("======================================================================")
main()