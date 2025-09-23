import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import ollama
from threading import Thread

# Example image path (adjust this to a real example in your setup)
EXAMPLE_IMAGE = r"C:\Users\E40065689\Desktop\pdf_parse\images_10__External_Interrupts\table_6.png"

# Available models
MODELS = ["qwen2.5vl:7b", "qwen2.5vl:3b", "gemma3:4b"]

# Base prompt with one-shot example
BASE_PROMPT = """
The provided image may or may not contain a table.
If it does, please convert it to markdown format text.
Else, just say 'No table found'.

Requirements:
- Preserve the table structure with vertical and horizontal lines.
- Keep all column and row alignments intact.
- Do not skip any columns or rows, even if they are empty.
- Use Markdown pipes (|) and dashes (---).

Example:
The first image will be provided, and I will also provide the expected Markdown output.

Expected output for the first image:
| Bit           | 7     | 6     | 5     | 4     | 3     | 2     | 1     | 0     |       |
| ------------- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
|               | INTF7 | INTF6 | INTF5 | INTF4 | INTF3 | INTF2 | INTF1 | INTF0 | EIFR  |
| Read/Write    | R/W   | R/W   | R/W   | R/W   | R/W   | R/W   | R/W   | R/W   |       |
| Initial Value | 0     | 0     | 0     | 0     | 0     | 0     | 0     | 0     |       |

The second image may or may not contain a table with similar formatting.
Now, extract the table from the second image:
"""

class MarkdownImageProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Markdown Image Processor")
        self.root.geometry("800x500")
        self.root.configure(padx=20, pady=20)

        # Create main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Style configuration
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))
        
        # File selection frame
        file_frame = ttk.LabelFrame(self.main_frame, text="Input Selection", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side=tk.RIGHT, padx=5)

        # Model selection frame
        model_frame = ttk.LabelFrame(self.main_frame, text="Model Configuration", padding="10")
        model_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(model_frame, text="Select Model:").pack(side=tk.LEFT, padx=5)
        self.model_var = tk.StringVar(value=MODELS[0])
        model_dropdown = ttk.Combobox(model_frame, textvariable=self.model_var, values=MODELS, state="readonly", width=30)
        model_dropdown.pack(side=tk.LEFT, padx=5)

        # Progress frame
        progress_frame = ttk.LabelFrame(self.main_frame, text="Progress", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        # Overall progress
        self.progress_label = ttk.Label(progress_frame, text="Progress: 0/0")
        self.progress_label.pack(fill=tk.X, padx=5)
        self.total_progress = ttk.Progressbar(progress_frame, mode="determinate")
        self.total_progress.pack(fill=tk.X, padx=5, pady=5)

        # Control buttons frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        self.process_button = ttk.Button(button_frame, text="Process Markdown", command=self.start_processing)
        self.process_button.pack(pady=5)

        # Status label
        self.status_label = ttk.Label(self.main_frame, text="", wraplength=750)
        self.status_label.pack(fill=tk.X, pady=(10, 0))

    def browse_file(self):
        file_selected = filedialog.askopenfilename(
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        if file_selected:
            self.file_path.set(file_selected)

    def start_processing(self):
        if not self.file_path.get() or not os.path.isfile(self.file_path.get()):
            messagebox.showerror("Error", "Please select a valid markdown file.")
            return

        # Disable controls during processing
        self.process_button.state(["disabled"])
        
        # Start processing in a separate thread
        Thread(target=self.process_markdown, daemon=True).start()

    def process_markdown(self):
        try:
            md_file_path = self.file_path.get()
            output_file = os.path.splitext(md_file_path)[0] + "_processed.md"
            
            # Read the markdown file
            with open(md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find all image references
            image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            matches = list(re.finditer(image_pattern, content))

            if not matches:
                self.update_status("No images found in the markdown file.")
                self.process_button.state(["!disabled"])
                return

            # Configure progress bar
            total_images = len(matches)
            self.total_progress["maximum"] = total_images
            self.total_progress["value"] = 0
            self.root.after(0, lambda: self.progress_label.configure(text=f"Progress: 0/{total_images}"))

            # Process each image and update the content
            new_content = []
            last_end = 0

            for idx, match in enumerate(matches, start=1):
                img_alt = match.group(1)
                img_path = match.group(2)
                
                # Convert relative path to absolute path
                if not os.path.isabs(img_path):
                    img_path = os.path.join(os.path.dirname(md_file_path), img_path)

                # Add content before the image (excluding the image reference itself)
                new_content.append(content[last_end:match.start()])
                last_end = match.end()

                if os.path.exists(img_path):
                    try:
                        # Process with selected model - ensure fresh context
                        try:
                            # First ensure no existing chat context
                            ollama.chat(
                                model=self.model_var.get(),
                                messages=[{"role": "system", "content": "RESET"}]
                            )
                        except Exception:
                            # If reset fails, continue anyway
                            pass
                            
                        # Start fresh chat session
                        response = ollama.chat(
                            model=self.model_var.get(),
                            messages=[
                                {"role": "user", "content": BASE_PROMPT, "images": [EXAMPLE_IMAGE]},
                                {"role": "user", "content": "Process the second image. Remember: ONLY output the table.", "images": [img_path]}
                            ]
                        )
                        output = response['message']['content'].strip()
                        
                        # Only add output if it's not "No table found"
                        if "No table found" not in output:
                            new_content.append(f"\n\n{output}\n\n")
                        
                    except Exception as e:
                        new_content.append(f"\n\nError processing image: {e}\n\n")
                else:
                    new_content.append(f"\n\nError: Image file not found: {img_path}\n\n")
                
                # Update total progress and status
                self.root.after(0, lambda: self.total_progress.configure(value=idx))
                self.root.after(0, lambda: self.progress_label.configure(text=f"Progress: {idx}/{total_images}"))
                self.root.after(0, lambda: self.update_status(f"Processing: {img_path}"))

            # Add remaining content after the last image
            new_content.append(content[last_end:])

            # Write the processed content to the output file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(''.join(new_content))

            self.root.after(0, lambda: messagebox.showinfo(
                "Processing Complete",
                f"Processing complete!\nProcessed markdown saved to:\n{output_file}"
            ))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.process_button.state(["!disabled"]))
            self.root.after(0, lambda: self.progress_label.configure(text="Progress: 0/0"))

    def update_status(self, message):
        self.status_label.config(text=message)


if __name__ == "__main__":
    root = tk.Tk()
    app = MarkdownImageProcessorApp(root)
    root.mainloop()