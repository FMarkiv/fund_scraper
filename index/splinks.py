import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
import time
import os

# Configuration
EXCEL_FILE = "sp_links.xlsx"
PDF_FOLDER = "./pdfs"
DOWNLOAD_TIMEOUT = 30

def setup_driver():
    """Set up Chrome driver with download preferences"""
    
    # Create download folder if it doesn't exist
    Path(PDF_FOLDER).mkdir(exist_ok=True)
    
    options = webdriver.ChromeOptions()
    
    # Set download folder
    prefs = {
        "download.default_directory": str(Path(PDF_FOLDER).absolute()),
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True,
    }
    options.add_experimental_option("prefs", prefs)
    
    # Uncomment below to run in headless mode (no browser window)
    # options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=options)
    return driver

def download_factsheets():
    """Download factsheets from S&P Global URLs"""
    
    # Check if Excel file exists
    if not Path(EXCEL_FILE).exists():
        print(f"❌ File not found: {EXCEL_FILE}")
        return
    
    # Read Excel file
    try:
        df = pd.read_excel(EXCEL_FILE)
        print(f"📊 Read {len(df)} rows from {EXCEL_FILE}\n")
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return
    
    # Assume first column is sector name, second is URL
    sector_col = df.columns[0]
    url_col = df.columns[1]
    
    print(f"Columns detected: '{sector_col}' | '{url_col}'\n")
    
    driver = setup_driver()
    successful = 0
    failed = 0
    
    try:
        for index, row in df.iterrows():
            sector = row[sector_col]
            url = row[url_col]
            
            # Skip empty rows
            if pd.isna(url) or not url:
                print(f"⏭️  Skipping row {index + 1}: No URL provided")
                continue
            
            print(f"Processing ({index + 1}/{len(df)}): {sector}")
            print(f"  URL: {url}")
            
            try:
                # Navigate to the page
                driver.get(url)
                
                # Wait for page to load
                time.sleep(3)
                
                # Find and click the Factsheet link
                # Look for links in the Documents section
                print(f"  Looking for Factsheet download link...")
                
                try:
                    # Try to find factsheet link (may be in a Documents section)
                    factsheet_link = WebDriverWait(driver, DOWNLOAD_TIMEOUT).until(
                        EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
                    )
                    
                    # Search through links for one containing "factsheet" or "pdf"
                    found = False
                    for link in driver.find_elements(By.TAG_NAME, "a"):
                        link_text = link.text.lower()
                        link_href = link.get_attribute("href") or ""
                        
                        # Look for factsheet link
                        if "factsheet" in link_text or ("pdf" in link_text and "download" in link_text.lower()):
                            print(f"  Found link: {link.text}")
                            link.click()
                            found = True
                            break
                    
                    if found:
                        # Wait for download to complete
                        time.sleep(5)
                        print(f"  ✅ Download initiated\n")
                        successful += 1
                    else:
                        print(f"  ⚠️  Could not find Factsheet link\n")
                        failed += 1
                
                except Exception as e:
                    print(f"  ❌ Error finding/clicking link: {str(e)}\n")
                    failed += 1
            
            except Exception as e:
                print(f"  ❌ Error navigating to URL: {str(e)}\n")
                failed += 1
    
    finally:
        driver.quit()
    
    # Summary
    print("=" * 60)
    print(f"📊 DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 PDFs saved to: {Path(PDF_FOLDER).absolute()}")

if __name__ == "__main__":
    download_factsheets()