# this file is used to clean the headers and footers of the text files
import os
import re
from collections import Counter
from pathlib import Path

class PDFHeaderFooterCleaner:
    def __init__(self, folder_path, output_folder=None, threshold=0.7, header_lines=5, footer_lines=5):
        self.folder_path = folder_path
        self.output_folder = output_folder or f"{folder_path}_cleaned"
        self.threshold = threshold
        self.header_lines = header_lines
        self.footer_lines = footer_lines
        self.pages = {}
        self.common_headers = {}
        self.common_footers = {}

    def read_page_files(self):
        """Read all page files and return a dictionary of page_num -> content"""
        pages = {}
        folder = Path(self.folder_path)
        for file_path in folder.glob("page*.txt"):
            match = re.search(r'page[_]?(\d+)', file_path.stem)
            if match:
                page_num = int(match.group(1))
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        pages[page_num] = content
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                        pages[page_num] = content
        self.pages = pages

    @staticmethod
    def extract_lines(text, num_lines=5):
        """Extract first and last N lines from text"""
        lines = text.split('\n')
        first_lines = lines[:num_lines]
        last_lines = lines[-num_lines:] if len(lines) > num_lines else []
        return first_lines, last_lines

    def find_common_patterns(self):
        """Find common header and footer patterns across pages"""
        all_headers = []
        all_footers = []
        for page_num, content in self.pages.items():
            first_lines, last_lines = self.extract_lines(content, max(self.header_lines, self.footer_lines))
            for i in range(min(self.header_lines, len(first_lines))):
                if i < len(first_lines) and first_lines[i].strip():
                    all_headers.append((i, first_lines[i].strip()))
            for i in range(min(self.footer_lines, len(last_lines))):
                if i < len(last_lines) and last_lines[i].strip():
                    all_footers.append((i, last_lines[i].strip()))
        header_counter = Counter(all_headers)
        footer_counter = Counter(all_footers)
        min_occurrences = int(len(self.pages) * self.threshold)
        common_headers = {}
        common_footers = {}
        for (pos, line), count in header_counter.items():
            if count >= min_occurrences:
                if pos not in common_headers:
                    common_headers[pos] = []
                common_headers[pos].append(line)
        for (pos, line), count in footer_counter.items():
            if count >= min_occurrences:
                if pos not in common_footers:
                    common_footers[pos] = []
                common_footers[pos].append(line)
        self.common_headers = common_headers
        self.common_footers = common_footers

    def remove_common_patterns(self, text):
        """Remove identified common headers and footers from text"""
        lines = text.split('\n')
        lines_to_remove_start = 0
        for pos in sorted(self.common_headers.keys()):
            if pos < len(lines):
                line = lines[pos].strip()
                if any(pattern in line or line in pattern for pattern in self.common_headers[pos]):
                    lines_to_remove_start = max(lines_to_remove_start, pos + 1)
        lines_to_remove_end = 0
        for pos in sorted(self.common_footers.keys()):
            if pos < len(lines):
                line = lines[-(pos + 1)].strip()
                if any(pattern in line or line in pattern for pattern in self.common_footers[pos]):
                    lines_to_remove_end = max(lines_to_remove_end, pos + 1)
        if lines_to_remove_end > 0:
            cleaned_lines = lines[lines_to_remove_start:-lines_to_remove_end]
        else:
            cleaned_lines = lines[lines_to_remove_start:]
        return '\n'.join(cleaned_lines)

    def clean_pages(self):
        """Main function to clean all pages"""
        print("Reading page files...")
        self.read_page_files()
        print(f"Found {len(self.pages)} pages")
        if len(self.pages) == 0:
            print("No page files found!")
            return
        print("Analyzing common headers and footers...")
        self.find_common_patterns()
        print(f"\nFound common headers (appearing in at least {self.threshold*100}% of pages):")
        for pos, patterns in self.common_headers.items():
            print(f"  Line {pos}: {patterns}")
        print(f"\nFound common footers (appearing in at least {self.threshold*100}% of pages):")
        for pos, patterns in self.common_footers.items():
            print(f"  Line {pos}: {patterns}")
        os.makedirs(self.output_folder, exist_ok=True)
        print(f"\nCleaning pages and saving to {self.output_folder}...")
        for page_num in sorted(self.pages.keys()):
            content = self.pages[page_num]
            cleaned_content = self.remove_common_patterns(content)
            output_file = os.path.join(self.output_folder, f"page_{page_num}_cleaned.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
        print(f"Cleaned {len(self.pages)} pages successfully!")
        return self.common_headers, self.common_footers

# Example usage
if __name__ == "__main__":
    cleaner = PDFHeaderFooterCleaner(
        folder_path="at90can128_rm.pagewise_txt",
        output_folder="at90can128_rm.cleaned_txt",
        threshold=0.7,
        header_lines=5,
        footer_lines=5
    )
    common_headers, common_footers = cleaner.clean_pages()
    # join all pages after clean into one file
    with open("at90can128_rm.cleaned_txt/all_cleaned.txt", 'w', encoding='utf-8') as f:
        for page_num in sorted(cleaner.pages.keys()):
            content = cleaner.pages[page_num]
            cleaned_content = cleaner.remove_common_patterns(content)
            f.write(cleaned_content)
   
