# json_extraction_gemini_cli.py

import argparse
from pydantic import BaseModel, Field
import instructor
import json
import asyncio
import inspect
from typing import List, Optional
from pathlib import Path
import os
import sys
if sys.platform != 'win32':
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
    if 'http_proxy' in os.environ:
        del os.environ['http_proxy']
    if 'https_proxy' in os.environ:
        del os.environ['https_proxy']

# --- Step 1: Define the Comprehensive Pydantic Schema ---
# This schema is designed to be generic for any peripheral.

class BitField(BaseModel):
    """A single bit or group of bits within a register."""
    name: str = Field(..., description="The mnemonic name of the bit field (e.g., 'EEMWE', 'ADEN').")
    bit_position: str = Field(..., description="The bit number or range (e.g., '7', '3..2', '15..12').")
    access: str = Field(..., description="Read/Write access (e.g., 'R/W', 'R', 'W', 'R/W (once)').")
    initial_value: Optional[str] = Field(None, description="The value after reset (e.g., '0', '1', 'X', 'Undefined').")
    description: str = Field(..., description="A concise summary of the bit field's function.")

class Register(BaseModel):
    """A single memory-mapped register."""
    name: str = Field(..., description="The name of the register (e.g., 'EECR', 'ADMUX').")
    address: Optional[str] = Field(None, description="The memory address or offset, if specified.")
    size_bits: Optional[int] = Field(None, description="The size of the register in bits (e.g., 8, 16, 32).")
    description: str = Field(..., description="A concise summary of the register's purpose.")
    bit_fields: List[BitField] = Field(..., description="A list of all bit fields in this register.")

class Interrupt(BaseModel):
    """An interrupt source associated with the peripheral."""
    name: str = Field(..., description="The name of the interrupt (e.g., 'EEPROM Ready Interrupt', 'ADC Conversion Complete').")
    enabling_bit: Optional[str] = Field(None, description="The bit used to enable this interrupt (e.g., 'EERIE', 'ADIE').")
    flag_bit: Optional[str] = Field(None, description="The bit that is set when the interrupt condition occurs.")
    description: str = Field(..., description="A concise description of what triggers this interrupt.")

class Operation(BaseModel):
    """A specific procedure, operation, or state machine sequence."""
    name: str = Field(..., description="The name of the operation (e.g., 'EEPROM Write Procedure', 'Starting a Conversion').")
    description: str = Field(..., description="A high-level summary of what this operation does.")
    steps: List[str] = Field(..., description="The ordered sequence of steps required to perform the operation.")

class Peripheral(BaseModel):
    """Holds all extracted information for a single hardware peripheral."""
    name: str = Field(..., description="The name of the peripheral (e.g., 'EEPROM Data Memory', 'SRAM Data Memory', 'ADC').")
    summary: str = Field(..., description="A high-level summary of the peripheral's main purpose.")
    registers: List[Register] = Field(default_factory=list, description="A list of all registers for this peripheral.")
    interrupts: List[Interrupt] = Field(default_factory=list, description="A list of all interrupts for this peripheral.")
    operations: List[Operation] = Field(default_factory=list, description="A list of operational procedures or state machines.")

class PeripheralData(BaseModel):
    """The top-level model to hold a list of all peripherals found in the text."""
    peripherals: List[Peripheral]

# --- Step 2: CLI Arguments ---
def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract peripheral data from markdown using instructor and a provider.",
        epilog="Example: py json_extraction_gemini_cli.py --input 4__Memories_with_images.md --provider minimax-m2:cloud"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="4__Memories_with_images.md",
        help="Path to the input markdown file (default: 4__Memories_with_images.md)"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="minimax-m2:cloud",
        help="Provider string for instructor (default: minimax-m2:cloud)"
    )
    return parser.parse_args()

# --- Step 3: Load input markdown ---
def load_text(input_file):
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: '{input_file}' not found. Please make sure it's in the correct path.")
        exit(1)

# --- Step 4: Define the extraction task ---
async def extract_peripheral_data(text, provider, input_file):
    """
    Extracts all peripheral data from the text using a single, comprehensive call.
    """
    # Configure the instructor client
    client = instructor.from_provider(f"ollama/{provider}", mode=instructor.Mode.JSON)
    
    print("Attempting to extract peripheral data... This may take a moment.")

    try:
        # Create a single, comprehensive extraction call
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert at analyzing microcontroller reference manuals. "
                    "Your task is to extract all software-relevant information for creating a SystemC simulation model. "
                    "Focus *only* on registers, bit fields, interrupts, and operational procedures. "
                    "Ignore physical characteristics, timing diagrams, electrical specs, C/Assembly code examples, and JTAG/SPI programming details."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"From the following peripheral documentation, extract all peripherals (like 'EEPROM', 'SRAM', 'Flash'). "
                    "For each peripheral, extract:"
                    "1. All **Registers** (e.g., 'EECR', 'EEARH', 'EEDR')."
                    "2. All **Bit Fields** for each register (incl. name, bit position, R/W access, initial value, and description)."
                    "3. All **Interrupts** (incl. name, enabling bit, and trigger condition)."
                    "4. All **Operations** or **Procedures** described as a sequence of steps (e.g., 'EEPROM Write Procedure')."
                    "\n\n--- DOCUMENTATION TEXT --- \n\n"
                    f"{text}"
                ),
            },
        ]
        
        response = client.chat.completions.create(
            response_model=PeripheralData,
            messages=messages
        )

        if inspect.iscoroutine(response):
            response = await response
        
        print("\n---  Extraction Successful ---")
        data = response.model_dump()
        #print(json.dumps(data, indent=2))

        # Save to file with provider in name
        safe_provider = provider.replace(":", "_").replace("/", "_")
        input_stem = Path(input_file).stem
        output_filename = f"{input_stem}_gemini_extracted_{safe_provider}.json"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"\nSaved extracted data to {output_filename}")

    except Exception as e:
        print(f"\n---  Extraction Failed ---")
        print(f"An error occurred: {e}")

# --- Step 5: Run the extraction ---
if __name__ == "__main__":
    args = parse_args()
    text = load_text(args.input)
    asyncio.run(extract_peripheral_data(text, args.provider, args.input))
