# PDF Processing and Parsing Toolkit - Workflow Documentation

This document provides a comprehensive guide to the PDF processing toolkit, designed for developers who need to understand, use, and extend the PDF extraction pipeline. The toolkit leverages a combination of specialized libraries and language models to transform raw PDF documents into structured, machine-readable formats suitable for further processing with LLMs and downstream applications.

## 1. Introduction

The PDF Processing and Parsing Toolkit is a modular pipeline designed to handle complex PDF documents, particularly those containing technical documentation with tables, images, diagrams, and structured content. The toolkit addresses a common challenge in document processing: PDFs are excellent for visual presentation but poor for data extraction. This toolkit bridges that gap by providing a systematic approach to converting visual PDFs into structured text and data formats.

The architecture follows a sequential pipeline approach where each step builds upon the output of the previous step. This modular design allows developers to enter the pipeline at any stage, use individual components independently, or extend the toolkit with custom implementations. The toolkit is particularly well-suited for processing hardware documentation, technical manuals, papers, and other content-rich PDFs that require careful handling of visual elements like tables, diagrams, and formulas.

The primary motivation behind this toolkit emerged from the need to extract hardware peripheral specifications from documentation and feed them into language models for further processing. Traditional PDF extraction tools often fail to preserve the semantic structure of technical documents, losing important information about table relationships, figure references, and hierarchical content organization. By combining multiple specialized tools with AI-powered vision models, this toolkit achieves significantly better results than any single-tool approach.

## 2. Prerequisites

Before using the toolkit, ensure your development environment meets the following requirements. The toolkit has been tested on Windows systems with Python 3.10+ and requires several dependencies that handle different aspects of PDF processing.

### 2.1 Core Dependencies

The following Python libraries form the foundation of the toolkit. Install them using pip with the provided requirements.txt file:

- **docling**: The primary PDF parsing library that converts PDFs to Markdown while preserving document structure, tables, and embedded images. Docling uses a sophisticated pipeline that combines layout analysis, OCR, and structure recognition to produce high-quality Markdown output.

- **pymupdf** (fitz): A powerful PDF manipulation library used for chapter splitting and page-level operations. It provides low-level access to PDF elements while maintaining good performance for large documents.

- **camelot**: A table extraction library that specializes in identifying and parsing tabular data from PDFs. It offers multiple algorithms (stream and lattice) to handle different table structures.

- **Pydantic**: Used for structured data validation in the JSON extraction phase, ensuring that LLM outputs conform to defined schemas.

- **langchain** and related integrations: Provides the interface layer for interacting with various LLM providers including Gemini, Ollama, and OpenRouter.

### 2.2 LLM and VLM Requirements

Depending on which processing steps you intend to use, you will need access to one or more language models:

- **Vision Language Models (VLMs)**: Required for Step 3 (Image Processing). Tested models include Qwen2.5-VL (32B), Gemma 3 (27B), and other Ollama-compatible VLMs. These models analyze images embedded in Markdown files and generate textual descriptions or table representations.

- **Text-only LLMs**: Required for Step 4 (JSON Extraction). Supported providers include Google Gemini (gemini-2.0-flash-exp), Ollama (local models), and OpenRouter (various providers). These models process extracted text and generate structured JSON output based on Pydantic schemas.

### 2.3 API Keys and Configuration

For cloud-based LLM providers, you will need to configure API access:

- **Gemini**: Obtain an API key from Google AI Studio and set it as an environment variable or configure it in the extraction scripts.

- **OpenRouter**: Create an account at OpenRouter.ai and obtain an API key for accessing models from multiple providers through a unified interface.

- **Ollama**: For local model inference, install Ollama from ollama.com and pull the desired models (e.g., `ollama pull qwen2.5vl:32b`).

## 3. Workflow Overview

