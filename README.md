# PDF Processing and Parsing Toolkit

This repository contains a collection of Python scripts for processing, parsing, and extracting information from PDF documents. The toolkit is designed to handle complex PDFs, including those with tables, images, and a structured table of contents. It leverages a combination of libraries and models, including `docling`, `camelot`, `pymupdf`, and various language models, to provide a comprehensive solution for PDF data extraction.

## Features

- **PDF Chapter Splitting**: Automatically split a PDF into separate chapter files based on its table of contents.
- **PDF to Markdown Conversion**: Convert PDF files into Markdown format, preserving text and embedding images.
- **Image to Text/Table Conversion**: Utilize Vision Language Models (VLMs) to analyze images within the Markdown and convert them into text or Markdown tables.
- **Structured JSON Extraction**: Extract hardware peripheral specifications from documentation into structured JSON using configurable Pydantic schemas and LLMs (Gemini, Ollama, OpenRouter).
- **JSON to SystemC Code Generation**: Generate production-ready SystemC/TLM implementation code from structured JSON using LLMs via Ollama, with reference-based style matching.
- **SystemC Code Conversion**: Bidirectional conversion between generic/clean SystemC code and proprietary DESYRE framework format using configurable rule-based transformations.
- **Text and Table Extraction**: Advanced tools for extracting text and tables from PDFs, with support for different table structures.
- **GUI and CLI Interfaces**: Many scripts offer both graphical and command-line interfaces for ease of use.
- **Content Chunking**: Scripts to chunk Markdown content for further processing with language models.

## Installation

To use these scripts, you need to install the required Python libraries. You can install them using pip and the provided `requirements.txt` file:

```bash
pip install -r requirements.txt
```

## Workflow

The recommended workflow for processing a PDF is as follows:

1.  **Split the PDF into Chapters**:
    -   Use either the GUI or the CLI script.
    -   **GUI**: Run `pdf_chapter_splitter_GUI.pyw`.
    -   **CLI**: Run `pdf_chapter_splitter_CLI.py`.
        ```bash
        python pdf_chapter_splitter_CLI.py your_document.pdf -o output_directory
        ```
    -   This will create a folder containing the individual PDF chapters. This works best for PDFs with a table of contents.

2.  **Convert PDF Chapters to Markdown**:
    -   You have two options for this step:
        -   **GUI**: Use the `docling_basic_parse_GUI.pyw` script for a graphical interface.
        -   **CLI**: Use the `docling_basic_parse_cli.py` script for command-line processing.
            ```bash
            # Basic usage
            python docling_basic_parse_cli.py input.pdf

            # Advanced usage with custom options
            python docling_basic_parse_cli.py input.pdf \
                --output-dir custom_output \
                --start-page 1 --end-page 20 \
                --images-scale 3.0 \
                --threads 4 --device CPU \
                --table-images --table-structure \
                --code-enrichment --formula-enrichment

            # View all available options
            python docling_basic_parse_cli.py --help
            ```
    -   Both scripts use `docling` to convert PDF chapters into Markdown files with embedded images.
    -   The CLI version offers additional configuration options for image scaling, table processing, and performance settings.

3.  **Process Images in Markdown**:
    -   You have two options for this step:
        -   **GUI**: Run `markdown_image_processor_gui.pyw`. This provides a graphical interface for processing the images.
        -   **CLI**: Run `markdown_image_processor_cli.py`. This allows you to process the images from the command line.
            -   Example commands:
            ```bash
            python3.13 markdown_image_processor_cli.py 4__Memories_with_images.md --model qwen2.5vl:32b
            python3.13 markdown_image_processor_cli.py 4__Memories_with_images.md --model gemma3:27b-it-fp16
            ```
                The default output file will be named `<input_file>_<model>_processed.md` (e.g., `4__Memories_with_images_qwen2_5vl_32b_processed.md`). Use `--output` to specify a custom output file.
    -   This step uses a Vision Language Model to convert the embedded images into Markdown tables or text.

4.  **Extract Structured Data**:
    -   Use the JSON extraction tools in the `json_extraction_demo/` folder to extract hardware peripheral specifications into structured JSON format.
    -   **GUI**: Run `json_extraction_demo/json_extraction_gui_configurable.pyw` for a graphical interface with schema selection.
    -   **CLI**: Use provider-specific scripts:
        ```bash
        # Using Gemini
        python json_extraction_demo/json_extraction_cli_gemini.py input.md --output output.json

        # Using OpenRouter
        python json_extraction_demo/json_extraction_cli_openrouter.py input.md --output output.json
        ```
    -   Choose from multiple extraction schemas: Detailed Peripheral, Simple Registers, Operations Focused, or SystemC Model Generation.

5.  **Generate SystemC Code from JSON**:
    -   Use the code generation tool to convert the structured JSON into SystemC/TLM implementation files.
    -   **GUI**: Run `json_extraction_demo/ollama_codegen.py`.
    -   The tool takes 4 inputs: the JSON schema + 3 reference SystemC files (`IP_Interface.h`, `Basic.h`, `Basic.cpp`).
    -   Select an Ollama model from the dropdown and click Generate.
    -   The LLM produces 3 SystemC files matching the style of the reference code.

