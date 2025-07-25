# pdf_parse

1. run pdf_chapter_splitter - a folder with pdf chapters and ToC intact will be created. works only with pdfs with ToC

2. run process_pdf_toc_sections - input is the pdf folder and output is another folder with txt files section wise using pymupdf

3. (TODO) identify tables with pattern: enter pattern of table; then table names will be found


------------------------------------------------------------------------------------------------------------------------------
Some findings trying to parse tables:

1- Camelot has 4 algorithms: ["stream", "lattice", "network", "hybrid"]
If there are bounding boxes already- lattice works well. for this pdf, all tables have bounding boxes- they can be extracted from "lattice" algorithm.
But the registrr information is there in tabular format wthout bounding boxes. For that, "network" OR "hybrid" works well.

2- Unstructured finds all contents and the bounding boxes- can be used to detect positions of all content for a general pdf

3- Layoutparser uses OCR - tesseract which is able to give bounding boxes but due to its english language training data, it is not able to get the exact text 
like register names, bit names.


so the idea for this pdf is to use combination of camelot and pymupdf to parse register information



PDF parsing findings- https://rtxusers-my.sharepoint.us/personal/e40065689_adxuser_com/Documents/MVP-parsing.pptx?web=1


some libraries:
gfmt - does not work, not updated
docling - promising; extracts all text and some tables and positions of images.; but some tables were detected as images instead of tables. 
Camelot-  "lattice" algorithm works well for merged cells and detects all tables with visible boundaries. However, it may also identify some non-table elements that visually resemble tables due to their box-like appearance in the PDF.
pymupdf - for text extraction, supports chunking for llm
unstructured - paid
layoutparser - bounding boxes of all elements.
nanonets - requires large GPU for local inference
tableextraction - https://github.com/cvlab-stonybrook/TableExtraction
tabula- needs java, not good for merged cells
microsoft/table-transformer-detection - identify and locate tables within an image, drawing bounding boxes around them. It does not perform structure recognition (identifying rows, columns, or cells) or data extraction. Slow.

idea: take text order from docling, take bounding boxes from layout parser, find
correct position of images and replace them in docling.

train for table detection using: https://github.com/ismail-mebsout/Parsing-PDFs-using-YOLOV3


Some sites:
https://www.youtube.com/watch?v=9lBTS5dM27c&t=1056s
https://github.com/daveebbelaar/ai-cookbook/tree/main/knowledge/docling

https://medium.com/nanonets/extract-tables-from-pdf-b8f7d7392b7d
https://github.com/jsvine/pdfplumber/issues/79
https://stackoverflow.com/questions/17591426/how-can-i-extract-tables-as-structured-data-from-pdf-documents
https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/?view=doc-intel-4.0.0
https://github.com/mattlgroff/pdf-to-markdown
https://www.deeplearning.ai/short-courses/preprocessing-unstructured-data-for-llm-applications/
https://github.com/Filimoa/open-parse
https://www.aryn.ai/
https://github.com/VikParuchuri/tabled
https://github.com/datalab-to/marker
https://github.com/datalab-to/pdftext
https://github.com/datalab-to/surya
https://github.com/VikParuchuri/zero_to_gpt
