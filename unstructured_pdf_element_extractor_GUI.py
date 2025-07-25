"""
PDF Section Extractor with Visual Bounding Box Display
Uses unstructured to get pdf blocks - sometimes goes L-R instead of top-bottom
"""

import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pymupdf as p
from unstructured.partition.pdf import partition_pdf
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


class PDFSectionExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Section Extractor with Bounding Boxes")
        self.root.geometry("1200x800")
        
        self.pdf_path = "at90can128_rm.pdf_chapters/4__Memories.pdf"
        self.elements = []
        self.doc = None
        self.current_page = 1
        self.total_pages = 0
        
        self.setup_gui()
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # File selection
        ttk.Label(control_frame, text="PDF File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.file_var = tk.StringVar(value=self.pdf_path)
        ttk.Entry(control_frame, textvariable=self.file_var, width=50).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(control_frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=(5, 0))
        
        # Page selection
        ttk.Label(control_frame, text="Pages:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        page_frame = ttk.Frame(control_frame)
        page_frame.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        self.page_mode = tk.StringVar(value="all")
        ttk.Radiobutton(page_frame, text="All pages", variable=self.page_mode, value="all").pack(side=tk.LEFT)
        ttk.Radiobutton(page_frame, text="Single page:", variable=self.page_mode, value="single").pack(side=tk.LEFT, padx=(10, 0))
        self.single_page_var = tk.StringVar(value="1")
        ttk.Entry(page_frame, textvariable=self.single_page_var, width=5).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Radiobutton(page_frame, text="Range:", variable=self.page_mode, value="range").pack(side=tk.LEFT, padx=(10, 0))
        self.range_start_var = tk.StringVar(value="1")
        self.range_end_var = tk.StringVar(value="5")
        ttk.Entry(page_frame, textvariable=self.range_start_var, width=5).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(page_frame, text="to").pack(side=tk.LEFT, padx=(2, 2))
        ttk.Entry(page_frame, textvariable=self.range_end_var, width=5).pack(side=tk.LEFT, padx=(0, 5))
        
        # Process button
        ttk.Button(control_frame, text="Process PDF", command=self.process_pdf).grid(row=2, column=1, pady=(10, 0))
        
        # Results frame with notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Text output tab
        self.text_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.text_frame, text="Text Output")
        
        self.text_output = tk.Text(self.text_frame, wrap=tk.WORD)
        text_scrollbar = ttk.Scrollbar(self.text_frame, orient=tk.VERTICAL, command=self.text_output.yview)
        self.text_output.configure(yscrollcommand=text_scrollbar.set)
        self.text_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Visual tab
        self.visual_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.visual_frame, text="Visual Bounding Boxes")
        
        # Page navigation for visual
        nav_frame = ttk.Frame(self.visual_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(nav_frame, text="Previous", command=self.prev_page).pack(side=tk.LEFT)
        self.page_label = ttk.Label(nav_frame, text="Page 1 of 1")
        self.page_label.pack(side=tk.LEFT, padx=(10, 10))
        ttk.Button(nav_frame, text="Next", command=self.next_page).pack(side=tk.LEFT)
        
        # Matplotlib canvas
        self.fig, self.ax = plt.subplots(figsize=(10, 12))
        self.canvas = FigureCanvasTkAgg(self.fig, self.visual_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.file_var.set(filename)
            self.pdf_path = filename
    
    def get_page_list(self):
        """Get list of pages to process based on user selection"""
        if self.page_mode.get() == "all":
            return None  # Process all pages
        elif self.page_mode.get() == "single":
            try:
                page = int(self.single_page_var.get())
                return [page]
            except ValueError:
                messagebox.showerror("Error", "Invalid page number")
                return None
        else:  # range
            try:
                start = int(self.range_start_var.get())
                end = int(self.range_end_var.get())
                if start > end:
                    messagebox.showerror("Error", "Start page must be <= end page")
                    return None
                return list(range(start, end + 1))
            except ValueError:
                messagebox.showerror("Error", "Invalid page range")
                return None
    
    def process_pdf(self):
        """Process the PDF and extract elements"""
        try:
            self.pdf_path = self.file_var.get()
            if not self.pdf_path:
                messagebox.showerror("Error", "Please select a PDF file")
                return
            
            # Get page list
            page_list = self.get_page_list()
            
            # Process with unstructured
            if page_list:
                # Process specific pages
                self.elements = partition_pdf(self.pdf_path, pages=page_list)
            else:
                # Process all pages
                self.elements = partition_pdf(self.pdf_path)
            
            # Open PDF with PyMuPDF for visualization
            self.doc = p.open(self.pdf_path)
            self.total_pages = len(self.doc)
            
            # Filter elements by page if needed
            if page_list:
                self.elements = [elem for elem in self.elements 
                               if hasattr(elem, 'metadata') and elem.metadata and 
                               getattr(elem.metadata, 'page_number', None) in page_list]
            
            # Update display
            self.display_text_output()
            self.current_page = page_list[0] if page_list else 1
            self.display_visual_output()
            
            messagebox.showinfo("Success", f"Processed {len(self.elements)} elements")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process PDF: {str(e)}")
    
    def display_text_output(self):
        """Display text output with element information"""
        self.text_output.delete(1.0, tk.END)
        
        output = []
        
        # Display elements with location info
        for i, element in enumerate(self.elements):
            output.append(f"Element {i}:")
            output.append(f"Text: {element}")
            output.append(f"Type: {type(element).__name__}")
            
            # Get metadata including coordinates
            if hasattr(element, 'metadata') and element.metadata:
                metadata = element.metadata
                output.append(f"Metadata: {metadata}")
                
                # Extract coordinate information
                coordinates = getattr(metadata, 'coordinates', None)
                if coordinates:
                    output.append(f"Coordinates: {coordinates}")
                    points = coordinates.points if hasattr(coordinates, 'points') else None
                    if points:
                        output.append(f"Bounding box points: {points}")
                
                # Page number
                page_number = getattr(metadata, 'page_number', None)
                if page_number:
                    output.append(f"Page number: {page_number}")
            
            output.append("-" * 40)
        
        # Try to get TOC and section info
        try:
            if self.doc:
                toc = self.get_pdf_toc(self.doc)
                if toc:
                    output.append("\n" + "=" * 60)
                    output.append("TABLE OF CONTENTS:")
                    output.append("=" * 60)
                    for entry in toc:
                        output.append(str(entry))
                    
                    # Section analysis
                    output.append("\n" + "=" * 60)
                    output.append("SECTION ANALYSIS:")
                    output.append("=" * 60)
                    self.analyze_sections(output)
        except Exception as e:
            output.append(f"\nTOC Analysis failed: {str(e)}")
        
        self.text_output.insert(1.0, "\n".join(output))
    
    def get_pdf_toc(self, doc):
        """Get PDF table of contents"""
        toc = doc.get_toc()
        if not toc:
            raise ValueError("The PDF has no embedded Table of Contents (ToC).")
        return toc
    
    def analyze_sections(self, output):
        """Analyze sections based on TOC"""
        try:
            toc = self.get_pdf_toc(self.doc)
            
            def extract_section_number(title):
                match = re.match(r"^(\d+(\.\d+)*)", title.strip())
                return match.group(1) if match else None
            
            # Build mapping from section number to element index
            section_to_index = {}
            for idx, element in enumerate(self.elements):
                text = str(element)
                sec_num = extract_section_number(text)
                if sec_num:
                    section_to_index[sec_num] = idx
            
            # Map TOC entries to elements
            toc_sections = []
            for entry in toc:
                title = entry[1]
                sec_num = extract_section_number(title)
                if sec_num and sec_num in section_to_index:
                    toc_sections.append((sec_num, section_to_index[sec_num], title))
            
            toc_sections.sort(key=lambda x: x[1])
            
            # Display sections
            for i, (sec_num, start_idx, title) in enumerate(toc_sections):
                end_idx = toc_sections[i + 1][1] if i + 1 < len(toc_sections) else len(self.elements)
                
                section_elements = self.elements[start_idx:end_idx]
                section_elements_with_pos = [(elem, self.get_element_position(elem)) for elem in section_elements]
                section_elements_with_pos.sort(key=lambda x: (
                    getattr(x[0].metadata, 'page_number', 0) if hasattr(x[0], 'metadata') and x[0].metadata else 0,
                    x[1]
                ))
                
                output.append(f"Section {sec_num} ({title}):")
                for elem, pos in section_elements_with_pos:
                    page_num = getattr(elem.metadata, 'page_number', 'Unknown') if hasattr(elem, 'metadata') and elem.metadata else 'Unknown'
                    output.append(f"[Page {page_num}, Y-pos: {pos:.1f}] {elem}")
                output.append("=" * 60)
                
        except Exception as e:
            output.append(f"Section analysis failed: {str(e)}")
    
    def get_element_position(self, element):
        """Extract y-coordinate for sorting elements by vertical position"""
        if hasattr(element, 'metadata') and element.metadata:
            coordinates = getattr(element.metadata, 'coordinates', None)
            if coordinates and hasattr(coordinates, 'points') and coordinates.points:
                y_coords = [point[1] for point in coordinates.points]
                return min(y_coords) if y_coords else float('inf')
        return float('inf')
    
    def display_visual_output(self):
        """Display visual bounding boxes for current page"""
        if not self.doc or not self.elements:
            return
        
        self.ax.clear()
        
        # Get page
        if self.current_page > len(self.doc):
            self.current_page = len(self.doc)
        if self.current_page < 1:
            self.current_page = 1
            
        page = self.doc[self.current_page - 1]
        
        # Get page image
        mat = p.Matrix(2, 2)  # 2x zoom
        pix = page.get_pixmap(matrix=mat)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        
        # Display page image
        self.ax.imshow(img)
        
        # Get elements for this page
        page_elements = [elem for elem in self.elements 
                        if hasattr(elem, 'metadata') and elem.metadata and 
                        getattr(elem.metadata, 'page_number', None) == self.current_page]
        
        # Draw bounding boxes
        colors = plt.cm.Set3(np.linspace(0, 1, len(page_elements)))
        
        for i, element in enumerate(page_elements):
            if hasattr(element, 'metadata') and element.metadata:
                coordinates = getattr(element.metadata, 'coordinates', None)
                if coordinates and hasattr(coordinates, 'points') and coordinates.points:
                    points = coordinates.points
                    if len(points) >= 4:
                        # Convert coordinates (scale by 2 for zoom)
                        x_coords = [p[0] * 2 for p in points]
                        y_coords = [p[1] * 2 for p in points]
                        
                        # Create rectangle
                        min_x, max_x = min(x_coords), max(x_coords)
                        min_y, max_y = min(y_coords), max(y_coords)
                        
                        rect = patches.Rectangle(
                            (min_x, min_y), max_x - min_x, max_y - min_y,
                            linewidth=2, edgecolor=colors[i], facecolor='none', alpha=0.7
                        )
                        self.ax.add_patch(rect)
                        
                        # Add element number
                        self.ax.text(min_x, min_y - 10, f"{i}", 
                                   fontsize=8, color=colors[i], weight='bold')
        
        self.ax.set_title(f"Page {self.current_page} - Bounding Boxes ({len(page_elements)} elements)")
        self.ax.set_xlim(0, pix.width)
        self.ax.set_ylim(pix.height, 0)  # Flip Y axis
        
        self.page_label.config(text=f"Page {self.current_page} of {self.total_pages}")
        self.canvas.draw()
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self.display_visual_output()
    
    def next_page(self):
        """Go to next page"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.display_visual_output()


def main():
    root = tk.Tk()
    app = PDFSectionExtractor(root)
    root.mainloop()


if __name__ == "__main__":
    main()