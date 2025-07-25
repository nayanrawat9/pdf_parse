import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pymupdf as p

class PDFChapterSplitter:
    def __init__(self, docname):
        self.docname = docname
        self.doc = p.open(docname)
        self.toc = self.get_pdf_toc()

    def get_pdf_toc(self):
        toc = self.doc.get_toc()
        if not toc:
            raise ValueError("The PDF has no embedded Table of Contents (ToC).")
        return toc

    def print_toc(self):
        return "\n".join(str(entry) for entry in self.toc)

    def count_top_level_chapters(self):
        top_level_chapters = [entry for entry in self.toc if entry[0] == 1]
        return len(top_level_chapters), [entry[1] for entry in top_level_chapters]

    def get_chapter_ranges(self, manual_ranges=None):
        # manual_ranges: Optional dict {title: (start, end)}
        chapters = [(title, page) for level, title, page in self.toc if level == 1]
        chapter_ranges = []
        for i, (title, start_page) in enumerate(chapters):
            if manual_ranges and title in manual_ranges:
                start_idx, end_idx = manual_ranges[title]
            else:
                start_idx = start_page - 1
                end_idx = len(self.doc)
                for j in range(i + 1, len(chapters)):
                    next_start = chapters[j][1] - 1
                    if next_start == start_idx:
                        # If next chapter starts on the same page, current chapter is a single page
                        end_idx = start_idx + 1
                        break
                    elif next_start > start_idx:
                        end_idx = next_start
                        break
            # Only add if range is valid
            if end_idx > start_idx:
                chapter_ranges.append((title, start_idx, end_idx))
            else:
                chapter_ranges.append((title, start_idx, start_idx + 1))
        return chapter_ranges

    def save_chapters(self, output_dir, output_widget=None, manual_ranges=None):
        os.makedirs(output_dir, exist_ok=True)
        chapter_ranges = self.get_chapter_ranges(manual_ranges=manual_ranges)
        for idx, (title, start, end) in enumerate(chapter_ranges, 1):
            title_clean = "".join(c if c.isalnum() else "_" for c in title)[:50]
            output_path = os.path.join(output_dir, f"{title_clean}.pdf")
            new_doc = p.open()
            new_doc.insert_pdf(self.doc, from_page=start, to_page=end - 1)
            chapter_toc = []
            for entry in self.toc:
                level, entry_title, page = entry
                if start <= page - 1 < end:
                    chapter_toc.append([level, entry_title, (page - start)])
            if chapter_toc:
                new_doc.set_toc(chapter_toc)
            new_doc.save(output_path)
            new_doc.close()
            if output_widget:
                output_widget.insert(tk.END, f"Saved: {output_path}\n")
                output_widget.see(tk.END)
        if output_widget:
            output_widget.insert(tk.END, f"Saved {len(chapter_ranges)} chapters to '{output_dir}' folder.\n")
            output_widget.see(tk.END)

class PDFSplitterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Chapter Splitter")
        self.splitter = None
        self.pdf_path = tk.StringVar()
        self.outdir = tk.StringVar()

        tk.Label(root, text="PDF Chapter Splitter", font=("Arial", 16, "bold")).pack(pady=5)
        frm1 = tk.Frame(root)
        frm1.pack(fill=tk.X, padx=10)
        tk.Label(frm1, text="Select PDF:").pack(side=tk.LEFT)
        tk.Entry(frm1, textvariable=self.pdf_path, width=50, state='readonly').pack(side=tk.LEFT, padx=5)
        tk.Button(frm1, text="Browse", command=self.browse_pdf).pack(side=tk.LEFT)

        frm2 = tk.Frame(root)
        frm2.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(frm2, text="Show ToC", width=15, command=self.show_toc).pack(side=tk.LEFT, padx=2)
        tk.Button(frm2, text="Count/Edit Chapters", width=20, command=self.count_and_edit_chapters).pack(side=tk.LEFT, padx=2)
        tk.Button(frm2, text="Select Output Folder", width=18, command=self.browse_outdir).pack(side=tk.LEFT, padx=2)
        tk.Button(frm2, text="Split Chapters", width=15, command=self.split_chapters).pack(side=tk.LEFT, padx=2)
        self.manual_ranges = None

        frm3 = tk.Frame(root)
        frm3.pack(fill=tk.X, padx=10)
        tk.Label(frm3, text="Output Folder:").pack(side=tk.LEFT)
        tk.Entry(frm3, textvariable=self.outdir, width=40, state='readonly').pack(side=tk.LEFT, padx=5)

        self.output = scrolledtext.ScrolledText(root, width=90, height=18, font=("Consolas", 10))
        self.output.pack(padx=10, pady=8)

    def clear_output(self):
        self.output.delete(1.0, tk.END)

    def browse_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path:
            self.pdf_path.set(path)
            self.clear_output()
            try:
                self.splitter = PDFChapterSplitter(path)
                self.output.insert(tk.END, f"Loaded: {path}\n")
            except Exception as e:
                self.output.insert(tk.END, f"Error: {e}\n")
                self.splitter = None

    def browse_outdir(self):
        folder = filedialog.askdirectory()
        if folder:
            self.outdir.set(folder)
            self.clear_output()
            self.output.insert(tk.END, f"Output folder set to: {folder}\n")

    def show_toc(self):
        self.clear_output()
        if self.splitter:
            self.output.insert(tk.END, self.splitter.print_toc() + "\n")
        else:
            self.output.insert(tk.END, "No PDF loaded.\n")

    def count_and_edit_chapters(self):
        self.clear_output()
        if self.splitter:
            count, names = self.splitter.count_top_level_chapters()
            chapter_ranges = self.splitter.get_chapter_ranges(manual_ranges=self.manual_ranges)
            self.output.insert(tk.END, f"Number of top-level chapters: {count}\n")
            for (title, start, end) in chapter_ranges:
                self.output.insert(
                    tk.END,
                    f"- {title} (pages {start + 1} to {end})\n"
                )
            # Immediately open the edit window
            self.edit_chapter_ranges()
        else:
            self.output.insert(tk.END, "No PDF loaded.\n")

    def split_chapters(self):
        self.clear_output()
        if self.splitter:
            outdir = self.outdir.get() or f"{os.path.splitext(os.path.basename(self.splitter.docname))[0]}_chapters"
            self.output.insert(tk.END, f"Saving chapters to: {outdir}\n")
            try:
                self.splitter.save_chapters(outdir, output_widget=self.output, manual_ranges=self.manual_ranges)
            except Exception as e:
                self.output.insert(tk.END, f"Error: {e}\n")
        else:
            self.output.insert(tk.END, "No PDF loaded.\n")

    def edit_chapter_ranges(self):
        if not self.splitter:
            messagebox.showinfo("No PDF loaded", "Please load a PDF first.")
            return
        # Get current chapter ranges
        chapter_ranges = self.splitter.get_chapter_ranges()
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit Chapter Ranges")
        tk.Label(edit_win, text="Edit start and end page (1-based, inclusive) for each chapter:").pack(pady=5)
        entries = []
        for idx, (title, start, end) in enumerate(chapter_ranges):
            frm = tk.Frame(edit_win)
            frm.pack(fill=tk.X, padx=5, pady=2)
            tk.Label(frm, text=title, width=40, anchor='w').pack(side=tk.LEFT)
            start_var = tk.StringVar(value=str(start + 1))
            end_var = tk.StringVar(value=str(end))
            tk.Entry(frm, textvariable=start_var, width=6).pack(side=tk.LEFT, padx=2)
            tk.Entry(frm, textvariable=end_var, width=6).pack(side=tk.LEFT, padx=2)
            entries.append((title, start_var, end_var))
        def save_ranges():
            manual = {}
            for title, start_var, end_var in entries:
                try:
                    s = int(start_var.get()) - 1
                    e = int(end_var.get())
                    if e > s:
                        manual[title] = (s, e)
                except Exception:
                    continue
            self.manual_ranges = manual
            edit_win.destroy()
            self.output.insert(tk.END, "Manual chapter ranges updated.\n")
        tk.Button(edit_win, text="Save", command=save_ranges).pack(pady=5)

def main():
    root = tk.Tk()
    PDFSplitterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()