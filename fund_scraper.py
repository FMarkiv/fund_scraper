"""
InvestSmart Fund Performance Scraper
Extracts fund performance data from investsmart.com.au
"""

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import re
from datetime import datetime

def setup_driver():
    """Set up Chrome driver with appropriate options"""
    options = webdriver.ChromeOptions()
    # Run in headless mode (no browser window) - remove this line if you want to see what's happening
    # options.add_argument('--headless')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

def close_modal(driver):
    """Close the signup modal if it appears"""
    try:
        # Wait up to 5 seconds for modal to appear and close it
        wait = WebDriverWait(driver, 5)
        # Try to find and click the close button (X or close button)
        close_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Close'], .modal-close, button.close")))
        close_button.click()
        print("  ✓ Closed signup modal")
        time.sleep(1)
    except TimeoutException:
        print("  ✓ No modal appeared (or already closed)")
    except Exception as e:
        print(f"  ⚠ Modal handling issue: {e}")

def extract_performance_data(driver, url, fund_name):
    """Extract performance table from a single fund page"""
    try:
        print(f"\n📊 Scraping: {fund_name}")
        driver.get(url)
        
        # Wait longer for page to fully load
        time.sleep(5)
        
        # Scroll down to make sure table is in view
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(2)
        
        # Close modal if it appears
        close_modal(driver)
        
        # Find the performance table - try multiple patterns for funds and ETFs
        wait = WebDriverWait(driver, 15)
        table = None
        
        # Pattern 1: Managed funds - h4 "Fund performance"
        try:
            table = driver.find_element(By.XPATH, "//h4[contains(text(), 'Fund performance')]/following-sibling::div//table")
            print("  ✓ Found managed fund performance table")
        except NoSuchElementException:
            pass

        # Pattern 2: ETFs - h2 containing "ETF performance"
        if table is None:
            try:
                table = driver.find_element(By.XPATH, "//h2[contains(text(), 'ETF performance')]/following-sibling::*//table")
                print("  ✓ Found ETF performance table")
            except NoSuchElementException:
                pass

        # Pattern 3: Generic - any heading with "performance"
        if table is None:
            try:
                table = driver.find_element(By.XPATH, "//*[contains(text(), 'performance') and (self::h2 or self::h3 or self::h4)]/following::table[1]")
                print("  ✓ Found performance table (generic)")
            except NoSuchElementException:
                pass
        
        if table is None:
            print(f"  ✗ Could not find performance table")
            return None
        
        # Extract table data
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        if len(rows) < 2:
            print("  ✗ Table found but no data rows")
            return None
        
        data = {
            'Fund Name': fund_name,
            'URL': url,
            'Scraped Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Get headers from first row (could be in <td> or <th> tags)
        header_row = rows[0]
        header_cells = header_row.find_elements(By.TAG_NAME, "td")
        if not header_cells:
            header_cells = header_row.find_elements(By.TAG_NAME, "th")
        header_texts = [cell.text.strip() for cell in header_cells[1:]]  # Skip first empty cell
        
        # Normalize column names to consistent format
        column_mapping = {
            '1 month %': '1M',
            '3 month %': '3M', 
            '6 month %': '6M',
            '1 year % p.a.': '1Y p.a.',
            '2 year % p.a.': '2Y p.a.',
            '3 year % p.a.': '3Y p.a.',
            '5 year % p.a.': '5Y p.a.',
            '10 year % p.a.': '10Y p.a.',
        }
        header_texts = [column_mapping.get(h.lower(), h) for h in header_texts]
        
        print(f"  ✓ Found columns: {', '.join(header_texts)}")
        
        # Find and extract ONLY the "Total return" row from tbody (or directly from table)
        try:
            tbody = table.find_element(By.TAG_NAME, "tbody")
            data_rows = tbody.find_elements(By.TAG_NAME, "tr")
        except NoSuchElementException:
            # Some tables don't have tbody, get rows directly
            data_rows = rows[1:]  # Skip header row
        
        found_total_return = False
        for row in data_rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) > 0:
                row_name = cells[0].text.strip()
                
                # Only process "Total return" row, skip all others
                if row_name.lower() == "total return":
                    for i, cell in enumerate(cells[1:]):
                        if i < len(header_texts):
                            column_key = header_texts[i]
                            data[column_key] = cell.text.strip()
                    found_total_return = True
                    print(f"  ✓ Extracted Total return data: {len(cells)-1} values")
                    break  # Stop after finding Total return row
        
        if not found_total_return:
            print("  ✗ Could not find 'Total return' row")
            return None
        
        # Extract the "As at" date - try multiple patterns
        data['As at Date'] = "Date not found"

        # Pattern 1: small.disclaimer after table
        try:
            disclaimer = table.find_element(By.XPATH, "./following-sibling::small[@class='disclaimer']")
            data['As at Date'] = disclaimer.text.strip()
        except NoSuchElementException:
            pass

        # Pattern 2: Any element containing "As at" near the table
        if data['As at Date'] == "Date not found":
            try:
                disclaimer = table.find_element(By.XPATH, "./following::*[contains(text(), 'As at')][1]")
                data['As at Date'] = disclaimer.text.strip()
            except NoSuchElementException:
                pass

        # Pattern 3: Look in table caption or footer
        if data['As at Date'] == "Date not found":
            try:
                caption = table.find_element(By.TAG_NAME, "caption")
                if "as at" in caption.text.lower():
                    data['As at Date'] = caption.text.strip()
            except NoSuchElementException:
                pass

        # Pattern 4: Look for text after the table containing date pattern
        if data['As at Date'] == "Date not found":
            try:
                # Find any small or p tag after table with date-like content
                elements = driver.find_elements(By.XPATH, "//table/following-sibling::*[self::small or self::p][position()<=3]")
                for el in elements:
                    text = el.text.strip()
                    if 'as at' in text.lower() or 'returns for periods' in text.lower():
                        data['As at Date'] = text
                        break
            except NoSuchElementException:
                pass

        # Pattern 5: Search page for "As at DD Mon YYYY" pattern
        if data['As at Date'] == "Date not found":
            try:
                page_text = driver.find_element(By.TAG_NAME, "body").text
                match = re.search(r'As at \d{1,2} \w{3} \d{4}', page_text)
                if match:
                    data['As at Date'] = match.group(0)
            except NoSuchElementException:
                pass
        
        if data['As at Date'] != "Date not found":
            print(f"  ✓ Found date: {data['As at Date']}")
        else:
            print("  ⚠ Could not find 'As at' date")

        return data
        
    except TimeoutException:
        print(f"  ✗ Timeout - page took too long to load")
        return None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None