The following ASCII diagram illustrates the complete data flow through the processing pipeline. Each box represents a processing step, with arrows showing the direction of data flow and the file formats used at each stage.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PDF PROCESSING PIPELINE                              │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌──────────────┐
     │   INPUT PDF  │
     │  (with TOC)  │
     └──────┬───────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: CHAPTER SPLITTING                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Library: pymupdf (fitz)                                             │    │
│  │ Method: TOC-based page range extraction                            │    │
│  │ Input: Full PDF document                                            │    │
│  │ Output: Individual PDF files per chapter                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
            │
            ▼
     ┌──────────────┐
     │ CHAPTER_PDF  │
     │   FILES      │
     └──────┬───────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: PDF TO MARKDOWN CONVERSION                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Library: docling                                                    │    │
│  │ Methods: Layout analysis, OCR, table structure recognition,        │    │
│  │          formula detection, code block identification               │    │
│  │ Input: Chapter PDF files                                            │    │
│  │ Output: Markdown files with embedded base64 images                  │    │
│  │ Features: Table extraction, image scaling, code/formula enrichment │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
            │
            ▼
     ┌──────────────┐
     │  MARKDOWN    │
     │  + IMAGES    │
     └──────┬───────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: IMAGE PROCESSING WITH VISION LANGUAGE MODELS                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Models: Qwen2.5-VL (32B), Gemma 3 (27B), other Ollama VLMs         │    │
│  │ Method: VLM inference on embedded images                            │    │
│  │ Input: Markdown with base64 image placeholders                      │    │
│  │ Output: Markdown with image descriptions/tables replacing images    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
            │
            ▼
     ┌──────────────┐
     │  PROCESSED   │
     │  MARKDOWN    │
     └──────┬───────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: STRUCTURED JSON EXTRACTION                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Providers: Gemini, Ollama, OpenRouter                               │    │
│  │ Methods: LLM inference with Pydantic schema validation              │    │
│  │ Input: Processed Markdown documentation                             │    │
│  │ Output: JSON files with structured hardware specifications          │    │
│  │ Schemas: Detailed Peripheral, Simple Registers, Operations Focused, │    │
│  │          SystemC Model Generation                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
            │
            ▼
     ┌──────────────┐
     │  STRUCTURED  │
     │    JSON      │
     └──────┬───────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 5: JSON TO SYSTEMC CODE GENERATION                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Tool: ollama_codegen.py (Tkinter GUI)                               │    │
│  │ Method: LLM inference via Ollama CLI with structured prompt         │    │
│  │ Input: JSON schema + 3 reference SystemC files                      │    │
│  │        (IP_Interface.h, Basic.h, Basic.cpp)                         │    │
│  │ Output: 3 generated SystemC files for the target peripheral         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
            │
            ▼
     ┌──────────────┐
     │   GENERIC    │
     │ SYSTEMC CODE │
     └──────┬───────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 6: SYSTEMC CODE CONVERSION (CLEAN ↔ PROPRIETARY)                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Tool: code_converter/code_converter_gui.py (Tkinter GUI)            │    │
│  │ Method: Rule-based text/regex replacement via CONVERSION_CONFIG.json│    │
│  │ Input: Generic SystemC code (IP_Interface.h, Basic.h, Basic.cpp)    │    │
│  │ Output: Proprietary (DESYRE framework) SystemC code, or vice versa │    │
│  │ Conversions: Includes, class macros, TLM sockets, logging, IRQ     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
            │
            ▼
     ┌──────────────┐
     │ PROPRIETARY  │
     │ SYSTEMC CODE │
     └──────────────┘
