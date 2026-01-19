import pandas as pd
import requests
from pathlib import Path
import time

# Configuration
EXCEL_FILE = "gics_links.xlsx"
PDF_FOLDER = "./pdfs"
DOWNLOAD_TIMEOUT = 30  # seconds

def download_pdfs():
    """Read Excel file and download all PDFs"""
    
    # Check if Excel file exists
    if not Path(EXCEL_FILE).exists():
        print(f"❌ File not found: {EXCEL_FILE}")
        return
    
    # Create PDF folder if it doesn't exist
    Path(PDF_FOLDER).mkdir(exist_ok=True)
    
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
    
    successful = 0
    failed = 0
    
    for index, row in df.iterrows():
        sector = row[sector_col]
        url = row[url_col]
        
        # Skip empty rows
        if pd.isna(url) or not url:
            print(f"⏭️  Skipping row {index + 1}: No URL provided")
            continue
        
        # Create filename from sector name
        filename = f"{sector}.pdf".replace(" ", "_").replace("/", "-")
        filepath = Path(PDF_FOLDER) / filename
        
        print(f"Downloading ({index + 1}/{len(df)}): {sector}")
        print(f"  URL: {url}")
        print(f"  File: {filename}")
        
        try:
            # Add headers to look like a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/pdf',
                'Referer': 'https://www.spglobal.com/'
            }
            
            # Download the PDF
            response = requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True, headers=headers)
            response.raise_for_status()  # Raise exception for bad status codes
            
            # Write to file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Check file size
            file_size = filepath.stat().st_size / (1024 * 1024)  # Convert to MB
            print(f"  ✅ Downloaded ({file_size:.2f} MB)\n")
            successful += 1
            
            # Small delay between downloads to be respectful to the server
            time.sleep(1)
            
        except requests.exceptions.Timeout:
            print(f"  ❌ Timeout (file took too long to download)\n")
            failed += 1
        except requests.exceptions.HTTPError as e:
            print(f"  ❌ HTTP Error: {e.response.status_code}\n")
            failed += 1
        except Exception as e:
            print(f"  ❌ Error: {str(e)}\n")
            failed += 1
    
    # Summary
    print("=" * 60)
    print(f"📊 DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 PDFs saved to: {Path(PDF_FOLDER).absolute()}")

if __name__ == "__main__":
    download_pdfs()