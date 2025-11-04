#!/usr/bin/env python3
"""
Markdown Image Processor CLI - Linux Version
Converts images in markdown files to markdown tables using Ollama vision models.
"""

import os
import re
import sys
import argparse
import ollama
from typing import List, Tuple, Optional


# Available models
MODELS = ["qwen2.5vl:32b", "gemma3:27b-it-fp16","gemma3:27b", "qwen2.5vl:7b", "qwen2.5vl:72b",  "gemma3:4b"]

# Base prompt with one-shot example
BASE_PROMPT = """
The provided image may or may not contain a table.
If it does, please convert it to markdown format text.
Else, just say 'No table found'.

Requirements:
- Preserve the table structure with vertical and horizontal lines.
- Keep all column and row alignments intact.
- Do not skip any columns or rows, even if they are empty.
- Use Markdown pipes (|) and dashes (---).

Example:
The first image will be provided, and I will also provide the expected Markdown output.

Expected output for the first image:
| Bit           | 7     | 6     | 5     | 4     | 3     | 2     | 1     | 0     |       |
| ------------- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
|               | INTF7 | INTF6 | INTF5 | INTF4 | INTF3 | INTF2 | INTF1 | INTF0 | EIFR  |
| Read/Write    | R/W   | R/W   | R/W   | R/W   | R/W   | R/W   | R/W   | R/W   |       |
| Initial Value | 0     | 0     | 0     | 0     | 0     | 0     | 0     | 0     |       |

The second image may or may not contain a table with similar formatting.
Now, extract the table from the second image:
"""


class MarkdownImageProcessorCLI:
    """CLI version of the Markdown Image Processor"""

    def __init__(self, input_file: str, model: str, output_file: Optional[str] = None):
        self.input_file = input_file
        self.model = model
        self.output_file = output_file or self._generate_output_filename()

    def _generate_output_filename(self) -> str:
        """Generate output filename based on input file and model"""
        base, _ = os.path.splitext(self.input_file)
        model_clean = self.model.replace(":", "_").replace(".", "_")
        return f"{base}_{model_clean}_processed.md"

    def _print_progress(self, current: int, total: int, message: str = ""):
        """Print progress to console"""
        percentage = (current / total) * 100 if total > 0 else 0
        bar_length = 40
        filled_length = int(bar_length * current // total) if total > 0 else 0
        bar = '=' * filled_length + ' ' * (bar_length - filled_length)

        sys.stdout.write(f'\r[{bar}] {percentage:.1f}% ({current}/{total}) {message}')
        sys.stdout.flush()

        if current == total:
            print()  # New line when complete

    def _resolve_image_path(self, image_path: str) -> str:
        """Convert relative path to absolute path based on markdown file location"""
        if os.path.isabs(image_path):
            return image_path
        return os.path.join(os.path.dirname(self.input_file), image_path)

    def _find_images_in_markdown(self, content: str) -> List[Tuple[str, str, int, int]]:
        """Find all image references in markdown content"""
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        matches = []

        for match in re.finditer(image_pattern, content):
            img_alt = match.group(1)
            img_path = match.group(2)
            start_pos = match.start()
            end_pos = match.end()
            matches.append((img_alt, img_path, start_pos, end_pos))

        return matches

    def _process_single_image(self, image_path: str) -> str:
        """Process a single image using Ollama vision model"""
        try:
            # Example image path (Linux-compatible relative path)
            example_image = "images_10__External_Interrupts/table_6.png"

            # Create fresh chat session for each image to prevent context contamination
            # Use a unique conversation starter for each image to ensure isolation
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": f"IMAGE_SESSION_{hash(image_path) % 10000}: {BASE_PROMPT.strip()}\n\nProcess this specific image only:",
                        "images": [example_image]
                    },
                    {
                        "role": "user",
                        "content": "Now process this NEW image. Forget any previous context. ONLY output the table from THIS image:",
                        "images": [image_path]
                    }
                ]
            )
            output = response['message']['content'].strip()

            # Only return output if it's not "No table found"
            if "No table found" not in output:
                return f"\n\n{output}\n\n"

            return ""

        except Exception as e:
            return f"\n\nError processing image {image_path}: {e}\n\n"

    def process_markdown(self):
        """Main processing function"""
        try:
            # Validate input file
            if not os.path.isfile(self.input_file):
                print(f"Error: Input file '{self.input_file}' not found.")
                return False

            # Read the markdown file
            print(f"Reading markdown file: {self.input_file}")
            with open(self.input_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find all image references
            image_matches = self._find_images_in_markdown(content)
            total_images = len(image_matches)

            print(f"Found {total_images} image(s) in markdown file")

            if total_images == 0:
                print("No images found in the markdown file.")
                return True

            # Process each image and update the content
            new_content_parts = []
            last_end = 0

            for idx, (img_alt, img_path, match_start, match_end) in enumerate(image_matches, start=1):
                # Convert relative path to absolute path
                resolved_img_path = self._resolve_image_path(img_path)

                # Add content before the image (excluding the image reference itself)
                new_content_parts.append(content[last_end:match_start])
                last_end = match_end

                # Check if image file exists
                if os.path.exists(resolved_img_path):
                    self._print_progress(idx-1, total_images, f"Processing: {img_path}")
                    result = self._process_single_image(resolved_img_path)
                    new_content_parts.append(result)
                else:
                    error_msg = f"\n\nError: Image file not found: {resolved_img_path}\n\n"
                    new_content_parts.append(error_msg)
                    print(f"\nWarning: Image file not found: {resolved_img_path}")

                # Update progress
                self._print_progress(idx, total_images, f"Completed: {img_path}")

            # Add remaining content after the last image
            new_content_parts.append(content[last_end:])

            # Write the processed content to the output file
            final_content = ''.join(new_content_parts)
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(final_content)

            print(f"\n[SUCCESS] Processing complete!")
            print(f"[SUCCESS] Processed markdown saved to: {self.output_file}")
            print(f"[SUCCESS] Successfully processed {total_images} image(s)")

            return True

        except Exception as e:
            print(f"Error processing markdown: {str(e)}")
            return False


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Process images in markdown files and convert them to markdown tables using Ollama vision models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.md
  %(prog)s input.md -m qwen2.5vl:3b -o output.md
  %(prog)s /path/to/input.md --model gemma3:4b --output /path/to/output.md

Available models:
  qwen2.5vl:7b, qwen2.5vl:32b, qwen2.5vl:72b, gemma3:4b, gemma3:27b, gemma3:27b-it-fp16
        """
    )

    parser.add_argument(
        'input_file',
        help='Path to the input markdown file'
    )

    parser.add_argument(
        '-m', '--model',
        choices=MODELS,
        default=MODELS[0],
        help=f'Ollama vision model to use (default: {MODELS[0]})'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: <input_file>_<model>_processed.md)'
    )

    parser.add_argument(
        '-v', '--version',
        action='version',
        version='Markdown Image Processor CLI 1.0.0'
    )

    args = parser.parse_args()

    # Create processor instance
    processor = MarkdownImageProcessorCLI(
        input_file=args.input_file,
        model=args.model,
        output_file=args.output
    )

    # Process the markdown file
    success = processor.process_markdown()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()