```

The pipeline is designed to be flexible, allowing you to stop at any stage depending on your requirements. For example, if you only need Markdown conversion, you can stop after Step 2. If you have already processed Markdown files, you can begin at Step 3 or Step 4 directly.

## 4. Step 1: PDF Chapter Splitting

### 4.1 Overview

The first step in the processing pipeline involves splitting a large PDF document into smaller, chapter-level files based on the table of contents. This step is particularly valuable when processing technical manuals, books, or documentation that naturally divides into sections. By splitting the document, subsequent processing steps can operate on smaller, more manageable files, and the logical structure of the document is preserved in the file organization.

The chapter splitting functionality uses pymupdf (fitz), a mature and well-documented PDF library that provides reliable access to PDF internal structures including the table of contents. The TOC extraction capability allows the splitter to identify chapter boundaries accurately, even in PDFs with nested section hierarchies.

### 4.2 Input and Output

**Input Requirements:**
- PDF file with a valid table of contents (Bookmark structure)
- The TOC should use standard PDF bookmark features
- Nested bookmarks are handled by treating each top-level bookmark as a chapter boundary

**Output:**
- Individual PDF files for each chapter
- Files are named based on the chapter title from the TOC
- Output directory structure preserves the logical organization

### 4.3 Processing Method

The splitting process works by reading the PDF's table of contents to identify chapter boundaries. For each entry in the TOC, the script extracts the starting page number and searches for the next chapter's starting page to determine the page range. The script then uses pymupdf to extract only the pages belonging to each chapter and saves them as separate PDF files.

The library handles several edge cases automatically: chapters without explicit ending pages (the next chapter's start is used), missing TOC entries (the entire remaining document is treated as one chapter), and special characters in chapter titles (filename-safe characters are used).

### 4.4 CLI Usage

To split a PDF into chapters using the command line interface:

```bash
# Basic usage - output folder is created automatically
python pdf_chapter_splitter_cli.py my_document.pdf

# Specify a custom output directory
python pdf_chapter_splitter_cli.py my_document.pdf --output_dir my_chapters

# Specify output directory with path
python pdf_chapter_splitter_cli.py input/manual.pdf --output_dir ./processed/chapters
```

The CLI automatically creates the output directory if it doesn't exist and generates filename-safe names for each chapter file based on the TOC entries.

### 4.5 GUI Usage

For users who prefer a graphical interface, the GUI version provides an interactive way to split PDFs:

```bash
# Launch the chapter splitter GUI
python pdf_chapter_splitter_GUI.pyw
```

The GUI interface allows you to:
- Select the input PDF file through a file browser dialog
- Specify or create the output directory
- View the extracted table of contents before splitting
- Monitor the splitting progress in real-time
- Access detailed logs for troubleshooting

![PDF Chapter Splitter GUI](screenshots/pdf_chapter_splitter_gui.png)

## 5. Step 2: PDF to Markdown Conversion

### 5.1 Overview

The second step converts PDF chapter files into Markdown format with embedded images. This is the core transformation step where the visual PDF content becomes machine-readable text while preserving as much semantic structure as possible. The conversion uses Docling, a modern PDF parsing library that combines multiple AI-powered techniques to achieve high-quality output.

Docling represents a significant advancement over traditional PDF text extraction tools. Rather than simply extracting raw text, Docling performs layout analysis to understand the document's visual organization, applies OCR for scanned documents or embedded images, recognizes table structures, detects formulas and code blocks, and produces semantically rich Markdown that preserves headings, lists, tables, and other structural elements.

### 5.2 Input and Output

**Input:**
- PDF files (individual chapters from Step 1 or entire documents)
- Supported formats: PDF, DOCX, HTML, and other formats supported by Docling

**Output:**
- Markdown (.md) files with embedded base64-encoded images
- Image files saved separately with numeric names (image_0.png, image_1.png, etc.)
- The Markdown references images using standard Markdown image syntax
- Optional JSON export with additional metadata

### 5.3 Processing Methods

The Docling pipeline applies several processing techniques in sequence:

**Layout Analysis:** Docling uses computer vision models to understand the document's visual layout, identifying regions of text, images, tables, and other elements. This analysis helps preserve the logical reading order even in complex multi-column layouts.

**Text Extraction:** Text is extracted using a combination of methods depending on the PDF type. For text-based PDFs, direct text extraction is used. For scanned documents or PDFs with embedded images, OCR is applied to convert images of text into machine-readable content.

**Table Recognition:** Tables are identified and parsed using specialized models that recognize table structures including rows, columns, headers, and cell boundaries. The extracted tables are rendered in Markdown table syntax.

**Formula Detection:** Mathematical formulas are detected and converted to appropriate representations. The system can produce both readable text representations and, when enabled, MathML or LaTeX output.

**Code Block Identification:** Sections of text identified as code are wrapped in Markdown code blocks with appropriate language hints when detectable.

**Image Extraction:** Images embedded in the PDF are extracted, scaled according to parameters, and embedded in the Markdown as base64 data URIs or saved as separate files.

### 5.4 CLI Usage

The CLI version offers extensive configuration options for customizing the conversion process:

```bash
# Basic usage - convert a single PDF
python docling_basic_parse_cli.py input.pdf

