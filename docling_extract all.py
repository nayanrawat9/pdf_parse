from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.document import PictureItem, TableItem
from pathlib import Path
import os
import re

# Create extracted_images directory if it doesn't exist
output_dir = Path("extracted_images")
output_dir.mkdir(parents=True, exist_ok=True)

source = r"C:\Users\E40065689\Desktop\pdf_parse\at90can128_rm.pdf_chapters\4__Memories.pdf"

# Configure pipeline options to extract images
pipeline_options = PdfPipelineOptions()
pipeline_options.images_scale = 2.0  # Scale for image resolution (2.0 = 144 DPI)
pipeline_options.generate_picture_images = True
pipeline_options.generate_page_images = True

# Create converter with image extraction options
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result = converter.convert(source)
doc_filename = result.input.file.stem

# Create ordered lists to track images in document order
ordered_images = []  # Will store (type, counter, filename) for each image in document order
table_counter = 0
picture_counter = 0

# Iterate through document elements in order and save images
for element, _level in result.document.iterate_items():
    if isinstance(element, TableItem):
        table_counter += 1
        element_image_filename = output_dir / f"{doc_filename}-table-{table_counter}.png"
        try:
            with element_image_filename.open("wb") as fp:
                element.get_image(result.document).save(fp, "PNG")
            print(f"Saved table image: {element_image_filename}")
            ordered_images.append(("table", table_counter, f"{doc_filename}-table-{table_counter}.png"))
        except Exception as e:
            print(f"Error saving table image {table_counter}: {e}")

    if isinstance(element, PictureItem):
        picture_counter += 1
        element_image_filename = output_dir / f"{doc_filename}-picture-{picture_counter}.png"
        try:
            with element_image_filename.open("wb") as fp:
                element.get_image(result.document).save(fp, "PNG")
            print(f"Saved picture image: {element_image_filename}")
            ordered_images.append(("picture", picture_counter, f"{doc_filename}-picture-{picture_counter}.png"))
        except Exception as e:
            print(f"Error saving picture image {picture_counter}: {e}")

# Get markdown content
markdown_content = result.document.export_to_markdown()

# Create a closure to properly map images in order
image_index = 0

def replace_image_placeholder(match):
    global image_index
    if image_index < len(ordered_images):
        image_type, counter, filename = ordered_images[image_index]
        image_index += 1
        return f"![{image_type.title()} {counter}](extracted_images/{filename})"
    else:
        return "<!-- image not found -->"

# Replace image placeholders in order
updated_markdown = re.sub(r'<!-- image -->', replace_image_placeholder, markdown_content)

# Save markdown with image references
md_filename = output_dir / f"{doc_filename}-with-image-refs.md"
with open(md_filename, 'w', encoding='utf-8') as f:
    f.write(updated_markdown)

print(f"\nMarkdown with image references saved to: {md_filename}")
print(f"Total images extracted: {picture_counter} pictures, {table_counter} tables")

# Also save the original markdown for comparison
original_md_filename = output_dir / f"{doc_filename}-original.md"
with open(original_md_filename, 'w', encoding='utf-8') as f:
    f.write(markdown_content)

print(f"Original markdown saved to: {original_md_filename}")

# Count how many image placeholders were found
placeholder_count = len(re.findall(r'<!-- image -->', markdown_content))
print(f"Found {placeholder_count} image placeholders in markdown")
print(f"Extracted {len(ordered_images)} images from PDF")

if placeholder_count != len(ordered_images):
    print(f"⚠️  WARNING: Mismatch between placeholders ({placeholder_count}) and extracted images ({len(ordered_images)})")

# Print the mapping for verification
print(f"\n" + "="*50)
print("IMAGE MAPPING (in document order):")
print("="*50)
for i, (image_type, counter, filename) in enumerate(ordered_images, 1):
    print(f"  Placeholder #{i}: {image_type}-{counter} -> {filename}")

# Print first part of the updated markdown content to console
print("\n" + "="*50)
print("UPDATED MARKDOWN CONTENT (first 2000 chars):")
print("="*50)
print(updated_markdown[:2000])
if len(updated_markdown) > 2000:
    print("\n... (truncated)")  