def scrape_all_funds(excel_file_path, output_csv_path, batch_size=15, min_delay=10, max_delay=15, batch_break=60):
    """
    Main function to scrape all funds from Excel list
    
    Parameters:
    - excel_file_path: Path to Excel file with Fund Name and URL columns
    - output_csv_path: Where to save the results
    - batch_size: Number of funds to scrape before taking a longer break (default: 15)
    - min_delay: Minimum seconds to wait between requests (default: 10)
    - max_delay: Maximum seconds to wait between requests (default: 15)
    - batch_break: Seconds to wait between batches (default: 60)
    """
    
    # Read Excel file
    print("📂 Reading Excel file...")
    df_input = pd.read_excel(excel_file_path)
    
    # Check if required columns exist
    if 'Fund Name' not in df_input.columns or 'URL' not in df_input.columns:
        print("❌ Error: Excel must have 'Fund Name' and 'URL' columns")
        return
    
    total_funds = len(df_input)
    total_batches = (total_funds + batch_size - 1) // batch_size
    print(f"✓ Found {total_funds} funds to scrape")
    print(f"✓ Will scrape in {total_batches} batches of ~{batch_size} funds each")
    print(f"✓ Random delays: {min_delay}-{max_delay} seconds between funds")
    print(f"✓ Batch breaks: {batch_break} seconds between batches\n")
    
    # Set up browser
    print("🌐 Starting Chrome browser...")
    driver = setup_driver()
    
    all_results = []
    successful = 0
    failed = 0
    
    try:
        for index, row in df_input.iterrows():
            fund_name = row['Fund Name']
            url = row['URL']
            
            current_batch = (index // batch_size) + 1
            position_in_batch = (index % batch_size) + 1
            
            print(f"\n[Batch {current_batch}/{total_batches}] [{position_in_batch}/{min(batch_size, total_funds - (current_batch-1)*batch_size)}]")
            
            # Scrape the fund
            result = extract_performance_data(driver, url, fund_name)
            
            if result:
                all_results.append(result)
                successful += 1
                
                # Save progress after each successful scrape
                df_temp = pd.DataFrame(all_results)
                df_temp.to_csv(output_csv_path, index=False)
                print(f"  💾 Progress saved ({successful} funds so far)")
            else:
                failed += 1
            
            # Check if we've completed a batch
            if (index + 1) % batch_size == 0 and (index + 1) < total_funds:
                print(f"\n{'='*60}")
                print(f"  🎯 BATCH {current_batch} COMPLETE!")
                print(f"  📊 Progress: {index + 1}/{total_funds} funds ({((index + 1)/total_funds*100):.1f}%)")
                print(f"  ✅ Successful: {successful} | ❌ Failed: {failed}")
                print(f"  ☕ Taking a {batch_break} second break before next batch...")
                print(f"{'='*60}\n")
                time.sleep(batch_break)
            elif (index + 1) < total_funds:
                # Random delay between requests within a batch
                wait_time = random.randint(min_delay, max_delay)
                print(f"  ⏳ Waiting {wait_time} seconds before next request...")
                time.sleep(wait_time)
        
        # Final save and summary
        if all_results:
            df_output = pd.DataFrame(all_results)
            df_output.to_csv(output_csv_path, index=False)
            print(f"\n{'='*60}")
            print(f"✅ SCRAPING COMPLETE!")
            print(f"{'='*60}")
            print(f"   📊 Total scraped: {successful}/{total_funds} funds")
            print(f"   ❌ Failed: {failed} funds")
            print(f"   💾 Saved to: {output_csv_path}")
            print(f"{'='*60}")
        else:
            print("\n❌ No data was scraped successfully")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  SCRAPING INTERRUPTED BY USER")
        if all_results:
            df_output = pd.DataFrame(all_results)
            df_output.to_csv(output_csv_path, index=False)
            print(f"   💾 Partial results saved: {len(all_results)} funds")
            print(f"   📁 File: {output_csv_path}")
        print("\nYou can resume later by removing completed funds from your Excel file")
            
    finally:
        driver.quit()
        print("\n🔒 Browser closed")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    # ============ CONFIGURATION ============
    INPUT_EXCEL = "fund_links.xlsx"  # Your Excel file with Fund Name and URL columns
    OUTPUT_CSV = f"fund_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Scraping behavior settings (adjust these as needed):
    BATCH_SIZE = 15          # Scrape this many funds before taking a long break
    MIN_DELAY = 10           # Minimum seconds between requests
    MAX_DELAY = 15           # Maximum seconds between requests
    BATCH_BREAK = 60         # Seconds to wait between batches (1 minute)
    # =======================================
    
    print("=" * 60)
    print("  INVESTSMART FUND PERFORMANCE SCRAPER")
    print("=" * 60)
    
    scrape_all_funds(
        INPUT_EXCEL, 
        OUTPUT_CSV,
        batch_size=BATCH_SIZE,
        min_delay=MIN_DELAY,
        max_delay=MAX_DELAY,
        batch_break=BATCH_BREAK
    )
    
    print("\n" + "=" * 60)
    print("Done! Press Enter to exit...")
    input()