# Specify custom output directory
python docling_basic_parse_cli.py input.pdf --output-dir custom_output

# Process a page range (useful for large documents)
python docling_basic_parse_cli.py input.pdf --start-page 1 --end-page 20

# Increase image quality with higher scaling
python docling_basic_parse_cli.py input.pdf --images-scale 3.0

# Enable table structure recognition
python docling_basic_parse_cli.py input.pdf --table-structure

# Enable both table images and structure
python docling_basic_parse_cli.py input.pdf --table-images --table-structure

# Enable code and formula enrichment
python docling_basic_parse_cli.py input.pdf --code-enrichment --formula-enrichment

# Multi-threaded processing on CPU
python docling_basic_parse_cli.py input.pdf --threads 4 --device CPU

# View all available options
python docling_basic_parse_cli.py --help
```

### 5.5 GUI Usage

For interactive use, the GUI provides a convenient interface:

```bash
# Launch the Docling GUI
python docling_basic_parse_GUI.pyw
```

The GUI allows you to:
- Select input PDF files through a file browser
- Configure conversion options through checkboxes and input fields
- Set image scale, page range, and processing options
- Monitor conversion progress with real-time updates
- View and export the generated Markdown

![Docling PDF Parser GUI](screenshots/docling_basic_parse_gui.png)

## 6. Step 3: Image Processing with Vision Language Models

### 6.1 Overview

The third step processes the images embedded in Markdown files using Vision Language Models (VLMs). When PDFs are converted to Markdown, images are extracted as visual data but remain images rather than text. For many applications, particularly those involving language models, these images need to be converted to textual descriptions or table representations.

This step uses VLMs to analyze each embedded image and generate appropriate text descriptions. The model interprets the image content and produces Markdown-formatted text that describes what the image shows. For diagrams, flowcharts, and technical illustrations, this often produces more useful text than simple alt-text would provide.

### 6.2 Input and Output

**Input:**
- Markdown files with embedded base64 images
- The images appear in the Markdown as data URIs or as references to separate image files
- Multiple images per file are supported

**Output:**
- Processed Markdown file with image descriptions
- Images are replaced with VLM-generated text descriptions
- The output filename follows the pattern: `<input>_<model>_processed.md`
- Optional custom output filename can be specified

### 6.3 Supported Vision Language Models

The toolkit supports several VLM implementations, with Ollama providing the easiest path to local inference:

**Qwen2.5-VL (32B):** A large vision language model from Alibaba's Qwen series. It offers strong performance on technical document understanding and is well-suited for processing diagrams, tables, and complex illustrations. The 32B parameter version provides a good balance of capability and resource requirements.

**Gemma 3 (27B):** Google's latest Gemma model with vision capabilities. It provides competitive performance on image understanding tasks and integrates well with the Ollama ecosystem.

**Other Ollama VLMs:** The toolkit is designed to work with any Ollama-compatible VLM. Additional models can be used by specifying the model name when running the processor.

### 6.4 CLI Usage

```bash
# Process with Qwen2.5-VL 32B model
python markdown_image_processor_cli.py 4__Memories_with_images.md --model qwen2.5vl:32b

