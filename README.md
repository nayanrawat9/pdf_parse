# PDF Processing and Parsing Toolkit

This repository contains a collection of Python scripts for processing, parsing, and extracting information from PDF documents. The toolkit is designed to handle complex PDFs, including those with tables, images, and a structured table of contents. It leverages a combination of libraries and models, including `docling`, `camelot`, `pymupdf`, and various language models, to provide a comprehensive solution for PDF data extraction.

## Features

- **PDF Chapter Splitting**: Automatically split a PDF into separate chapter files based on its table of contents.
- **PDF to Markdown Conversion**: Convert PDF files into Markdown format, preserving text and embedding images.
- **Image to Text/Table Conversion**: Utilize Vision Language Models (VLMs) to analyze images within the Markdown and convert them into text or Markdown tables.
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
    -   Use the `docling_basic_parse_GUI.pyw` script.
    -   This script uses `docling` to convert the PDF chapters into Markdown files with embedded images.

3.  **Process Images in Markdown**:
    -   You have two options for this step:
        -   **GUI**: Run `markdown_image_processor_gui.pyw`. This provides a graphical interface for processing the images.
        -   **CLI**: Run `markdown_image_processor_cli.py`. This allows you to process the images from the command line.
            -   Example commands:
                ```bash
                python markdown_image_processor_cli.py 4__Memories_with_images.md --model qwen2.5vl:32b
                python markdown_image_processor_cli.py 4__Memories_with_images.md --model gemma3:27b-it-fp16
                ```
    -   This step uses a Vision Language Model to convert the embedded images into Markdown tables or text.

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
-   `markdown_image_processor_gui.pyw`: A GUI tool to process images in a Markdown file and convert them to text or tables using a VLM.
-   `markdown_image_processor_cli.py`: The command-line version of the image processor.
-   `process_pdf_toc_sections_GUI.pyw`: A GUI tool to extract text sections from a PDF based on its table of contents and save them as `.txt` files.
-   `chunking.py`: A script to chunk Markdown files into smaller pieces, which is useful for processing with language models.
-   `table_extractor_gui_improved.py`: A GUI tool to extract tables from images using a language model.
-   `camelot_table_extraction_comparison.py`: A script for comparing different table extraction algorithms in `camelot`.
-   `layoutparser_OCR_demo.py`: A demonstration of using `layoutparser` and OCR for text and layout detection.
-   `relevance_filter.py`: A script for filtering content based on relevance.
-   `unstructured_pdf_element_extractor_GUI.py`: A GUI tool for extracting elements from a PDF using the `unstructured` library.

## Miscellaneous

This repository also contains various other scripts and notebooks for experimenting with different PDF parsing and table extraction techniques. The `parser_comparison_notebook.py` provides more insights into the findings and comparisons of different libraries.