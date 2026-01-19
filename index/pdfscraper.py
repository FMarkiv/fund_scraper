import pdfplumber
import os
from pathlib import Path
import re
import csv

# Configuration
PDF_FOLDER = "./pdfs"  # Change this to your PDF folder path
OUTPUT_FILE = "performance_data.csv"

def extract_total_return(pdf_path):
    """Extract Total Return row from page 2 of PDF using text extraction"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Get page 2 (index 1)
            page = pdf.pages[1]
            
            # Extract text
            text = page.extract_text()
            lines = text.split('\n')
            
            # Find "Total Return" line and get the next line with data
            for i, line in enumerate(lines):
                if line.strip() == "Total Return" and i + 1 < len(lines):
                    # Next line should have the data
                    data_line = lines[i + 1]
                    
                    # Extract all numbers (including decimals and negatives)
                    # This will get: index_level, then all the percentages
                    numbers = re.findall(r'-?\d+[\.,]\d+%|-?\d+%', data_line)
                    
                    # Skip the index level (first number), start from the returns
                    if len(numbers) > 1:
                        values = numbers[1:]  # Skip index level
                        
                        return {
                            "filename": os.path.basename(pdf_path),
                            "index_level": numbers[0],
                            "1_mo": values[0] if len(values) > 0 else None,
                            "3_mos": values[1] if len(values) > 1 else None,
                            "ytd": values[2] if len(values) > 2 else None,
                            "1_yr": values[3] if len(values) > 3 else None,
                            "3_yrs": values[4] if len(values) > 4 else None,
                            "5_yrs": values[5] if len(values) > 5 else None,
                            "10_yrs": values[6] if len(values) > 6 else None,
                        }
            
            print(f"⚠️  Could not parse 'Total Return' row in {os.path.basename(pdf_path)}")
            return None
            
    except Exception as e:
        print(f"❌ Error processing {os.path.basename(pdf_path)}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    # Create PDF folder if it doesn't exist
    Path(PDF_FOLDER).mkdir(exist_ok=True)
    
    # Get all PDFs in folder
    pdf_files = list(Path(PDF_FOLDER).glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in '{PDF_FOLDER}' folder")
        print(f"📁 Please add your PDFs to: {os.path.abspath(PDF_FOLDER)}")
        return
    
    print(f"📄 Found {len(pdf_files)} PDFs. Processing...\n")
    
    results = []
    for pdf_file in sorted(pdf_files):
        print(f"Processing: {pdf_file.name}")
        data = extract_total_return(str(pdf_file))
        if data:
            results.append(data)
            print(f"✅ Extracted: 1MO={data['1_mo']}, YTD={data['ytd']}, 1YR={data['1_yr']}\n")
        else:
            print()
    
    if results:
        # Save to CSV
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\n✅ Success! Data saved to: {OUTPUT_FILE}")
        print(f"📊 Extracted {len(results)} files")
        
        # Print preview
        print("\n📋 Preview of extracted data:")
        for result in results[:5]:
            print(f"  {result['filename']}: {result}")
    else:
        print("\n❌ No data extracted from any files")

if __name__ == "__main__":
    main()