# Process with Gemma 3 27B model
python markdown_image_processor_cli.py 4__Memories_with_images.md --model gemma3:27b-it-fp16

# Specify custom output filename
python markdown_image_processor_cli.py input.md --model qwen2.5vl:32b --output custom_output.md

# Process with a different VLM
python markdown_image_processor_cli.py input.md --model llava:34b

# View help for all options
python markdown_image_processor_cli.py --help
```

### 6.5 GUI Usage

```bash
# Launch the image processor GUI
python markdown_image_processor_gui.pyw
```

The GUI provides:
- File selection for Markdown input
- Model selection from a dropdown of available Ollama models
- Progress visualization during processing
- Preview of before/after results

![Markdown Image Processor GUI](screenshots/markdown_image_processor_gui.png)

## 7. Step 4: Structured JSON Extraction

### 7.1 Overview

The final step extracts structured information from the processed Markdown into JSON format using language models and Pydantic schemas. This step transforms free-form documentation into machine-readable data structures suitable for downstream processing, database storage, or integration with other systems.

The extraction uses a combination of LLM inference and Pydantic validation. The LLM processes the Markdown content and generates JSON output, which is then validated against a Pydantic model. This approach provides both the flexibility of natural language understanding and the rigor of structured data validation.

### 7.2 Input and Output

**Input:**
- Processed Markdown files from Step 3
- The Markdown should contain hardware peripheral documentation
- More detailed documentation produces better extraction results

**Output:**
- JSON files with structured data
- The JSON structure depends on the selected schema
- Files include both extracted data and metadata about the extraction

### 7.3 Supported LLM Providers

**Google Gemini:** Cloud-based model access through Google's AI API. The gemini-2.0-flash-exp model is recommended for its speed and cost-effectiveness. Gemini provides strong performance on structured extraction tasks and integrates well with the Pydantic validation approach.

**Ollama:** Local model inference using Ollama. Supports various open-source models running on local hardware. This option provides privacy (no data leaves your machine) and eliminates API costs.

**OpenRouter:** Unified API access to models from multiple providers including Anthropic, Meta, and others. Useful for comparing results across providers or accessing models not available through other channels.

### 7.4 Extraction Schemas

Four extraction schemas are available, each optimized for different use cases:

**Detailed Peripheral (Full):** This schema extracts comprehensive information about hardware peripherals including register definitions, bit field descriptions, operational procedures, formula representations, state machine specifications, and interrupt handling details. Use this schema when you need complete documentation of a peripheral device.

**Simple Registers Only:** A focused schema that extracts only register definitions and bit field configurations. Use this schema when you need lightweight register documentation without the additional context and operational details.

**Operations Focused:** This schema prioritizes extraction of operational procedures, workflows, and usage patterns. Use it when your primary interest is in understanding how to use the peripheral rather than its complete specification.

**SystemC Model Generation:** Optimized for generating SystemC model descriptions including Read/Write behaviors, internal state representations, port definitions, and timing specifications. Use this schema when feeding data into SystemC modeling workflows.

### 7.5 CLI Usage

**Using Gemini:**

```bash
# Extract with Gemini API
python json_extraction_demo/json_extraction_cli_gemini.py input.md --output output.json