6.  **Convert SystemC Code (Clean ↔ Proprietary)**:
    -   Use the code converter to transform between generic SystemC and proprietary DESYRE framework format.
    -   **GUI**: Run `json_extraction_demo/code_converter/code_converter_gui.py`.
    -   Supports directory mode (all `.h`/`.cpp` files) or individual file selection.
    -   Bidirectional: "Proprietary → Clean" or "Clean → Proprietary".
    -   Conversion rules (includes, macros, TLM sockets, logging) are defined in `CONVERSION_CONFIG.json`.

## Scripts

Here is a brief description of the main scripts in this repository:

-   `pdf_chapter_splitter_GUI.pyw`: A GUI tool to split a PDF into chapters based on its table of contents.
-   `pdf_chapter_splitter_cli.py`: The command-line version of the PDF chapter splitter.
    ```bash
    # Basic usage (output folder is created automatically)
    python pdf_chapter_splitter_cli.py my_document.pdf

    # Specify an output directory
    python pdf_chapter_splitter_cli.py my_document.pdf --output_dir my_chapters
    ```
-   `docling_basic_parse_GUI.pyw`: A GUI tool that uses `docling` to parse a PDF and convert it to a Markdown file with embedded images.
-   `docling_basic_parse_cli.py`: A CLI tool with extensive configuration options for PDF parsing and conversion:
    ```bash
    # Features:
    - PDF to Markdown conversion with image extraction
    - Configurable page range processing
    - Image scaling and classification options
    - Code and formula enrichment
    - Table structure recognition and extraction
    - Multi-threaded processing with CPU/CUDA support
    - Detailed logging and progress reporting
    ```
-   `markdown_image_processor_gui.pyw`: A GUI tool to process images in a Markdown file and convert them to text or tables using a VLM.
-   `markdown_image_processor_cli.py`: The command-line version of the image processor. Default output filename includes the selected model name.
-   `process_pdf_toc_sections_GUI.pyw`: A GUI tool to extract text sections from a PDF based on its table of contents and save them as `.txt` files.
-   `chunking.py`: A script to chunk Markdown files into smaller pieces, which is useful for processing with language models.
-   `table_extractor_gui_improved.py`: A GUI tool to extract tables from images using a language model.
-   `camelot_table_extraction_comparison.py`: A script for comparing different table extraction algorithms in `camelot`.
-   `layoutparser_OCR_demo.py`: A demonstration of using `layoutparser` and OCR for text and layout detection.
-   `relevance_filter.py`: A script for filtering content based on relevance.
-   `unstructured_pdf_element_extractor_GUI.py`: A GUI tool for extracting elements from a PDF using the `unstructured` library.

## JSON Extraction Demo

The `json_extraction_demo/` folder contains tools for extracting structured hardware peripheral specifications from markdown documentation using LLMs and Pydantic schemas.

### Key Features

- **Configurable Schemas**: Choose from multiple extraction schemas optimized for different use cases:
  - **Detailed Peripheral (Full)**: Complete extraction with registers, operations, formulas, state machines, and interrupts
  - **Simple Registers Only**: Focused extraction of register definitions and bit fields
  - **Operations Focused**: Extraction of operational procedures and workflows
  - **SystemC Model Generation**: Optimized for generating SystemC models with Read/Write behaviors, internal state, ports, and timing

- **Multiple LLM Providers**: Support for Gemini, Ollama, and OpenRouter APIs

- **Extensible Architecture**: Easy to add custom schemas by editing `extraction_schemas.py`

### Files

- `extraction_schemas.py`: Central configuration file containing all Pydantic schema definitions and extraction prompts
- `json_extraction_gui_configurable.pyw`: GUI application with schema dropdown selection
- `json_extraction_gui_unified.pyw`: Unified GUI supporting all three LLM providers
- `json_extraction_cli_gemini.py`: CLI tool for Gemini API
- `json_extraction_cli_openrouter.py`: CLI tool for OpenRouter API
- `json_extraction_cli_ollama.py`: CLI tool for local Ollama models
- `ollama_codegen.py`: GUI tool for generating SystemC code from JSON schema using Ollama LLMs
- `code_converter/code_converter_gui.py`: GUI tool for bidirectional conversion between clean and proprietary (DESYRE) SystemC code
- `code_converter/CONVERSION_CONFIG.json`: Configuration file defining all conversion rules

### Usage Examples

GUI with schema selection:
```bash
python json_extraction_demo/json_extraction_gui_configurable.pyw
```

CLI extraction with Gemini:
```bash
python json_extraction_demo/json_extraction_cli_gemini.py input.md \
    --output output.json \
    --model gemini-2.0-flash-exp
```

### Adding Custom Schemas

To add a new extraction schema:

1. Open `json_extraction_demo/extraction_schemas.py`
2. Define your Pydantic model classes
3. Create a prompt string describing the extraction task
4. Add an entry to the `SCHEMA_OPTIONS` dictionary:

```python
SCHEMA_OPTIONS = {
    "Your Schema Name": {
        "schema": YourSchemaClass,
        "prompt": YOUR_PROMPT_STRING,
        "description": "Brief description"
    }
}
```

The new schema will automatically appear in the GUI dropdown and can be used in CLI tools.

## Miscellaneous

This repository also contains various other scripts and notebooks for experimenting with different PDF parsing and table extraction techniques. The `parser_comparison_notebook.py` provides more insights into the findings and comparisons of different libraries.