from docling.document_converter import DocumentConverter


source = r"C:\Users\E40065689\Desktop\pdf_parse\at90can128_rm.pdf_chapters\4__Memories.pdf"
converter = DocumentConverter()
result = converter.convert(source)
print(result.document.export_to_markdown())  