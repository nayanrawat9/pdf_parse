import os
import base64
import re
from pathlib import Path
from PIL import Image
from io import BytesIO
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.pipeline_options import PdfPipelineOptions, granite_picture_description
from docling.datamodel.base_models import InputFormat
from docling_core.types.doc import ImageRefMode
from docling.datamodel.settings import settings

def create_pipeline_options():
    """Create and configure pipeline options."""
    pipeline_options = PdfPipelineOptions()
    pipeline_options.generate_picture_images = True
    pipeline_options.images_scale = 2
    pipeline_options.do_code_enrichment = True
    pipeline_options.do_formula_enrichment = True
    pipeline_options.picture_description_options = granite_picture_description
    pipeline_options.generate_table_images = True
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_options.accelerator_options = AcceleratorOptions(num_threads=8, device=AcceleratorDevice.CPU)
    return pipeline_options

def save_base64_image(uri_str, output_folder, filename_prefix, index):
    """Extract and save base64 image from URI."""
    try:
        if not uri_str.startswith("data:image/"):
            print(f"{filename_prefix} {index} URI format not supported: {uri_str[:50]}...")
            return None
            
        header, base64_data = uri_str.split(",", 1)
        image_format = header.split("/")[1].split(";")[0]
        image_data = base64.b64decode(base64_data)
        pil_image = Image.open(BytesIO(image_data))
        
        filename = f"{filename_prefix}_{index+1}.{image_format}"
        filepath = os.path.join(output_folder, filename)
        pil_image.save(filepath)
        
        print(f"Saved {filename_prefix}: {filepath}")
        return filename
    except Exception as e:
        print(f"Error processing {filename_prefix} {index}: {e}")
        return None

def extract_and_save_items(items, output_folder, filename_prefix):
    """Extract and save images/tables from document items."""
    filenames = []
    for i, item in enumerate(items):
        if item.image and item.image.uri:
            filename = save_base64_image(str(item.image.uri), output_folder, filename_prefix, i)
            filenames.append(filename)
        else:
            filenames.append(None)
    return filenames

def replace_placeholders(markdown_content, filenames, placeholder, item_name, output_folder):
    """Replace placeholders with actual image references."""
    index = 0
    def replacer(match):
        nonlocal index
        if index < len(filenames) and filenames[index]:
            replacement = f"![{item_name.title()} {index+1}]({output_folder}/{filenames[index]})"
        else:
            replacement = f"<!-- {item_name} not available -->"
        index += 1
        return replacement
    
    return re.sub(placeholder, replacer, markdown_content)

def extract_images_and_modify_markdown(source_path, output_folder="images"):
    """Main function to extract images/tables and modify markdown."""
    os.makedirs(output_folder, exist_ok=True)
    
    # Setup converter
    converter = DocumentConverter(format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=create_pipeline_options())
    })
    
    # Enable profiling and convert
    settings.debug.profile_pipeline_timings = True
    conversion_result = converter.convert(source=source_path, page_range=(1, 1))
    doc = conversion_result.document
    
    print(f"Conversion secs: {conversion_result.timings['pipeline_total'].times}")
    
    # Extract and save images and tables
    image_filenames = extract_and_save_items(doc.pictures, output_folder, "image")
    table_filenames = extract_and_save_items(doc.tables, output_folder, "table")
    
    # Export and modify markdown
    markdown_content = doc.export_to_markdown(image_mode=ImageRefMode.PLACEHOLDER)
    markdown_content = replace_placeholders(markdown_content, image_filenames, r'<!-- image -->', "image", output_folder)
    markdown_content = replace_placeholders(markdown_content, table_filenames, r'<!-- table -->', "table", output_folder)
    
    return markdown_content, image_filenames, table_filenames

# Usage example
if __name__ == "__main__":
    source = r"C:\Users\E40065689\Desktop\pdf_parse\at90can128_rm.pdf_chapters\4__Memories.pdf"
    
    modified_markdown, saved_images, saved_tables = extract_images_and_modify_markdown(source)
    
    with open("output_with_images.md", "w", encoding="utf-8") as f:
        f.write(modified_markdown)
    
    print(f"Extracted {len([img for img in saved_images if img])} images")
    print(f"Extracted {len([tbl for tbl in saved_tables if tbl])} tables")
    print("Modified markdown saved to: output_with_images.md")
    print("Images and tables saved to: images/ folder")