#!/usr/bin/env python3
"""
Tkinter GUI that takes:
  - JSON schema
  - Reference IP_Interface.h
  - Reference Basic.h
  - Reference Basic.cpp

Calls ollama CLI and generates the 3 SystemC files.

Requirements:
  - Python 3.8+
  - ollama installed & accessible
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import tempfile
import os
from pathlib import Path

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

DEFAULT_MODEL = "qwen3-coder:480b-cloud"     # change to your installed model
OLLAMA_CMD = "ollama"        # override if needed

OLLAMA_MODELS = [
    "gemini-3-pro-preview:latest",
    "kimi-k2-thinking:cloud",
    "kimi-k2:1t-cloud",
    "qwen3-vl:235b-cloud",
    "gpt-oss:120b-cloud",
    "minimax-m2:cloud",
    "glm-4.6:cloud",
    "qwen:0.5b",
    "deepseek-v3.1:671b-cloud",
    "qwen3-coder:480b-cloud",
    "gpt-oss:20b-cloud",
]

# ---------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------

def call_ollama(prompt: str, model: str) -> str:
    """Run `ollama run <model>` with prompt via stdin."""
    try:
        cmd = [OLLAMA_CMD, "run", model]
        proc = subprocess.run(
            cmd, input=prompt, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=3000
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip())
        return proc.stdout
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}")


def build_prompt(json_schema, ref_ip, ref_h, ref_cpp) -> str:
    """Build the optimized prompt with all input blocks."""
    system_prompt = """SYSTEM / INSTRUCTION:
You are an expert SystemC/TLM code generator. You will read (A) a JSON schema describing a peripheral and (B) three reference code files that represent the required code style and structure. Using only information from those inputs, generate a complete, production-ready implementation for the peripheral in exactly three files and in the exact order below:

  1) IP_Interface.h
  2) Basic.h
  3) Basic.cpp

REQUIREMENTS & CONSTRAINTS:
- Produce only the three file bodies, in the exact order above.
- Do NOT include any commentary, explanation, or extra text outside the explicit file delimiters specified below.
- Follow the style shown in the reference files.
- Implement register semantics from the JSON schema.
- Implement ports, signals, side effects and reset.
- Think deeply and model all the implementable items as in json; dont leave any items out.
- Output must be wrapped with exact delimiters:

<<<FILE:IP_Interface.h>>>
<content>
<<<END:IP_Interface.h>>>

<<<FILE:Basic.h>>>
<content>
<<<END:Basic.h>>>

<<<FILE:Basic.cpp>>>
<content>
<<<END:Basic.cpp>>>

