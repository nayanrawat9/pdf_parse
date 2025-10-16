import os
import argparse
import pymupdf as p

class PDFChapterSplitter:
    def __init__(self, docname):
        self.docname = docname
        try:
            self.doc = p.open(docname)
        except Exception as e:
            raise IOError(f"Failed to open PDF '{docname}': {e}")
        self.toc = self.get_pdf_toc()

    def get_pdf_toc(self):
        toc = self.doc.get_toc()
        if not toc:
            raise ValueError("The PDF has no embedded Table of Contents (ToC).")
        return toc

    def get_chapter_ranges(self):
        chapters = [(title, page) for level, title, page in self.toc if level == 1]
        chapter_ranges = []
        for i, (title, start_page) in enumerate(chapters):
            start_idx = start_page - 1
            end_idx = len(self.doc)
            # Find the start of the next chapter to determine the end of the current one
            for j in range(i + 1, len(chapters)):
                next_start = chapters[j][1] - 1
                if next_start > start_idx:
                    end_idx = next_start
                    break
            
            if end_idx > start_idx:
                chapter_ranges.append((title, start_idx, end_idx))
            else: # Handle single-page chapters
                chapter_ranges.append((title, start_idx, start_idx + 1))
        return chapter_ranges

    def save_chapters(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        chapter_ranges = self.get_chapter_ranges()
        
        print(f"Found {len(chapter_ranges)} top-level chapters.")
        
        for idx, (title, start, end) in enumerate(chapter_ranges, 1):
            # Clean title for use as a filename
            title_clean = "".join(c if c.isalnum() else "_" for c in title)[:50]
            output_path = os.path.join(output_dir, f"{title_clean}.pdf")
            
            print(f"  -> Saving chapter '{title}' (pages {start + 1}-{end}) to '{output_path}'")
            
            new_doc = p.open()
            new_doc.insert_pdf(self.doc, from_page=start, to_page=end - 1)
            
            # Preserve ToC entries relevant to this chapter
            chapter_toc = []
            for level, entry_title, page in self.toc:
                if start < page <= end:
                    # Adjust page number to be relative to the new document
                    chapter_toc.append([level, entry_title, page - start])
            
            if chapter_toc:
                new_doc.set_toc(chapter_toc)
                
            new_doc.save(output_path)
            new_doc.close()
            
        print(f"\nSuccessfully saved {len(chapter_ranges)} chapters to the '{output_dir}' directory.")

def main():
    parser = argparse.ArgumentParser(
        description="Splits a PDF into separate files based on its top-level table of contents (ToC) chapters.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_pdf",
        help="Path to the input PDF file."
    )
    parser.add_argument(
        "-o", "--output_dir",
        help="Path to the directory where chapter files will be saved.\n" 
             "If not provided, a directory named after the PDF will be created."
    )
    args = parser.parse_args()

    if not os.path.exists(args.input_pdf):
        print(f"Error: Input PDF not found at '{args.input_pdf}'")
        return

    output_dir = args.output_dir
    if not output_dir:
        base_name = os.path.splitext(os.path.basename(args.input_pdf))[0]
        output_dir = f"{base_name}.pdf_chapters"

    try:
        splitter = PDFChapterSplitter(args.input_pdf)
        splitter.save_chapters(output_dir)
    except (IOError, ValueError) as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
