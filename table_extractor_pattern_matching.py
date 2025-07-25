"""
# table_extractor.py
This script extracts and prints table captions and table data from a PDF document, specifically targeting lines that match the pattern for table captions (e.g., "Table 3-1. ...") in the AT90CAN128 reference manual. It uses the `pdfplumber` library to process the PDF, extract text and tables from each page, and print relevant information. The script also summarizes the total number of table captions and tables found, and lists all matched table caption lines with their corresponding page numbers.
Key functionalities:
- Searches for lines matching the table caption pattern using regular expressions.
- Extracts and prints table data from pages containing matched captions.
- Provides a summary of the total lines and tables found.
- Lists all matched table caption lines with page references.
Dependencies:
- pdfplumber
- re
- sys
- io
"""

import pdfplumber
import re
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
docname = "at90can128_rm.pdf"
docname = r"C:\Users\E40065689\Desktop\pdf_parse\at90can128_rm.pdf_chapters\4__Memories.pdf"
docname = r"C:\Users\E40065689\Desktop\pdf_parse\at90can128_rm.pdf_chapters\25__Memory_Programming.pdf"
#docname = "C:/Users/E40065689/Downloads/LS10xxARM.pdf"

pattern = re.compile(r"^\s*table\s+\d+-\d+\..+", re.IGNORECASE)

with pdfplumber.open(docname) as pdf:
    total_tables = 0
    total_lines_found = 0
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        lines = text.splitlines()
        found_lines = [l for l in lines if pattern.search(l)]
        
        if found_lines:
            #print(f"\nPage {page_num + 1}: Found lines with 'Table ':")
            for fl in found_lines:
                print(f"  {fl}")
            total_lines_found += len(found_lines)
        
            tables = page.extract_tables()
            if tables:
                #print(f"  Extracted {len(tables)} tables:")
                total_tables += len(tables)
                for table in tables:
                    for row in table:
                        if row:
                            print(' | '.join(cell if cell else '' for cell in row))

    print("  Total lines found with 'Table': ", total_lines_found)
    print(f"\n Total tables extracted: {total_tables}")
    print("\nSummary:")
    print(f"Processed document: {docname}")
    print(f"Total lines found with 'Table': {total_lines_found}")
    print("Lines found:")
    with pdfplumber.open(docname) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            lines = text.splitlines()
            found_lines = [l for l in lines if pattern.search(l)]
            for fl in found_lines:
                print(f"Page {page_num + 1}: {fl}")

# print as python list the page numbers where the table caption lines are found
page_numbers = []
with pdfplumber.open(docname) as pdf:
    for page_num, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        lines = text.splitlines()
        found_lines = [l for l in lines if pattern.search(l)]
        if found_lines:
            page_numbers.append(page_num + 1)
print("Page numbers where table caption lines were found:", page_numbers)