# Specify model explicitly
python json_extraction_demo/json_extraction_cli_gemini.py input.md --output output.json --model gemini-2.0-flash-exp
```

**Using OpenRouter:**

```bash
# Extract with OpenRouter
python json_extraction_demo/json_extraction_cli_openrouter.py input.md --output output.json
```

**Using Ollama:**

```bash
# Extract with local Ollama model
python json_extraction_demo/json_extraction_cli_ollama.py input.md --output output.json --model llama3.2-vision
```

### 7.6 GUI Usage

**Configurable GUI with Schema Selection:**

```bash
# Launch GUI with schema dropdown
python json_extraction_demo/json_extraction_gui_configurable.pyw
```

The GUI allows you to:
- Select the Markdown input file
- Choose an extraction schema from a dropdown menu
- Configure LLM provider settings
- Preview extraction results before saving

![JSON Extraction Configurable GUI](screenshots/json_extraction_gui_configurable.png)

**Unified GUI (All Providers):**

```bash
# Launch unified GUI supporting all providers
python json_extraction_demo/json_extraction_gui_unified.pyw
```

![JSON Extraction Unified GUI](screenshots/json_extraction_gui_unified.png)

## 8. Step 5: JSON to SystemC Code Generation

### 8.1 Overview

The fifth step takes the structured JSON output from Step 4 and generates SystemC/TLM implementation code using an LLM via Ollama. The tool provides a Tkinter GUI that accepts four inputs: the JSON schema describing the peripheral and three reference SystemC files that define the target code style and structure. The LLM uses these inputs to produce a complete, production-ready SystemC implementation for the peripheral.

The generated code consists of exactly three files: `IP_Interface.h` (the interface definition), `Basic.h` (the implementation header), and `Basic.cpp` (the implementation source). The LLM is instructed to follow the style of the reference files and implement all register semantics, ports, signals, side effects, and reset logic described in the JSON schema.

### 8.2 Input and Output

**Input:**
- JSON schema file from Step 4 (using the SystemC Model Generation extraction schema)
- Reference `IP_Interface.h` — defines the expected interface structure
- Reference `Basic.h` — defines the expected header structure
- Reference `Basic.cpp` — defines the expected implementation structure

**Output:**
- Three generated SystemC files: `IP_Interface.h`, `Basic.h`, `Basic.cpp`
- Files use strict delimiters (`<<<FILE:...>>>` / `<<<END:...>>>`) for reliable parsing
- The output follows the style and conventions of the reference files

### 8.3 Supported Models

The tool supports any Ollama-compatible model. Pre-configured models include:

| Model | Description |
|-------|-------------|
| qwen3-coder:480b-cloud | Default model, strong code generation |
| gemini-3-pro-preview:latest | Google Gemini via Ollama |
| kimi-k2-thinking:cloud | Kimi K2 with reasoning |
| deepseek-v3.1:671b-cloud | DeepSeek V3.1 |
| gpt-oss:120b-cloud | GPT-OSS large |

### 8.4 GUI Usage

```bash
# Launch the SystemC Generator GUI
python json_extraction_demo/ollama_codegen.py
```

The GUI allows you to:
- Select the JSON schema and three reference SystemC files via file browsers
- Choose an Ollama model from a dropdown
- Generate the three SystemC files with a single click
- Preview the generated code in the output panel
- Save the generated files to a chosen directory

The tool auto-fills input paths based on the default reference files in `generic_systemc_model_code/`.

## 9. Step 6: SystemC Code Conversion (Clean ↔ Proprietary)

### 9.1 Overview

The sixth step converts the generated generic/clean SystemC code into a proprietary framework format (DESYRE), or vice versa. This is a deterministic, rule-based transformation that does not use an LLM. Instead, it applies text replacements and regex-based substitutions defined in a `CONVERSION_CONFIG.json` configuration file.

This step bridges the gap between the LLM-generated generic SystemC code and a specific proprietary simulation framework. The conversions handle differences in include paths, class declaration macros, TLM socket types, logging macros, port declarations, stub instantiations, IRQ transport implementations, and constructor signatures.

### 9.2 Input and Output

**Input:**
- SystemC source files (`IP_Interface.h`, `Basic.h`, `Basic.cpp`) from Step 5
- Can process individual files or an entire directory of `.h`/`.cpp` files

**Output:**
- Converted source files in the target format
- A colored diff showing all changes made during conversion

### 9.3 Conversion Rules

The conversions are defined in `CONVERSION_CONFIG.json` and include:

| Rule | Generic (Clean) | Proprietary (DESYRE) |
|------|-----------------|----------------------|
| Includes | `#include "header1.h"` | `#include <framework.core.model_builder/DESYRE.h>` |
| Class declaration | `class Basic : public ...` | `class MODEL_HW_PERIPHERAL_SPECIFIC_PERIPHERAL_EXPORT Basic : public ...` |
| Module declaration | `class IP_Interface : public sc_core::sc_module` | `DES_MODULE(IP_Interface)` |
| Constructor | `sc_core::sc_module(nm)` | `DES_MODULE_BASE(nm, configuration)` |
| Logging | `std::cout << ...` | `DES_LOG(info) << ...` |
| TLM sockets | `sc_core::sc_port<...>` | `tlm::tlm_initiator_socket<...>` / `tlm::tlm_target_socket<...>` |
| Stubs | `sc_core::sc_signal<double>` | `moc_io::signal::KnownSignal<double>` |

