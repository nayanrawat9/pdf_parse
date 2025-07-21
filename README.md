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

Some sites:



