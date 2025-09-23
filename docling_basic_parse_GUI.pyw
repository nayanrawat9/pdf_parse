import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox, BooleanVar
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.pipeline_options import PdfPipelineOptions, granite_picture_description
from docling.datamodel.base_models import InputFormat
from docling_core.types.doc.base import ImageRefMode
from docling.datamodel.settings import settings

class DoclingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Docling PDF Image Extractor")
        
        # Variables for file paths
        self.source_file = tk.StringVar()
        self.output_folder = tk.StringVar()
        
        # Page range variables
        self.start_page = tk.StringVar(value="1")
        self.end_page = tk.StringVar(value="1")
        
        # Pipeline options variables
        self.generate_picture_images = BooleanVar(value=True)
        self.images_scale = tk.StringVar(value="2")
        self.do_picture_classification = BooleanVar(value=False)
        self.do_code_enrichment = BooleanVar(value=True)
        self.do_formula_enrichment = BooleanVar(value=True)
        self.generate_table_images = BooleanVar(value=True)
        self.do_table_structure = BooleanVar(value=False)
        self.do_cell_matching = BooleanVar(value=True)
        self.num_threads = tk.StringVar(value="8")
        self.device = tk.StringVar(value="CPU")
        
        self.create_widgets()

    def create_widgets(self):
        # File selection frame
        file_frame = ttk.LabelFrame(self.root, text="File Selection", padding=5)
        file_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(file_frame, text="Source PDF:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.source_file, width=50).grid(row=0, column=1)
        ttk.Button(file_frame, text="Browse", command=self.browse_source).grid(row=0, column=2)

        ttk.Label(file_frame, text="Output Folder:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.output_folder, width=50).grid(row=1, column=1)
        ttk.Button(file_frame, text="Browse", command=self.browse_output).grid(row=1, column=2)

        # Page Range frame
        page_frame = ttk.LabelFrame(file_frame, text="Page Range", padding=5)
        page_frame.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        ttk.Label(page_frame, text="Start Page:").grid(row=0, column=0, padx=5)
        ttk.Entry(page_frame, textvariable=self.start_page, width=5).grid(row=0, column=1)
        ttk.Label(page_frame, text="End Page:").grid(row=0, column=2, padx=5)
        ttk.Entry(page_frame, textvariable=self.end_page, width=5).grid(row=0, column=3)

        # Pipeline options frame
        options_frame = ttk.LabelFrame(self.root, text="Pipeline Options", padding=5)
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        # Image options
        ttk.Checkbutton(options_frame, text="Generate Picture Images", variable=self.generate_picture_images).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(options_frame, text="Images Scale:").grid(row=0, column=1, sticky=tk.W)
        ttk.Entry(options_frame, textvariable=self.images_scale, width=5).grid(row=0, column=2, sticky=tk.W)
        
        # Other options
        ttk.Checkbutton(options_frame, text="Picture Classification", variable=self.do_picture_classification).grid(row=1, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="Code Enrichment", variable=self.do_code_enrichment).grid(row=1, column=1, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="Formula Enrichment", variable=self.do_formula_enrichment).grid(row=1, column=2, sticky=tk.W)
        
        # Table options
        ttk.Checkbutton(options_frame, text="Generate Table Images", variable=self.generate_table_images).grid(row=2, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="Table Structure", variable=self.do_table_structure).grid(row=2, column=1, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="Cell Matching", variable=self.do_cell_matching).grid(row=2, column=2, sticky=tk.W)
        
        # Accelerator options
        acc_frame = ttk.LabelFrame(options_frame, text="Accelerator Options", padding=5)
        acc_frame.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=5)
        
        ttk.Label(acc_frame, text="Threads:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(acc_frame, textvariable=self.num_threads, width=5).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(acc_frame, text="Device:").grid(row=0, column=2, sticky=tk.W)
        ttk.Combobox(acc_frame, textvariable=self.device, values=["CPU", "CUDA"], width=10).grid(row=0, column=3, sticky=tk.W)

        # Process button
        ttk.Button(self.root, text="Start Processing", command=self.start_processing).pack(pady=5)

        # Log frame
        log_frame = ttk.LabelFrame(self.root, text="Processing Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def browse_source(self):
        filename = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.source_file.set(filename)
            # Auto-generate output folder name if not already set
            if not self.output_folder.get():
                default_output = f"images_{Path(filename).stem}"
                self.output_folder.set(default_output)

    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)

    def log(self, message):
        # Schedule the log update to run in the main thread
        self.root.after(0, self._log_in_main_thread, message)
        
    def _log_in_main_thread(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def process_pdf(self):
        try:
            source_path = self.source_file.get()
            output_folder = self.output_folder.get()
            if not output_folder:
                output_folder = f"images_{Path(source_path).stem}"

            # Configure pipeline options
            pipeline_options = PdfPipelineOptions()
            pipeline_options.generate_picture_images = self.generate_picture_images.get()
            pipeline_options.images_scale = float(self.images_scale.get())
            pipeline_options.do_picture_classification = self.do_picture_classification.get()
            pipeline_options.do_code_enrichment = self.do_code_enrichment.get()
            pipeline_options.do_formula_enrichment = self.do_formula_enrichment.get()
            pipeline_options.picture_description_options = granite_picture_description
            pipeline_options.generate_table_images = self.generate_table_images.get()
            pipeline_options.do_table_structure = self.do_table_structure.get()
            pipeline_options.table_structure_options.do_cell_matching = self.do_cell_matching.get()

            # Configure accelerator options
            accelerator_options = AcceleratorOptions(
                num_threads=int(self.num_threads.get()),
                device=AcceleratorDevice.CUDA if self.device.get() == "CUDA" else AcceleratorDevice.CPU
            )
            pipeline_options.accelerator_options = accelerator_options

            # Enable profiling
            settings.debug.profile_pipeline_timings = True

            self.log(f"Processing PDF: {source_path}")
            self.log(f"Output folder: {output_folder}")

            # Get page range
            try:
                start_page = int(self.start_page.get())
                end_page = int(self.end_page.get())
                if start_page < 1:
                    raise ValueError("Start page must be greater than 0")
                if end_page < start_page:
                    raise ValueError("End page must be greater than or equal to start page")
            except ValueError as e:
                raise ValueError(f"Invalid page range: {str(e)}")

            # Create converter with proper configuration
            converter = DocumentConverter(format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            })

            # Convert the document with page range
            conversion_result = converter.convert(source=source_path, page_range=(start_page, end_page))
            doc = conversion_result.document

            # Process the PDF and extract images
            modified_markdown = doc.export_to_markdown(image_mode=ImageRefMode.PLACEHOLDER)

            # Extract and save images using the existing function's logic
            from docling_basic_parse import extract_images_and_modify_markdown
            modified_markdown, saved_images, saved_tables = extract_images_and_modify_markdown(
                source_path, 
                output_folder=output_folder,
                page_range=(start_page, end_page)
            )

            # Save the modified markdown
            output_md_filename = f"{Path(source_path).stem}_with_images.md"
            with open(output_md_filename, "w", encoding="utf-8") as f:
                f.write(modified_markdown)

            self.log(f"\nExtracted {len([img for img in saved_images if img])} images")
            self.log(f"Extracted {len([tbl for tbl in saved_tables if tbl])} tables")
            self.log(f"Modified markdown saved to: {output_md_filename}")
            self.log(f"Images and tables saved to: {output_folder}/ folder")
            
            messagebox.showinfo("Success", "PDF processing completed successfully!")

        except Exception as e:
            self.log(f"\nError: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def start_processing(self):
        if not self.source_file.get():
            messagebox.showerror("Error", "Please select a PDF file to process.")
            return

        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Start processing in a separate thread
        thread = threading.Thread(target=self.process_pdf)
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = DoclingGUI(root)
    root.mainloop()