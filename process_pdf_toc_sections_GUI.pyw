import os
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import pymupdf as p

class PDFBlockProcessor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = p.open(pdf_path)
        self.toc = self.get_pdf_toc()
        self.all_blocks = self.get_all_blocks()

    def get_pdf_toc(self):
        toc = self.doc.get_toc()
        if not toc:
            raise ValueError("The PDF has no embedded Table of Contents (ToC).")
        return toc

    def get_all_blocks(self):
        all_blocks = []
        for page in self.doc:
            blocks = page.get_text("blocks")
            blocks.sort(key=lambda b: (b[1], b[0]))
            all_blocks.extend(blocks)
        return all_blocks

    def group_blocks_by_toc(self):
        toc_blocks = []
        for toc_entry in self.toc:
            _, title, _ = toc_entry
            for idx, block in enumerate(self.all_blocks):
                text = block[4].strip()
                if text and text.replace('\n', ' ').startswith(title.split(' ', 1)[0]):
                    toc_blocks.append((idx, title))
                    break
        toc_blocks.append((len(self.all_blocks), None))

        groups = []
        for i in range(len(toc_blocks) - 1):
            start, title = toc_blocks[i]
            end, _ = toc_blocks[i + 1]
            group = {
                "toc_title": title,
                "blocks": self.all_blocks[start:end]
            }
            groups.append(group)
        return groups

def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in " ._-" else "_" for c in name).strip()

def process_pdfs(input_folder, output_folder, log_callback):
    if not os.path.isdir(input_folder):
        log_callback(f"Input folder does not exist: {input_folder}\n")
        return
    os.makedirs(output_folder, exist_ok=True)
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_folder, filename)
            try:
                log_callback(f"Processing: {filename}\n")
                processor = PDFBlockProcessor(pdf_path)
                groups = processor.group_blocks_by_toc()
                base_name = os.path.splitext(filename)[0]
                pdf_output_folder = os.path.join(output_folder, base_name)
                os.makedirs(pdf_output_folder, exist_ok=True)
                for i, group in enumerate(groups, 1):
                    toc_title = group['toc_title'] or f"section_{i}"
                    safe_title = sanitize_filename(toc_title)
                    txt_filename = f"{i:02d}_{safe_title}.txt"
                    txt_path = os.path.join(pdf_output_folder, txt_filename)
                    with open(txt_path, "w", encoding="utf-8") as f:
                        for block in group["blocks"]:
                            text = block[4].strip()
                            if text:
                                f.write(text + "\n\n")
                log_callback(f"Done: {filename}\n")
            except Exception as e:
                log_callback(f"Error processing {filename}: {e}\n")

class PDFToCExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF ToC Section Extractor")
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
        frm = tk.Frame(self.root)
        frm.pack(padx=10, pady=10, fill=tk.X)

        tk.Label(frm, text="Input Folder:").grid(row=0, column=0, sticky=tk.W)
        tk.Entry(frm, textvariable=self.input_folder, width=50).grid(row=0, column=1)
        tk.Button(frm, text="Browse", command=self.browse_input).grid(row=0, column=2)

        tk.Label(frm, text="Output Folder:").grid(row=1, column=0, sticky=tk.W)
        tk.Entry(frm, textvariable=self.output_folder, width=50).grid(row=1, column=1)
        tk.Button(frm, text="Browse", command=self.browse_output).grid(row=1, column=2)

        tk.Button(frm, text="Start Processing", command=self.start_processing).grid(row=2, column=0, columnspan=3, pady=10)

        self.log_text = scrolledtext.ScrolledText(self.root, width=80, height=20, state='disabled')
        self.log_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    def browse_input(self):
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_folder.set(folder)

    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)

    def log(self, message):
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    def start_processing(self):
        input_folder = self.input_folder.get()
        output_folder = self.output_folder.get()
        if not input_folder or not output_folder:
            messagebox.showerror("Error", "Please select both input and output folders.")
            return
        self.log("Starting processing...\n")
        thread = threading.Thread(target=process_pdfs, args=(input_folder, output_folder, self.log))
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFToCExtractorGUI(root)
    root.mainloop() 