Some rules use marker comments (e.g., `/* [PROPRIETARY_CLASS_DECL_START] */`) to scope replacements to specific code regions.

### 9.4 GUI Usage

```bash
# Launch the Code Converter GUI
python json_extraction_demo/code_converter/code_converter_gui.py
```

The GUI provides:
- **Directory mode**: Process all `.h`/`.cpp` files in a directory at once
- **Individual files mode**: Select specific files to convert
- **Bidirectional conversion**: Toggle between "Proprietary → Clean" and "Clean → Proprietary"
- **Output directory selection**: Choose where converted files are saved
- **Colored diff view**: Visualize all changes with red (removed) and green (added) highlighting
- **Progress bar**: Track conversion progress across multiple files

### 9.5 Adding Custom Conversion Rules

To add a new conversion rule, edit `json_extraction_demo/code_converter/CONVERSION_CONFIG.json`:

```json
{
  "conversions": {
    "your_rule_name": {
      "generic": "clean version of the code",
      "proprietary": "proprietary version of the code",
      "markers": {
        "start": "/* [YOUR_MARKER_START] */",
        "end": "/* [YOUR_MARKER_END] */"
      }
    }
  }
}
```

If `markers` is set, the replacement is scoped to code between those marker comments. If `markers` is `null`, a global find-and-replace is performed.

## 10. Model Selection Guide

Choosing the right model for each step significantly impacts processing quality and resource requirements. This guide provides recommendations for common scenarios.

### 10.1 Vision Language Model Selection

| Model | Parameters | Strengths | Best For |
|-------|------------|-----------|----------|
| Qwen2.5-VL | 32B | Strong technical document understanding | Diagrams, tables, complex illustrations |
| Gemma 3 | 27B | Balanced performance, good integration | General image description tasks |
| Llava | 34B | Good visual conversation abilities | Natural image descriptions |

**Selection Considerations:**
- **Resource Availability:** Larger models require more GPU memory. Qwen2.5-VL 32B requires approximately 24GB VRAM for optimal performance.
- **Task Complexity:** Simple images work well with any model. Technical diagrams benefit from models with stronger reasoning capabilities.
- **Speed Requirements:** Smaller models process images faster but may miss subtle details.

### 10.2 Text LLM Selection for JSON Extraction

| Provider | Model | Speed | Cost | Best For |
|----------|-------|-------|------|----------|
| Gemini | gemini-2.0-flash-exp | Fast | Low | General extraction, prototyping |
| Ollama | llama3.2-vision | Medium | Free (local) | Privacy-sensitive applications |
| OpenRouter | claude-3.5-sonnet | Medium | Medium | High-accuracy requirements |

## 11. Output Summary

Understanding the outputs of each step helps in designing downstream processing pipelines and troubleshooting issues.

### 11.1 Step 1 Outputs: Chapter PDFs

```
output_directory/
├── Chapter_1_Introduction.pdf
├── Chapter_2_Background.pdf
├── Chapter_3_Methodology.pdf
└── Chapter_4_Results.pdf
```

Each PDF contains only the pages belonging to that chapter, preserving the original quality and embedded resources.

