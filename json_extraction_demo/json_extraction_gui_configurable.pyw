#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configurable GUI for extracting hardware peripheral information from markdown documentation.
Supports multiple schema options and custom prompts.
Supports Gemini, Ollama, and OpenRouter LLM providers.
"""

import asyncio
import inspect
import json
import os
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from queue import Queue

import instructor

# Import schema configurations
from extraction_schemas import get_schema_option, get_available_options

# Add proxy settings for non-Windows platforms
if sys.platform != "win32":
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    if "http_proxy" in os.environ:
        del os.environ["http_proxy"]
    if "https_proxy" in os.environ:
        del os.environ["https_proxy"]

# Conditional imports based on provider
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import openai
    OPENROUTER_AVAILABLE = True
except ImportError:
    OPENROUTER_AVAILABLE = False


# ============================================================================
# EXTRACTION FUNCTIONS
# ============================================================================

async def extract_with_gemini(api_key: str, model: str, text: str, prompt_text: str, schema_class):
    """Extract using Gemini API."""
    genai.configure(api_key=api_key)
    
    model_mapping = {
        "gemini-2.5-pro": "google/gemini-2.5-pro",
        "gemini-2.5-flash": "google/gemini-2.5-flash"
    }
    api_model = model_mapping.get(model, f"google/{model}")
    
    client = instructor.from_provider(
        model=api_model,
        mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS,
        api_key=api_key
    )

    system_prompt = prompt_text
    user_prompt = f"Extract complete peripheral information from this microcontroller reference manual chapter.\n\nDocumentation:\n{text}"

    try:
        messages = [
            {"role": "user", "content": system_prompt + "\n\n" + user_prompt},
        ]

        result = client.chat.completions.create(
            response_model=schema_class,
            messages=messages,
            max_retries=2,
        )

        if inspect.iscoroutine(result):
            response = await result
        else:
            response = result

        return response, f"EXTRACTION SUCCESSFUL: {model}"

    except Exception as e:
        return None, f"ERROR during extraction with {model}: {e}"

async def extract_with_ollama(provider: str, text: str, prompt_text: str, schema_class):
    """Extract using Ollama provider."""
    client = instructor.from_provider(f"ollama/{provider}", mode=instructor.Mode.JSON)

    system_prompt = prompt_text
    user_prompt = f"Extract complete peripheral information from this microcontroller reference manual chapter.\n\nDocumentation:\n{text}"

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = client.chat.completions.create(
            response_model=schema_class,
            messages=messages,
            max_retries=2,
        )

        if inspect.iscoroutine(result):
            response = await result
        else:
            response = result

        return response, f"EXTRACTION SUCCESSFUL: {provider}"

    except Exception as e:
        return None, f"ERROR during extraction with {provider}: {e}"

async def extract_with_openrouter(model: str, text: str, prompt_text: str, api_key: str, schema_class):
    """Extract using OpenRouter API."""
    client = instructor.from_openai(
        openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        ),
        mode=instructor.Mode.JSON,
    )

    system_prompt = prompt_text
    user_prompt = f"Extract complete peripheral information from this microcontroller reference manual chapter.\n\nDocumentation:\n{text}"

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = await client.chat.completions.create(
            model=model,
            response_model=schema_class,
            messages=messages,
            max_retries=2,
        )

        if inspect.iscoroutine(result):
            response = await result
        else:
            response = result

        return response, f"EXTRACTION SUCCESSFUL: {model}"

    except Exception as e:
        return None, f"ERROR during extraction with {model}: {e}"


# ============================================================================
# GUI APPLICATION
# ============================================================================

class ExtractionGUI:
    """Main GUI application for configurable JSON extraction."""

    def __init__(self, root):
        self.root = root
        self.root.title("JSON Extraction Tool - Configurable Schemas")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)

        self.output_queue = Queue()
        self.is_running = False
        self.extraction_thread = None

        self.setup_ui()
        self.check_queue()
        self.show_initial_status()
    
    def setup_ui(self):
        """Setup the GUI components."""
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # ===== Input File Section =====
        input_frame = ttk.LabelFrame(main_frame, text="Input File", padding="5")
        input_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        input_frame.columnconfigure(1, weight=1)
        
        ttk.Label(input_frame, text="File:").grid(row=0, column=0)
        self.input_file_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.input_file_var, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(input_frame, text="Browse", command=self.browse_input).grid(row=0, column=2)
        
        # ===== Schema Selection Section =====
        schema_frame = ttk.LabelFrame(main_frame, text="Schema Configuration", padding="5")
        schema_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        schema_frame.columnconfigure(1, weight=1)

        ttk.Label(schema_frame, text="Schema:").grid(row=0, column=0, sticky=tk.W)
        self.schema_var = tk.StringVar(value=get_available_options()[0])
        schema_combo = ttk.Combobox(
            schema_frame,
            textvariable=self.schema_var,
            values=get_available_options(),
            state="readonly",
            width=30
        )
        schema_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        schema_combo.bind("<<ComboboxSelected>>", self.on_schema_change)

        # Schema description
        self.schema_desc_label = ttk.Label(schema_frame, text="", foreground="gray")
        self.schema_desc_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(5, 0))
        
        # ===== Provider Section =====
        provider_frame = ttk.LabelFrame(main_frame, text="Provider Configuration", padding="5")
        provider_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        provider_frame.columnconfigure(1, weight=1)
        provider_frame.columnconfigure(3, weight=1)

        ttk.Label(provider_frame, text="Provider:").grid(row=0, column=0, sticky=tk.W)
        self.provider_var = tk.StringVar(value="gemini")
        provider_combo = ttk.Combobox(
            provider_frame,
            textvariable=self.provider_var,
            values=["gemini", "ollama", "openrouter"],
            state="readonly",
            width=15
        )
        provider_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        provider_combo.bind("<<ComboboxSelected>>", self.on_provider_change)

        # API Key / Model
        ttk.Label(provider_frame, text="API Key:").grid(row=0, column=2, sticky=tk.W)
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(
            provider_frame,
            textvariable=self.api_key_var,
            width=30,
            show="*"
        )
        self.api_key_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=5)

        # Model selection dropdown
        self.provider_model_label = ttk.Label(provider_frame, text="Model:")
        self.provider_model_label.grid(row=1, column=0, sticky=tk.W)
        self.provider_model_var = tk.StringVar(value="gemini-2.5-pro")
        
        # Define model lists for each provider
        self.model_lists = {
            "gemini": ["gemini-2.5-pro", "gemini-2.5-flash"],
            "openrouter": [
                "openrouter/sherlock-think-alpha",
                "z-ai/glm-4.5-air:free",
                "qwen/qwen3-coder:free",
                "openrouter/sherlock-dash-alpha"
            ],
            "ollama": [
                "kimi-k2-thinking:cloud",
                "glm-4.6:cloud",
                "kimi-k2:1t-cloud",
                "minimax-m2:cloud",
                "qwen3-coder:480b-cloud",
                "gpt-oss:120b-cloud"
            ]
        }
        
        self.provider_model_combo = ttk.Combobox(
            provider_frame,
            textvariable=self.provider_model_var,
            values=self.model_lists["gemini"],
            width=30
        )
        self.provider_model_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)

        # Test Connection Button
        self.test_btn = ttk.Button(
            provider_frame,
            text="Test Connection",
            command=self.test_connection
        )
        self.test_btn.grid(row=1, column=2, padx=5)

        # Output file
        ttk.Label(provider_frame, text="Output File:").grid(row=2, column=0, sticky=tk.W)
        self.output_file_var = tk.StringVar()
        ttk.Entry(
            provider_frame,
            textvariable=self.output_file_var,
            width=30
        ).grid(row=2, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=(5, 0))
        
        # ===== Prompt Section =====
        prompt_frame = ttk.LabelFrame(main_frame, text="Extraction Prompt (Editable)", padding="5")
        prompt_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        prompt_frame.columnconfigure(0, weight=1)
        
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, height=5, wrap=tk.WORD)
        self.prompt_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        prompt_frame.rowconfigure(0, weight=1)
        
        # ===== Output Display Section =====
        output_frame = ttk.LabelFrame(main_frame, text="Terminal Output", padding="5")
        output_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, wrap=tk.WORD, state=tk.DISABLED)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ===== Control Section =====
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        self.run_btn = ttk.Button(
            control_frame,
            text="Run Extraction",
            command=self.run_extraction
        )
        self.run_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(
            control_frame,
            text="Stop Generation",
            command=self.stop_extraction,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame,
            text="Clear Output",
            command=self.clear_output
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame,
            text="Reset Prompt",
            command=self.reset_prompt
        ).pack(side=tk.LEFT, padx=5)

        # Add trace to update output filename when model changes
        self.provider_model_var.trace_add("write", self.update_output_filename)

        # Initialize schema and provider
        self.on_schema_change()
        self.on_provider_change()

    def show_initial_status(self):
        """Show initial status with default options."""
        self.log("="*80)
        self.log("JSON Extraction Tool - Configurable Schemas")
        self.log("="*80)
        self.log("\nDEFAULT CONFIGURATION:")
        self.log(f"  Schema: {self.schema_var.get()}")
        self.log(f"  Provider: {self.provider_var.get()}")
        self.log(f"  Model: {self.provider_model_var.get()}")
        if self.provider_var.get() == "gemini":
            self.log("  Requires: API Key")
            if self.get_env_variable("GEMINI_API_KEY"):
                self.log("  Status: GEMINI_API_KEY environment variable detected")
        elif self.provider_var.get() == "ollama":
            self.log("  Requires: Local Ollama server running")
        elif self.provider_var.get() == "openrouter":
            self.log("  Requires: API Key")
            if self.get_env_variable("OPENROUTER_API_KEY"):
                self.log("  Status: OPENROUTER_API_KEY environment variable detected")
        self.log("\nREADY: Select input file to begin\n")

    def on_schema_change(self, event=None):
        """Update prompt when schema changes."""
        schema_name = self.schema_var.get()
        schema_config = get_schema_option(schema_name)
        
        # Update prompt text
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", schema_config["prompt"])
        
        # Update description
        self.schema_desc_label.config(text=schema_config["description"])
        
        self.log(f"\nSCHEMA CHANGED: {schema_name}")
        self.log(f"  {schema_config['description']}")

    def on_provider_change(self, event=None):
        """Update UI when provider changes."""
        provider = self.provider_var.get()

        # Update model dropdown values
        self.provider_model_combo['values'] = self.model_lists[provider]

        if provider == "gemini":
            self.provider_model_label.config(text="Model:")
            self.provider_model_var.set("gemini-2.5-pro")
            self.api_key_entry.config(show="*")
            self.log("\nPROVIDER CHANGED: Gemini")
            self.log("  Requires: API Key (enter above)")
            self.log(f"  Default Model: {self.provider_model_var.get()}")
        elif provider == "ollama":
            self.provider_model_label.config(text="Model:")
            self.provider_model_var.set("minimax-m2:cloud")
            self.api_key_entry.config(show="")
            self.log("\nPROVIDER CHANGED: Ollama")
            self.log("  Requires: Local Ollama server running")
            self.log(f"  Default Model: {self.provider_model_var.get()}")
        elif provider == "openrouter":
            self.provider_model_label.config(text="Model:")
            self.provider_model_var.set("openrouter/sherlock-think-alpha")
            self.api_key_entry.config(show="*")
            self.log("\nPROVIDER CHANGED: OpenRouter")
            self.log("  Requires: API Key (enter above)")
            self.log(f"  Default Model: {self.provider_model_var.get()}")

        # Update output filename to match new provider
        self.update_output_filename()
    
    def update_output_filename(self, *args):
        """Update output filename based on current input file, provider, and model."""
        input_file = self.input_file_var.get()
        if input_file:
            input_stem = Path(input_file).stem
            provider = self.provider_var.get()
            
            # Get model/provider name for filename
            model_name = self.provider_model_var.get().strip()
            
            if provider == "gemini":
                model_part = model_name.replace(".", "_")
            elif provider == "ollama":
                model_part = model_name.replace(":", "_").replace("/", "_").replace(" ", "_")
                if not model_part:
                    model_part = "ollama"
            elif provider == "openrouter":
                model_part = model_name.split("/")[-1].replace(":", "_").replace(" ", "_")
                if not model_part:
                    model_part = "openrouter"
            else:
                model_part = provider
            
            output_name = f"{input_stem}_extracted_{model_part}.json"
            self.output_file_var.set(output_name)

    def browse_input(self):
        """Open file browser for input file."""
        filename = filedialog.askopenfilename(
            title="Select Markdown File",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.input_file_var.set(filename)
            self.update_output_filename()
            self.log(f"\nInput file selected: {filename}")
    
    def log(self, message):
        """Add message to output display."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def clear_output(self):
        """Clear output display."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
    
    def reset_prompt(self):
        """Reset prompt to current schema's default."""
        schema_name = self.schema_var.get()
        schema_config = get_schema_option(schema_name)
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert("1.0", schema_config["prompt"])
        self.log("\nPrompt reset to schema default")

    def get_env_variable(self, var_name):
        """Get environment variable, checking registry on Windows if not in os.environ."""
        value = os.environ.get(var_name, "")
        if value:
            return value

        if sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Environment",
                    0,
                    winreg.KEY_READ
                )
                try:
                    value, _ = winreg.QueryValueEx(key, var_name)
                    winreg.CloseKey(key)
                    return value
                except WindowsError:
                    winreg.CloseKey(key)
            except Exception:
                pass

        return ""

    def get_api_key(self, provider):
        """Get API key from input field or environment variable."""
        api_key = self.api_key_var.get().strip()
        if api_key:
            return api_key

        if provider == "gemini":
            env_key = self.get_env_variable("GEMINI_API_KEY")
            if env_key:
                return env_key
        elif provider == "openrouter":
            env_key = self.get_env_variable("OPENROUTER_API_KEY")
            if env_key:
                return env_key

        return ""

    def test_connection(self):
        """Test connection to the selected provider."""
        provider = self.provider_var.get()
        api_key = self.get_api_key(provider)
        provider_model = self.provider_model_var.get()

        self.log("\n" + "="*80)
        self.log("TESTING CONNECTION...")
        self.log("="*80)

        if provider == "gemini":
            if not GEMINI_AVAILABLE:
                self.log("[ERROR] google-generativeai not installed")
                self.log("Install: pip install google-generativeai")
                return
            if not api_key:
                self.log("[ERROR] API Key required for Gemini")
                self.log("[INFO] Set GEMINI_API_KEY environment variable or enter above")
                return
            self.log("[OK] Gemini library available")
            if self.api_key_var.get().strip():
                self.log(f"[OK] API Key provided: {api_key[:8]}... (from input field)")
            else:
                self.log(f"[OK] API Key provided: {api_key[:8]}... (from GEMINI_API_KEY env)")
            self.log("[INFO] Connection will be tested during extraction")

        elif provider == "ollama":
            self.log(f"[INFO] Testing Ollama provider: {provider_model}")
            self.log("[INFO] Checking if Ollama server is accessible...")
            try:
                import requests
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    self.log("[OK] Ollama server is running")
                    models = response.json().get("models", [])
                    model_names = [m.get("name", "") for m in models]
                    if provider_model in model_names:
                        self.log(f"[OK] Model '{provider_model}' is available")
                    else:
                        self.log(f"[WARNING] Model '{provider_model}' not found locally")
                        self.log(f"Available models: {', '.join(model_names[:5])}")
                else:
                    self.log("[ERROR] Ollama server returned error")
            except ImportError:
                self.log("[WARNING] requests library not available for testing")
                self.log("Install: pip install requests")
            except Exception as e:
                self.log(f"[ERROR] Cannot connect to Ollama: {e}")
                self.log("Make sure Ollama is running: ollama serve")

        elif provider == "openrouter":
            if not OPENROUTER_AVAILABLE:
                self.log("[ERROR] openai library not installed")
                self.log("Install: pip install openai")
                return
            if not api_key:
                self.log("[ERROR] API Key required for OpenRouter")
                self.log("[INFO] Set OPENROUTER_API_KEY environment variable or enter above")
                return
            self.log("[OK] OpenAI library available")
            if self.api_key_var.get().strip():
                self.log(f"[OK] API Key provided: {api_key[:8]}... (from input field)")
            else:
                self.log(f"[OK] API Key provided: {api_key[:8]}... (from OPENROUTER_API_KEY env)")
            self.log(f"[OK] Model selected: {provider_model}")
            self.log("[INFO] Connection will be tested during extraction")

        self.log("="*80 + "\n")

    def stop_extraction(self):
        """Stop the running extraction."""
        if self.is_running:
            self.log("\n[USER] Stop requested - extraction will terminate...")
            self.is_running = False
            self.stop_btn.config(state=tk.DISABLED)
    
    def run_extraction(self):
        """Run extraction in a separate thread."""
        if self.is_running:
            messagebox.showwarning("Warning", "Extraction is already running")
            return

        # Validate inputs
        input_file = self.input_file_var.get()
        if not input_file:
            messagebox.showerror("Error", "Please select an input file")
            return

        if not os.path.exists(input_file):
            messagebox.showerror("Error", f"Input file not found: {input_file}")
            return

        provider = self.provider_var.get()
        api_key = self.get_api_key(provider)
        provider_model = self.provider_model_var.get()
        output_file = self.output_file_var.get()
        prompt_text = self.prompt_text.get("1.0", tk.END).strip()
        schema_name = self.schema_var.get()

        if provider == "gemini" and not api_key:
            messagebox.showerror(
                "Error",
                "API Key required for Gemini\n\n"
                "Set GEMINI_API_KEY environment variable or enter in the field above"
            )
            return

        if provider == "openrouter" and not api_key:
            messagebox.showerror(
                "Error",
                "API Key required for OpenRouter\n\n"
                "Set OPENROUTER_API_KEY environment variable or enter in the field above"
            )
            return

        if provider in ["ollama", "openrouter"] and not provider_model:
            messagebox.showerror("Error", "Please specify provider/model")
            return

        self.is_running = True
        self.run_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.clear_output()

        self.log(">>> Starting extraction...")
        self.log(f">>> Status: Initializing {provider.upper()}...")
        if api_key and not self.api_key_var.get().strip():
            env_var = "GEMINI_API_KEY" if provider == "gemini" else "OPENROUTER_API_KEY"
            self.log(f">>> Using API key from {env_var} environment variable")

        self.extraction_thread = threading.Thread(
            target=self._run_extraction_thread,
            args=(input_file, provider, api_key, provider_model, output_file, prompt_text, schema_name)
        )
        self.extraction_thread.daemon = True
        self.extraction_thread.start()

    def _run_extraction_thread(
        self, input_file, provider, api_key, provider_model, output_file, prompt_text, schema_name
    ):
        """Run extraction in thread."""
        import traceback
        result = None
        message = None

        try:
            if not self.is_running:
                return

            self.output_queue.put(">>> Status: Reading input file...")
            with open(input_file, "r", encoding="utf-8") as f:
                text = f.read()
            self.output_queue.put(f">>> Status: File loaded ({len(text)} characters)")

            self.output_queue.put(f"\n{'='*80}")
            self.output_queue.put("RUN OPTIONS")
            self.output_queue.put("-" * 80)
            self.output_queue.put(f"Input:     {input_file}")
            self.output_queue.put(f"Schema:    {schema_name}")
            self.output_queue.put(f"Provider:  {provider}")
            if provider == "ollama":
                self.output_queue.put(f"Model:     {provider_model}")
            elif provider == "openrouter":
                self.output_queue.put(f"Model:     {provider_model}")
            elif provider == "gemini":
                self.output_queue.put(f"Model:     {provider_model}")
            output_display = output_file if output_file else '(auto-generated)'
            self.output_queue.put(f"Output:    {output_display}")
            self.output_queue.put("Prompt:    (custom or default)")
            self.output_queue.put("-" * 80 + "\n")

            if not self.is_running:
                self.output_queue.put(">>> Status: STOPPED by user")
                return

            # Get schema class
            schema_config = get_schema_option(schema_name)
            schema_class = schema_config["schema"]

            # Validate before running extraction
            if provider == "gemini":
                if not GEMINI_AVAILABLE:
                    self.output_queue.put("ERROR: google-generativeai not installed")
                    return
                if not api_key:
                    self.output_queue.put("ERROR: Gemini API key not provided")
                    return
            elif provider == "openrouter":
                if not OPENROUTER_AVAILABLE:
                    self.output_queue.put("ERROR: openai not installed")
                    return
                if not api_key:
                    self.output_queue.put("ERROR: OpenRouter API key not provided")
                    return
            
            self.output_queue.put(">>> Status: Initializing event loop...")
            
            # Set up event loop for Windows
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
            self.output_queue.put(">>> Status: Connecting to API...")
            
            if provider == "gemini":
                self.output_queue.put(f">>> Status: Sending request to {provider_model}...")
                result, message = asyncio.run(
                    extract_with_gemini(api_key, provider_model, text, prompt_text, schema_class)
                )
            elif provider == "ollama":
                self.output_queue.put(f">>> Status: Sending request to Ollama ({provider_model})...")
                result, message = asyncio.run(
                    extract_with_ollama(provider_model, text, prompt_text, schema_class)
                )
            elif provider == "openrouter":
                self.output_queue.put(f">>> Status: Sending request to OpenRouter ({provider_model})...")
                result, message = asyncio.run(
                    extract_with_openrouter(provider_model, text, prompt_text, api_key, schema_class)
                )
            
            self.output_queue.put(">>> Status: Processing response...")
            self.output_queue.put(f"\n{'='*80}")
            self.output_queue.put(message)
            self.output_queue.put(f"{'='*80}\n")
            
            if result:
                self.output_queue.put(">>> Status: Processing extraction results...")
                # Save JSON
                output_path = output_file if output_file else f"{Path(input_file).stem}_extracted_{provider}.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result.model_dump(), f, indent=2)
                
                self.output_queue.put(">>> Status: Saving to file...")
                self.output_queue.put(f"[OK] Saved to: {output_path}")
                self.output_queue.put(f"\n{'='*80}")
                self.output_queue.put("EXTRACTION SUMMARY")
                self.output_queue.put(f"{'='*80}")
                self.output_queue.put(f"Schema: {schema_name}")
                self.output_queue.put(f"Peripheral: {result.peripheral_name}")
                
                # Show schema-specific summary
                result_dict = result.model_dump()
                for key, value in result_dict.items():
                    if key == "peripheral_name" or key == "description":
                        continue
                    if isinstance(value, list):
                        self.output_queue.put(f"{key.replace('_', ' ').title()}: {len(value)}")
                    elif value is not None:
                        self.output_queue.put(f"{key.replace('_', ' ').title()}: Yes")
                
                self.output_queue.put(">>> Status: COMPLETE")
            else:
                self.output_queue.put(">>> Status: FAILED - Extraction returned no result")
        
        except Exception as e:
            self.output_queue.put(f"\n{'='*80}")
            self.output_queue.put(f"EXCEPTION: {type(e).__name__}")
            self.output_queue.put(f"{'='*80}")
            self.output_queue.put(str(e))
            self.output_queue.put("\nFull traceback:")
            self.output_queue.put(traceback.format_exc())
            self.output_queue.put(">>> Status: ERROR")
        
        finally:
            self.output_queue.put("__DONE__")
    
    def check_queue(self):
        """Check for messages in output queue."""
        try:
            while True:
                msg = self.output_queue.get_nowait()
                if msg == "__DONE__":
                    self.is_running = False
                    self.run_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                else:
                    self.log(msg)
        except Exception:
            pass

        # Continue checking queue
        self.root.after(100, self.check_queue)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    gui = ExtractionGUI(root)
    root.mainloop()
