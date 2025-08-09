"""
LinkedIn Session Capture Script
===============================

This script helps you capture your LinkedIn authentication session
so the main scraper can access LinkedIn pages without manual login.

Usage:
1. Run this script: python capture_linkedin_session.py
2. Log into LinkedIn manually in the browser window that opens
3. Press Enter in the terminal when logged in
4. The session will be saved to linkedin_session.json
"""

import asyncio
from playwright.async_api import async_playwright
import json

async def capture_linkedin_session():
    """Capture LinkedIn authentication session."""
    print("🔐 LinkedIn Session Capture Tool")
    print("=" * 40)
    
    async with async_playwright() as playwright:
        # Launch browser in non-headless mode so you can log in
        browser = await playwright.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        print("\n📍 Step 1: Opening LinkedIn login page...")
        await page.goto('https://www.linkedin.com/login')
        
        print("\n🔑 Step 2: Please log into LinkedIn manually in the browser window")
        print("   - Enter your email and password")
        print("   - Complete any 2FA if required")
        print("   - Make sure you're fully logged in and can see your LinkedIn feed")
        
        input("\n⏳ Press Enter when you're successfully logged into LinkedIn...")
        
        print("\n🔍 Step 3: Verifying login status...")
        
        # Check if we're actually logged in by going to the feed
        await page.goto('https://www.linkedin.com/feed/')
        await page.wait_for_load_state('networkidle')
        
        # Look for signs that we're logged in
        try:
            # Check for profile picture or navigation elements that indicate login
            await page.wait_for_selector('[data-control-name="nav.settings_and_privacy"]', timeout=5000)
            print("✅ Login verified successfully!")
        except:
            print("⚠️  Warning: Could not verify login. Proceeding anyway...")
        
        print("\n💾 Step 4: Saving session state...")
        
        # Save the storage state (cookies, localStorage, etc.)
        storage_state = await context.storage_state()
        
        with open('linkedin_session.json', 'w') as f:
            json.dump(storage_state, f, indent=2)
        
        print("✅ Session saved to 'linkedin_session.json'")
        print("\n🎉 Setup complete! You can now run the main scraper with LinkedIn access.")
        print("\nNext steps:")
        print("1. Run: python velocity_scraper.py")
        print("2. The scraper will automatically use your saved LinkedIn session")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_linkedin_session())