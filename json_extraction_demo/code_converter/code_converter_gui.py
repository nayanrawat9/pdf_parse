#!/usr/bin/env python3
"""
Code Converter
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os
from pathlib import Path
import re
import difflib
import glob


class DesyreConverter:
    def __init__(self):
        self.config = None
        self.load_config()

    def load_config(self):
        """Load conversion configuration from JSON"""
        # Try multiple locations for the config file
        possible_paths = [
            "CONVERSION_CONFIG.json",
            os.path.join(os.path.dirname(__file__), "CONVERSION_CONFIG.json")
        ]
        
        config_path = None
        for path in possible_paths:
            if os.path.exists(path):
                config_path = path
                break
        
        if not config_path:
            raise FileNotFoundError(f"Config file not found in: {possible_paths}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {config_path}")

    def convert_file(self, input_path, output_path, direction="clean_to_proprietary"):
        """Convert a single file between clean and proprietary formats
        
        Args:
            input_path: Path to input file
            output_path: Path to output file
            direction: "clean_to_proprietary" or "proprietary_to_clean"
            
        Returns:
            Tuple of (changed: bool, diff_text: str)
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Apply all conversions
        for key, conversion in self.config["conversions"].items():
            content = self._apply_conversion(content, conversion, key, direction)

        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Generate diff
        changed = content != original_content
        diff_text = ""
        if changed:
            original_lines = original_content.splitlines(keepends=True)
            new_lines = content.splitlines(keepends=True)
            diff = difflib.unified_diff(original_lines, new_lines, 
                                       fromfile="Original", tofile="Converted",
                                       lineterm='')
            diff_text = ''.join(diff)
        
        return changed, diff_text

    def _apply_conversion(self, content, conversion, key, direction="clean_to_proprietary"):
        """Apply a single conversion rule
        
        Args:
            content: File content to convert
            conversion: Conversion rule from config
            key: Rule name
            direction: "clean_to_proprietary" or "proprietary_to_clean"
        """
        
        # Skip marker-only entries
        if "markers" in conversion and not any(k in conversion for k in ["generic", "proprietary"]):
            return content

        # Get patterns from config
        generic = conversion.get("generic")
        proprietary = conversion.get("proprietary")
        
        # Special handling for includes - map individual includes
        if key == "includes":
            # Check if using new mapping format
            if "mapping" in conversion:
                mapping = conversion["mapping"]
                
                # Create direction-aware replacement map
                if direction == "proprietary_to_clean":
                    # proprietary -> generic
                    replacements = {item["proprietary"].strip(): item["generic"].strip() for item in mapping}
                else:
                    # generic -> proprietary
                    replacements = {item["generic"].strip(): item["proprietary"].strip() for item in mapping}
                
                # Replace each include individually
                lines = content.split('\n')
                filtered_lines = []
                for line in lines:
                    stripped = line.strip()
                    if stripped in replacements:
                        # Replace this include with its mapping
                        filtered_lines.append(replacements[stripped])
                    else:
                        # Keep non-mapped includes as-is
                        filtered_lines.append(line)
                
                content = '\n'.join(filtered_lines)
                return content
            
            # Fallback to old list format for backwards compatibility
            lines = content.split('\n')
            
            # Get include lists
            proprietary_list = proprietary if isinstance(proprietary, list) else [proprietary]
            generic_list = generic if isinstance(generic, list) else [generic]
            
            # Determine which includes to keep and which to replace
            if direction == "proprietary_to_clean":
                # Converting FROM proprietary TO clean: remove proprietary, add generic
                includes_to_remove = proprietary_list
                includes_to_add = generic_list
            else:
                # Converting FROM clean TO proprietary: remove generic, add proprietary
                includes_to_remove = generic_list
                includes_to_add = proprietary_list
            
            # Remove old includes - match by exact string
            filtered_lines = []
            removed_indices = set()
            for idx, line in enumerate(lines):
                stripped = line.strip()
                # Skip any line that is one of our includes to remove
                is_old_include = False
                for inc in includes_to_remove:
                    if stripped == inc.strip():
                        is_old_include = True
                        removed_indices.add(idx)
                        break
                if not is_old_include:
                    filtered_lines.append(line)
            
            # Find pragma once (using line count from original, not filtered)
            pragma_idx = -1
            for idx, line in enumerate(lines):
                if '#pragma once' in line:
                    pragma_idx = idx
                    break
            
            # Recalculate pragma position in filtered list
            if pragma_idx >= 0:
                pragma_count = sum(1 for i in range(pragma_idx + 1) if i not in removed_indices)
                insert_idx = pragma_count
            else:
                insert_idx = 0
            
            # Insert new includes
            for i, inc in enumerate(includes_to_add):
                filtered_lines.insert(insert_idx + i, inc)
            
            content = '\n'.join(filtered_lines)
            return content

        # Single string conversion with markers
        if generic and isinstance(generic, str):
            if proprietary and isinstance(proprietary, str):
                markers = conversion.get("markers")
                if markers:
                    # Extract content between markers
                    start_marker = markers["start"]
                    end_marker = markers["end"]
                    
                    pattern = re.escape(start_marker) + r"(.*?)" + re.escape(end_marker)
                    
                    def replacer(match):
                        inner = match.group(1)
                        # Replace based on direction
                        if direction == "proprietary_to_clean":
                            # Replace proprietary with generic
                            inner = inner.replace(proprietary, generic)
                        else:
                            # Replace generic with proprietary
                            inner = inner.replace(generic, proprietary)
                        return start_marker + inner + end_marker
                    
                    content = re.sub(pattern, replacer, content, flags=re.DOTALL)
                else:
                    # Direct replacement without markers
                    if direction == "proprietary_to_clean":
                        content = content.replace(proprietary, generic)
                    else:
                        content = content.replace(generic, proprietary)

        # List-based conversions (for includes)
        elif generic and isinstance(generic, list):
            markers = conversion.get("markers")
            if markers:
                start_marker = markers["start"]
                end_marker = markers["end"]
                
                pattern = re.escape(start_marker) + r"(.*?)" + re.escape(end_marker)
                
                def replacer(match):
                    inner = match.group(1)
                    # Replace all items in order based on direction
                    if direction == "proprietary_to_clean":
                        # Replace proprietary with generic
                        prop_list = proprietary if isinstance(proprietary, list) else [proprietary]
                        gen_list = generic if isinstance(generic, list) else [generic]
                    else:
                        # Replace generic with proprietary
                        gen_list = generic if isinstance(generic, list) else [generic]
                        prop_list = proprietary if isinstance(proprietary, list) else [proprietary]
                    
                    for gen, prop in zip(gen_list, prop_list):
                        if direction == "proprietary_to_clean":
                            inner = inner.replace(prop, gen)
                        else:
                            inner = inner.replace(gen, prop)
                    return start_marker + inner + end_marker
                
                content = re.sub(pattern, replacer, content, flags=re.DOTALL)

        return content


class ConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Code Converter")
        self.root.state('zoomed')  # Fullscreen on Windows
        self.root.resizable(True, True)
        
        self.converter = DesyreConverter()
        self.input_mode = tk.StringVar(value="directory")  # "directory" or "files"
        self.input_directory = None
        self.file_paths = {
            "IP_Interface.h": None,
            "Basic.h": None,
            "Basic.cpp": None
        }
        self.output_dir = None
        
        # Load defaults from config
        self.load_defaults()
        self.setup_ui()
    
    def load_defaults(self):
        """Load default file paths and output directory from config"""
        try:
            # Find the config file
            config_paths = [
                "CONVERSION_CONFIG.json",
                os.path.join(os.path.dirname(__file__), "CONVERSION_CONFIG.json")
            ]
            config_file = None
            for path in config_paths:
                if os.path.exists(path):
                    config_file = os.path.abspath(path)
                    break
            
            if not config_file:
                return
            
            # Get the directory containing the config file (code_converter folder)
            config_dir = os.path.dirname(config_file)
            # Go up one level to json_extraction_demo
            base_dir = os.path.dirname(config_dir)
            
            # Set default input directory to desyre_code
            default_input_dir = os.path.join(base_dir, "desyre_code")
            default_input_dir = os.path.normpath(default_input_dir)
            if os.path.exists(default_input_dir):
                self.input_directory = default_input_dir
                self.input_mode.set("directory")
            
            if "default_files" in self.converter.config:
                default_files = self.converter.config["default_files"]
                for filename, path in default_files.items():
                    if filename in self.file_paths:
                        # Resolve relative paths from base directory
                        if not os.path.isabs(path):
                            full_path = os.path.join(base_dir, path)
                        else:
                            full_path = path
                        # Normalize path separators
                        full_path = os.path.normpath(full_path)
                        if os.path.exists(full_path):
                            self.file_paths[filename] = full_path
                        else:
                            print(f"Warning: Default file not found: {filename} at {full_path}")
            
            # Set default output directory to clean_code
            default_output_dir = os.path.join(base_dir, "clean_code")
            default_output_dir = os.path.normpath(default_output_dir)
            if os.path.exists(default_output_dir):
                self.output_dir = default_output_dir
            
            # Override with config if specified
            if "default_output_folder" in self.converter.config:
                output_path = self.converter.config["default_output_folder"]
                if not os.path.isabs(output_path):
                    full_output_path = os.path.join(base_dir, output_path)
                else:
                    full_output_path = output_path
                # Normalize path separators
                full_output_path = os.path.normpath(full_output_path)
                if os.path.exists(full_output_path):
                    self.output_dir = full_output_path
        except Exception as e:
            print(f"Error loading defaults: {e}")  # Print error for debugging

    def setup_ui(self):
        """Create the GUI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)

        # Title
        title_label = ttk.Label(main_frame,
                               text="SystemC Code Converter: Bidirectional DESYRE ↔ Generic",
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)

        # Input mode selection section
        mode_frame = ttk.LabelFrame(main_frame, text="Input Mode", padding="10")
        mode_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Radiobutton(mode_frame, text="Select Directory (all 3 files)",
                        variable=self.input_mode, value="directory",
                        command=self.on_input_mode_changed).pack(anchor=tk.W, padx=10)
        ttk.Radiobutton(mode_frame, text="Select Individual Files",
                        variable=self.input_mode, value="files",
                        command=self.on_input_mode_changed).pack(anchor=tk.W, padx=10)

        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="Select Files", padding="10")
        file_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        file_frame.columnconfigure(1, weight=1)

        # Directory selection (shown when input_mode is "directory")
        self.dir_frame = ttk.LabelFrame(main_frame, text="Select Directory", padding="10")
        self.dir_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        self.dir_frame.columnconfigure(1, weight=1)

        ttk.Label(self.dir_frame, text="Input Directory:").grid(row=0, column=0, sticky=tk.W, padx=5)
        # Show full directory path
        dir_display = str(self.input_directory) if self.input_directory else "Not selected"
        dir_fg = "black" if self.input_directory else "gray"
        self.input_dir_label = ttk.Label(self.dir_frame, text=dir_display, foreground=dir_fg, wraplength=400)
        self.input_dir_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Button(self.dir_frame, text="Browse",
                  command=self.browse_input_dir).grid(row=0, column=2, sticky=tk.E, padx=5)

        # Individual file selection frame
        self.file_frame = file_frame
        self.file_labels = {}
        row = 0
        for filename in self.file_paths.keys():
            label = ttk.Label(file_frame, text=f"{filename}:")
            label.grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
            
            # Show full path if set
            if self.file_paths[filename]:
                display_text = str(self.file_paths[filename])
                fg_color = "black"
            else:
                display_text = "Not selected"
                fg_color = "gray"
            value_label = ttk.Label(file_frame, text=display_text, foreground=fg_color, wraplength=400)
            value_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
            self.file_labels[filename] = value_label
            
            button = ttk.Button(file_frame, text="Browse", 
                              command=lambda fn=filename: self.browse_file(fn))
            button.grid(row=row, column=2, sticky=tk.E, padx=5, pady=5)
            
            row += 1

        # Output directory section
        output_frame = ttk.LabelFrame(main_frame, text="Output Directory", padding="10")
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        output_frame.columnconfigure(1, weight=1)

        ttk.Label(output_frame, text="Output Path:").grid(row=0, column=0, sticky=tk.W, padx=5)
        # Show full output folder path
        output_display = str(self.output_dir) if self.output_dir else "Not selected"
        output_fg = "black" if self.output_dir else "gray"
        self.output_label = ttk.Label(output_frame, text=output_display, foreground=output_fg, wraplength=400)
        self.output_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Button(output_frame, text="Browse", 
                  command=self.browse_output_dir).grid(row=0, column=2, sticky=tk.E, padx=5)

        # Direction selection
        direction_frame = ttk.LabelFrame(main_frame, text="Conversion Direction", padding="10")
        direction_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        self.direction_var = tk.StringVar(value="proprietary_to_clean")
        ttk.Radiobutton(direction_frame, text="Proprietary → Clean (DESYRE to generic)",
                        variable=self.direction_var, value="proprietary_to_clean").pack(anchor=tk.W, padx=10)
        ttk.Radiobutton(direction_frame, text="Clean → Proprietary (generic to DESYRE)",
                       variable=self.direction_var, value="clean_to_proprietary").pack(anchor=tk.W, padx=10)

        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(1, weight=1)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        self.status_text = tk.Text(progress_frame, height=8, width=80, state=tk.DISABLED)
        self.status_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        scrollbar = ttk.Scrollbar(progress_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S), padx=5)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        # Configure text tags for diff colors
        self.status_text.tag_config("removed", background="#ffcccc")
        self.status_text.tag_config("added", background="#ccffcc")
        self.status_text.tag_config("header", background="#ccccff")

        # Button section
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        button_frame.columnconfigure(0, weight=1)

        ttk.Button(button_frame, text="Convert", 
                  command=self.convert).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear",
                  command=self.clear).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit",
                  command=self.root.quit).pack(side=tk.RIGHT, padx=5)

        # Apply initial mode visibility
        self.on_input_mode_changed()

    def on_input_mode_changed(self):
        """Handle input mode change between directory and files"""
        mode = self.input_mode.get()
        if mode == "directory":
            self.dir_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
            self.file_frame.grid_remove()
        else:
            self.dir_frame.grid_remove()
            self.file_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

    def browse_input_dir(self):
        """Browse for input directory"""
        path = filedialog.askdirectory(title="Select Input Directory")
        if path:
            self.input_directory = path
            self.input_dir_label.config(text=path, foreground="black")

    def browse_file(self, filename):
        """Browse for a file"""
        path = filedialog.askopenfilename(
            title=f"Select {filename}",
            filetypes=[("Header/Source files", "*.h *.cpp"), ("All files", "*.*")]
        )
        if path:
            self.file_paths[filename] = path
            self.file_labels[filename].config(text=os.path.basename(path), foreground="black")

    def browse_output_dir(self):
        """Browse for output directory"""
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.output_dir = path
            self.output_label.config(text=path, foreground="black")

    def log_status(self, message):
        """Add message to status text"""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update()
    
    def log_diff(self, diff_text):
        """Add colored diff output to status text"""
        self.status_text.config(state=tk.NORMAL)
        for line in diff_text.split('\n'):
            if line.startswith('-'):
                self.status_text.insert(tk.END, line + "\n", "removed")
            elif line.startswith('+'):
                self.status_text.insert(tk.END, line + "\n", "added")
            elif line.startswith('@@'):
                self.status_text.insert(tk.END, line + "\n", "header")
            else:
                self.status_text.insert(tk.END, line + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update()

    def convert(self):
        """Perform the conversion"""
        mode = self.input_mode.get()
        
        # Validate inputs based on mode
        if mode == "directory":
            if not self.input_directory:
                messagebox.showerror("Error", "Please select input directory")
                return
            # Get all .h and .cpp files from the directory
            files_to_convert = {}
            for ext in ['*.h', '*.cpp']:
                pattern = os.path.join(self.input_directory, ext)
                for filepath in glob.glob(pattern):
                    filename = os.path.basename(filepath)
                    files_to_convert[filename] = filepath
            if not files_to_convert:
                messagebox.showerror("Error", "No .h or .cpp files found in directory")
                return
        else:
            # Individual files mode
            missing = [fn for fn, path in self.file_paths.items() if not path]
            if missing:
                messagebox.showerror("Error", f"Missing files: {', '.join(missing)}")
                return
            files_to_convert = self.file_paths

        if not self.output_dir:
            messagebox.showerror("Error", "Please select output directory")
            return

        # Clear status
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)

        try:
            direction = self.direction_var.get()
            direction_str = "Clean → Proprietary" if direction == "clean_to_proprietary" else "Proprietary → Clean"
            self.log_status(f"Starting conversion: {direction_str}\n")

            total_files = len(files_to_convert)
            for idx, (filename, input_path) in enumerate(files_to_convert.items()):
                self.log_status(f"\n[{idx+1}/{total_files}] Converting {filename}...")

                output_path = os.path.join(self.output_dir, filename)

                try:
                    changed, diff_text = self.converter.convert_file(input_path, output_path, direction)
                    status = "✓ Converted" if changed else "✓ No changes needed"
                    self.log_status(f"  {status}")
                    self.log_status(f"  Output: {output_path}")
                    
                    if changed and diff_text:
                        self.log_status("\n--- Code Diff ---")
                        self.log_diff(diff_text)
                        self.log_status("--- End Diff ---\n")
                except Exception as e:
                    self.log_status(f"  ✗ ERROR: {str(e)}")
                    raise

                progress = ((idx + 1) / total_files) * 100
                self.progress_var.set(progress)

            self.log_status("\n" + "="*60)
            self.log_status("Conversion completed successfully!")
            self.log_status(f"Direction: {direction_str}")
            self.log_status(f"Files saved to: {self.output_dir}")
            messagebox.showinfo("Success", "Conversion completed successfully!")

        except Exception as e:
            self.log_status(f"\nERROR: {str(e)}")
            messagebox.showerror("Conversion Error", f"Failed to convert: {str(e)}")

    def clear(self):
        """Clear all selections"""
        self.file_paths = {fn: None for fn in self.file_paths.keys()}
        for label in self.file_labels.values():
            label.config(text="Not selected", foreground="gray")
        self.output_dir = None
        self.output_label.config(text="Not selected", foreground="gray")
        self.progress_var.set(0)
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = ConverterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