### 11.2 Step 2 Outputs: Markdown with Images

```
output_directory/
├── document.md              # Main Markdown file
├── document_image_0.png     # Extracted images
├── document_image_1.png
└── document_image_2.png
```

The Markdown references images using relative paths:
```markdown
![Image description](document_image_0.png)
```

### 11.3 Step 3 Outputs: Processed Markdown

```
output_directory/
└── document_qwen2_5vl_32b_processed.md
```

Images are replaced with VLM-generated descriptions:
```markdown
<!-- Image: Timing diagram showing signal relationships -->
The timing diagram illustrates the relationship between the clock signal, 
data input, and output enable signals. The setup time (tSU) is the interval 
between the data input stable and the rising edge of the clock...
```

### 11.4 Step 4 Outputs: Structured JSON

```json
{
  "peripheral_name": "ADC",
  "registers": [
    {
      "name": "ADCR",
      "address": "0x40048000",
      "description": "ADC Control Register",
      "fields": [
        {
          "name": "START",
          "bits": "0",
          "description": "Start conversion"
        }
      ]
    }
  ],
  "metadata": {
    "extracted_from": "adc_documentation.md",
    "model": "gemini-2.0-flash-exp",
    "schema": "detailed_peripheral"
  }
}
```

### 11.5 Step 5 Outputs: Generated SystemC Code

```
output_directory/
├── IP_Interface.h    # Interface definition for the peripheral
├── Basic.h           # Implementation header with register maps, ports
└── Basic.cpp         # Implementation source with read/write handlers, reset
```

### 11.6 Step 6 Outputs: Converted SystemC Code

```
output_directory/
├── IP_Interface.h    # Converted to proprietary (DESYRE) or clean format
├── Basic.h           # With framework-specific macros and includes
└── Basic.cpp         # With framework-specific logging and TLM sockets
```

## 12. Quick Reference Commands

This section provides a condensed reference for common operations.

### 12.1 Full Pipeline Execution

```bash
# Step 1: Split PDF into chapters
python pdf_chapter_splitter_cli.py input.pdf --output_dir chapters

# Step 2: Convert all chapters to Markdown
for f in chapters/*.pdf; do
    python docling_basic_parse_cli.py "$f" --output-dir markdown
done

# Step 3: Process images in all Markdown files
for f in markdown/*.md; do
    python markdown_image_processor_cli.py "$f" --model qwen2.5vl:32b
done

# Step 4: Extract JSON from processed Markdown
for f in markdown/*_processed.md; do
    python json_extraction_demo/json_extraction_cli_gemini.py "$f" --output json/$(basename "$f" .md).json
done

# Step 5: Generate SystemC code from JSON (GUI only)
python json_extraction_demo/ollama_codegen.py

# Step 6: Convert generic SystemC to proprietary format (GUI only)
python json_extraction_demo/code_converter/code_converter_gui.py
```

### 12.2 Single File Processing

```bash
# Process one PDF through the entire pipeline
python pdf_chapter_splitter_cli.py manual.pdf --output_dir temp
python docling_basic_parse_cli.py temp/chapter1.pdf --output-dir temp
python markdown_image_processor_cli.py temp/chapter1.md --model qwen2.5vl:32b --output temp/chapter1_processed.md
python json_extraction_demo/json_extraction_cli_gemini.py temp/chapter1_processed.md --output temp/chapter1.json
# Then use ollama_codegen.py GUI to generate SystemC from temp/chapter1.json
# Then use code_converter_gui.py GUI to convert to proprietary format
```

## 13. Conclusion

This toolkit provides a comprehensive solution for extracting structured data from PDF documents. The modular pipeline design allows for flexible usage, from simple Markdown conversion to complete structured data extraction. Developers can use individual steps independently or combine them for end-to-end processing.

For extending the toolkit, refer to the individual script source files for implementation details. The modular architecture makes it straightforward to add new processing steps, integrate additional LLM providers, or implement custom extraction schemas.