Now ingest the four inputs below and produce the three files in the required delimiter format and order. Do not output anything else."""

    prompt = "\n\n".join([
        system_prompt,
        "### JSON_SCHEMA_BEGIN",
        json_schema.strip(),
        "### JSON_SCHEMA_END",
        "### REF_IP_INTERFACE_BEGIN",
        ref_ip.strip(),
        "### REF_IP_INTERFACE_END",
        "### REF_BASIC_H_BEGIN",
        ref_h.strip(),
        "### REF_BASIC_H_END",
        "### REF_BASIC_CPP_BEGIN",
        ref_cpp.strip(),
        "### REF_BASIC_CPP_END",
    ])
    return prompt


def parse_output(output: str):
    """Extract the three file bodies using strict delimiters."""
    files = {}
    markers = [
        ("IP_Interface.h", "<<<FILE:IP_Interface.h>>>", "<<<END:IP_Interface.h>>>"),
        ("Basic.h", "<<<FILE:Basic.h>>>", "<<<END:Basic.h>>>"),
        ("Basic.cpp", "<<<FILE:Basic.cpp>>>", "<<<END:Basic.cpp>>>"),
    ]

    for name, start_m, end_m in markers:
        s = output.find(start_m)
        e = output.find(end_m)
        if s == -1 or e == -1 or e < s:
            raise ValueError(f"Missing delimiters for {name}")
        body = output[s + len(start_m):e].strip()
        files[name] = body

    return files


# ---------------------------------------------------
# GUI
# ---------------------------------------------------

class App:
    def __init__(self, root):
        self.root = root
        root.title("SystemC Generator (Ollama / Tkinter)")

        # state
        self.generated = None

        # input selectors
        self.json_path = self.add_file_row("JSON Schema")
        self.ip_path   = self.add_file_row("Reference IP_Interface.h")
        self.h_path    = self.add_file_row("Reference Basic.h")
        self.cpp_path  = self.add_file_row("Reference Basic.cpp")

        # model selection
        tk.Label(root, text="Ollama Model").pack(anchor="w")
        self.model_var = tk.StringVar(value=DEFAULT_MODEL)
        self.model_combo = ttk.Combobox(root, textvariable=self.model_var, 
                                        values=OLLAMA_MODELS, state="readonly")
        self.model_combo.pack(fill="x")
        
        # Autofill paths
        base_dir = Path(__file__).parent
        self.json_path.delete(0, tk.END)
        self.json_path.insert(0, str(base_dir / "21__Analog_to_Digital_Converter___ADC_with_images_processed_gemini_gemini-2_5-pro_SystemC_Code_Generation.json"))
        self.ip_path.delete(0, tk.END)
        self.ip_path.insert(0, str(base_dir / "generic_systemc_model_code" / "interface" / "IP_Interface.h"))
        self.h_path.delete(0, tk.END)
        self.h_path.insert(0, str(base_dir / "generic_systemc_model_code" / "sc_implementation" / "Basic" / "include" / "Basic.h"))
        self.cpp_path.delete(0, tk.END)
        self.cpp_path.insert(0, str(base_dir / "generic_systemc_model_code" / "sc_implementation" / "Basic" / "source" / "Basic.cpp"))

        # buttons
        tk.Button(root, text="Generate", command=self.generate).pack(pady=5)
        tk.Button(root, text="Save Files", command=self.save_files).pack(pady=5)

        # output preview
        tk.Label(root, text="Preview (first ~400 chars each)").pack(anchor="w", pady=(10, 0))

        frame = tk.Frame(root)
        frame.pack(fill="both", expand=True)

        self.output_box = tk.Text(frame, wrap="none", height=20)
        self.output_box.pack(side="left", fill="both", expand=True)

        scroll = tk.Scrollbar(frame, command=self.output_box.yview)
        scroll.pack(side="right", fill="y")
        self.output_box.configure(yscrollcommand=scroll.set)

        # status
        self.status = tk.Label(root, text="", anchor="w")
        self.status.pack(fill="x", pady=(5, 0))

    def add_file_row(self, label):
        row = tk.Frame(self.root)
        row.pack(fill="x")
        tk.Label(row, text=label).pack(side="left")
        entry = tk.Entry(row)
        entry.pack(side="left", fill="x", expand=True)
        def browse():
            path = filedialog.askopenfilename()
            if path:
                entry.delete(0, tk.END)
                entry.insert(0, path)
        tk.Button(row, text="Browse", command=browse).pack(side="right")
        return entry

    def generate(self):
        json_file = self.json_path.get()
        ip_file   = self.ip_path.get()
        h_file    = self.h_path.get()
        cpp_file  = self.cpp_path.get()
        model     = self.model_var.get().strip()

        if not all([json_file, ip_file, h_file, cpp_file]):
            self.set_status("Select all 4 input files.")
            return

        try:
            json_schema = Path(json_file).read_text()
            ref_ip      = Path(ip_file).read_text()
            ref_h       = Path(h_file).read_text()
            ref_cpp     = Path(cpp_file).read_text()
        except Exception as e:
            messagebox.showerror("Error", f"File read error:\n{e}")
            return

        prompt = build_prompt(json_schema, ref_ip, ref_h, ref_cpp)

        self.set_status("Running ollama…")
        try:
            output = call_ollama(prompt, model)
        except Exception as e:
            messagebox.showerror("Ollama Error", str(e))
            self.set_status("Failed.")
            return

        self.set_status("Parsing output…")
        try:
            parsed = parse_output(output)
        except Exception as e:
            messagebox.showerror("Parse Error", str(e))
            self.output_box.delete(1.0, tk.END)
            self.output_box.insert(tk.END, output[:2000])
            self.generated = None
            return

        # store
        self.generated = parsed

        # show preview
        self.output_box.delete(1.0, tk.END)
        for name, body in parsed.items():
            self.output_box.insert(tk.END, f"--- {name} ---\n{body[:400]}\n\n")

        self.set_status("Generation complete.")

    def save_files(self):
        if not self.generated:
            self.set_status("Nothing to save. Generate first.")
            return

        folder = filedialog.askdirectory()
        if not folder:
            return

        try:
            for name, body in self.generated.items():
                p = Path(folder) / name
                p.write_text(body + "\n")
            self.set_status(f"Saved to {folder}")
            messagebox.showinfo("Saved", f"Files saved to:\n{folder}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def set_status(self, msg):
        self.status.config(text=msg)



# ---------------------------------------------------
# MAIN
# ---------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x700")
    app = App(root)
    root.mainloop()
