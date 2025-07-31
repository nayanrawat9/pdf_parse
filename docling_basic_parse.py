import os
import base64
import re
from pathlib import Path
from PIL import Image
from io import BytesIO  
from docling.document_converter import DocumentConverter, PdfFormatOption  
from docling.datamodel.pipeline_options import PdfPipelineOptions, granite_picture_description
from docling.datamodel.base_models import InputFormat  
from docling_core.types.doc import ImageRefMode  
  
def extract_images_and_modify_markdown(source_path, output_folder="images"):  
    # Create output folder if it doesn't exist  
    os.makedirs(output_folder, exist_ok=True)  
      
    # Configure pipeline to generate picture images  
    pipeline_options = PdfPipelineOptions()  
    pipeline_options.generate_picture_images = True  
    pipeline_options.images_scale = 2  
    #pipeline_options.do_picture_classification = True  
    pipeline_options.do_code_enrichment = True 
    pipeline_options.do_formula_enrichment = True
    pipeline_options.picture_description_options = granite_picture_description
    pipeline_options.generate_table_images = True
      
    # Create converter with proper configuration  
    converter = DocumentConverter(format_options={  
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)  
    })  
      
    # Convert the document  
    result = converter.convert(source = source_path, page_range=(7, 8))  
    doc = result.document  
      
    # Extract and save images  
    image_filenames = []  
    for i, picture in enumerate(doc.pictures):  
        if picture.image and picture.image.uri:  
            try:  
                # Convert URI to string if it's an AnyUrl object
                uri_str = str(picture.image.uri)
                
                # Extract base64 data from URI  
                if uri_str.startswith("data:image/"):  
                    # Parse the data URI format: data:image/png;base64,<base64_data>  
                    header, base64_data = uri_str.split(",", 1)  
                    image_format = header.split("/")[1].split(";")[0]  # Extract format (png, jpeg, etc.)  
                      
                    # Decode base64 data  
                    image_data = base64.b64decode(base64_data)  
                      
                    # Create PIL Image  
                    pil_image = Image.open(BytesIO(image_data))  
                      
                    # Generate filename  
                    filename = f"image_{i+1}.{image_format}"  
                    filepath = os.path.join(output_folder, filename)  
                      
                    # Save image  
                    pil_image.save(filepath)  
                    image_filenames.append(filename)  
                    print(f"Saved image: {filepath}")  
                else:
                    print(f"Image {i} URI format not supported: {uri_str[:50]}...")
                    image_filenames.append(None)
                      
            except Exception as e:  
                print(f"Error processing image {i}: {e}")  
                image_filenames.append(None)  
        else:  
            image_filenames.append(None)

    # Extract and save table images
    table_filenames = []
    for i, table in enumerate(doc.tables):
        if table.image and table.image.uri:
            try:
                # Convert URI to string if it's an AnyUrl object
                uri_str = str(table.image.uri)
                
                # Extract base64 data from URI
                if uri_str.startswith("data:image/"):
                    # Parse the data URI format: data:image/png;base64,<base64_data>
                    header, base64_data = uri_str.split(",", 1)
                    image_format = header.split("/")[1].split(";")[0]  # Extract format (png, jpeg, etc.)
                    
                    # Decode base64 data
                    image_data = base64.b64decode(base64_data)
                    
                    # Create PIL Image
                    pil_image = Image.open(BytesIO(image_data))
                    
                    # Generate filename
                    filename = f"table_{i+1}.{image_format}"
                    filepath = os.path.join(output_folder, filename)
                    
                    # Save image
                    pil_image.save(filepath)
                    table_filenames.append(filename)
                    print(f"Saved table: {filepath}")
                else:
                    print(f"Table {i} URI format not supported: {uri_str[:50]}...")
                    table_filenames.append(None)
                    
            except Exception as e:
                print(f"Error processing table {i}: {e}")
                table_filenames.append(None)
        else:
            table_filenames.append(None)  
      
    # Export markdown with placeholders  
    markdown_content = doc.export_to_markdown(image_mode=ImageRefMode.PLACEHOLDER)  
      
    # Replace <!-- image --> placeholders with actual image filenames  
    image_index = 0  
    def replace_image_placeholder(match):  
        nonlocal image_index  
        if image_index < len(image_filenames) and image_filenames[image_index]:  
            replacement = f"![Image {image_index+1}]({output_folder}/{image_filenames[image_index]})"  
            image_index += 1  
            return replacement  
        else:  
            image_index += 1  
            return "<!-- image not available -->"  
      
    # Replace all <!-- image --> occurrences  
    modified_markdown = re.sub(r'<!-- image -->', replace_image_placeholder, markdown_content)
    
    # Replace <!-- table --> placeholders with actual table image filenames
    table_index = 0
    def replace_table_placeholder(match):
        nonlocal table_index
        if table_index < len(table_filenames) and table_filenames[table_index]:
            replacement = f"![Table {table_index+1}]({output_folder}/{table_filenames[table_index]})"
            table_index += 1
            return replacement
        else:
            table_index += 1
            return "<!-- table not available -->"
    
    # Replace all <!-- table --> occurrences
    modified_markdown = re.sub(r'<!-- table -->', replace_table_placeholder, modified_markdown)
      
    return modified_markdown, image_filenames, table_filenames  
  
# Usage example  
if __name__ == "__main__":  
    source = r"C:\Users\E40065689\Desktop\pdf_parse\at90can128_rm.pdf_chapters\4__Memories.pdf"  
    #source = r"C:\Users\E40065689\Desktop\pdf_parse\at90can128_rm.pdf_chapters\21__Analog_to_Digital_Converter___ADC.pdf"
    #source = r"C:\Users\E40065689\Desktop\pdf_parse\at90can128_rm.pdf_chapters\10__External_Interrupts.pdf" 
     
    # Extract images and get modified markdown  
    modified_markdown, saved_images, saved_tables = extract_images_and_modify_markdown(source)  
      
    # Save the modified markdown to a file  
    with open("output_with_images.md", "w", encoding="utf-8") as f:  
        f.write(modified_markdown)  
      
    print(f"Extracted {len([img for img in saved_images if img])} images")
    print(f"Extracted {len([tbl for tbl in saved_tables if tbl])} tables") 
    print("Modified markdown saved to: output_with_images.md")  
    print("Images and tables saved to: images/ folder")