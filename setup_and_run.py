"""
Setup and Run Script for Velocity LinkedIn Scraper
==================================================

This script handles the installation of dependencies and provides an easy way to run the scraper.
"""

import subprocess
import sys
import os
from pathlib import Path


def install_dependencies():
    """Install required Python packages."""
    print("Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Python dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Python dependencies: {e}")
        return False
    
    print("\nInstalling Playwright browsers...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)
        print("✅ Playwright browsers installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing Playwright browsers: {e}")
        return False
    
    return True


def run_scraper():
    """Run the main scraper."""
    print("\n" + "="*50)
    print("STARTING VELOCITY LINKEDIN SCRAPER")
    print("="*50)
    print("This will:")
    print("1. Navigate to https://www.velocityincubator.com/companies")
    print("2. Filter companies founded in 2023 or later")
    print("3. Extract company names, founders, and LinkedIn profiles")
    print("4. Export data to Excel file")
    print("\nNote: This process may take several minutes depending on the number of companies.")
    print("The browser will open in visible mode so you can monitor progress.")
    
    input("\nPress Enter to continue or Ctrl+C to cancel...")
    
    try:
        from velocity_scraper import main
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Scraping cancelled by user")
    except Exception as e:
        print(f"\n❌ Error running scraper: {e}")


def main():
    """Main setup and run function."""
    print("Velocity LinkedIn Scraper Setup")
    print("=" * 40)
    
    # Check if dependencies are already installed
    try:
        import playwright
        import pandas
        import openpyxl
        print("✅ Dependencies already installed")
        deps_installed = True
    except ImportError:
        deps_installed = False
    
    if not deps_installed:
        install_success = install_dependencies()
        if not install_success:
            print("\n❌ Setup failed. Please install dependencies manually:")
            print("pip install -r requirements.txt")
            print("playwright install")
            return
    
    # Run the scraper
    run_scraper()


if __name__ == "__main__":
    main()