#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A consolidated CLI for extracting hardware peripheral information from markdown documentation.
"""

import argparse
import asyncio
import inspect
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

import instructor
from pydantic import BaseModel, Field

# Add proxy settings for non-Windows platforms
if sys.platform != "win32":
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    if "http_proxy" in os.environ:
        del os.environ["http_proxy"]
    if "https_proxy" in os.environ:
        del os.environ["https_proxy"]

# ============================================================================
# PYDANTIC SCHEMAS FOR PERIPHERAL EXTRACTION
# ============================================================================

class BitField(BaseModel):
    """A single bit or group of bits within a register."""
    name: str = Field(..., description="The mnemonic name of the bit field (e.g., 'EEMWE', 'ADEN').")
    bit_position: str = Field(..., description="The bit number or range (e.g., '7', '3..2', '15..12').")
    access_type: str = Field(..., description="Read/Write access (e.g., 'R/W', 'R', 'W', 'R/W (once)').")
    reset_value: str = Field(..., description="The value after reset (e.g., '0', '1', 'X', 'Undefined').")
    description: str = Field(..., description="A concise summary of the bit field's function.")
    special_behavior: Optional[str] = Field(None, description="Any special behavior, such as 'self-clearing' or 'write-once'.")

class Register(BaseModel):
    """A single memory-mapped register."""
    name: str = Field(..., description="The name of the register (e.g., 'EECR', 'ADMUX').")
    address: Optional[str] = Field(None, description="The memory address or offset, if specified (e.g., '0x1C', '0x003F').")
    size_bits: int = Field(..., description="The size of the register in bits (e.g., 8, 16, 32).")
    reset_value: str = Field(..., description="The value of the entire register after reset (e.g., '0x00', '0b00000000').")
    description: str = Field(..., description="A concise summary of the register's purpose.")
    bit_fields: List[BitField] = Field(..., description="A list of all bit fields in this register.")

class OperationStep(BaseModel):
    """A single step in a sequence of operations."""
    step_number: int = Field(..., description="The sequential step number (e.g., 1, 2, 3).")
    description: str = Field(..., description="The description of the action to be taken in this step.")
    pseudo_code: Optional[str] = Field(None, description="An optional pseudo-code representation of the step.")
    registers_accessed: List[str] = Field(default_factory=list, description="A list of registers accessed in this step.")

class Operation(BaseModel):
    """A specific procedure, operation, or state machine sequence."""
    name: str = Field(..., description="The name of the operation (e.g., 'EEPROM Write Procedure', 'Starting a Conversion').")
    description: str = Field(..., description="A high-level summary of what this operation does.")
    steps: List[OperationStep] = Field(..., description="The ordered sequence of steps required to perform the operation.")
    preconditions: List[str] = Field(default_factory=list, description="Conditions that must be met before starting the operation.")
    postconditions: List[str] = Field(default_factory=list, description="The state of the peripheral after the operation is complete.")
    notes: Optional[str] = Field(None, description="Any additional notes, warnings, or cautions related to the operation.")

class StateTransition(BaseModel):
    """A transition between states in a state machine."""
    from_state: str = Field(..., description="The name of the state from which the transition originates.")
    to_state: str = Field(..., description="The name of the state to which the transition leads.")
    condition: str = Field(..., description="The condition that triggers the transition (e.g., 'ADSC bit is written to one').")
    actions: List[str] = Field(default_factory=list, description="A list of actions performed during the transition.")

class StateMachine(BaseModel):
    """A state machine that governs the behavior of the peripheral."""
    name: str = Field(..., description="The name of the state machine.")
    states: List[str] = Field(..., description="A list of all possible states in the state machine.")
    initial_state: str = Field(..., description="The state of the machine upon reset.")
    transitions: List[StateTransition] = Field(..., description="A list of all possible transitions between states.")
    description: Optional[str] = Field(None, description="A summary of the state machine's purpose.")

class InterruptSource(BaseModel):
    """A source of interrupts for the peripheral."""
    name: str = Field(..., description="The name of the interrupt (e.g., 'EEPROM Ready Interrupt', 'ADC Conversion Complete').")
    enable_bit: Optional[str] = Field(None, description="The bit used to enable this interrupt (e.g., 'EERIE', 'ADIE').")
    flag_bit: Optional[str] = Field(None, description="The bit that is set when the interrupt condition occurs.")
    condition: str = Field(..., description="A concise description of what triggers this interrupt.")
    priority: Optional[int] = Field(None, description="The priority of the interrupt, if specified.")

class Interrupts(BaseModel):
    """The interrupt configuration for the peripheral."""
    sources: List[InterruptSource] = Field(..., description="A list of all interrupt sources for the peripheral.")
    global_enable: Optional[str] = Field(None, description="The mechanism for globally enabling interrupts (e.g., 'the I-bit in SREG').")
    notes: Optional[str] = Field(None, description="Any additional notes on interrupt handling.")

class ConfigParameter(BaseModel):
    """A configurable parameter of the peripheral."""
    name: str = Field(..., description="The name of the configuration parameter.")
    value: Optional[str] = Field(None, description="The default or constant value of the parameter.")
    data_type: str = Field(..., description="The data type of the parameter (e.g., 'int', 'bool', 'double').")
    description: str = Field(..., description="A description of the parameter's purpose.")
    configurable: bool = Field(True, description="Whether the parameter can be configured by the user.")

class PeripheralData(BaseModel):
    """The complete set of extracted data for a hardware peripheral."""
    peripheral_name: str = Field(..., description="The name of the peripheral (e.g., 'EEPROM', 'GPIO', 'ADC').")
    description: str = Field(..., description="A high-level description of the peripheral's functionality.")
    registers: List[Register] = Field(..., description="A list of all registers for this peripheral.")
    operations: List[Operation] = Field(default_factory=list, description="A list of key operations or procedures.")
    state_machine: Optional[StateMachine] = Field(None, description="The state machine for the peripheral, if one exists.")
    interrupts: Optional[Interrupts] = Field(None, description="The interrupt configuration for the peripheral, if applicable.")
    configuration_parameters: List[ConfigParameter] = Field(default_factory=list, description="A list of configuration parameters.")
    dependencies: List[str] = Field(default_factory=list, description="A list of other peripherals or modules this peripheral depends on.")
    timing_constraints: Optional[str] = Field(None, description="A brief summary of any timing constraints that are critical for software.")
    special_notes: Optional[str] = Field(None, description="Any other special notes or important information for software modeling.")

# ============================================================================
# EXTRACTION FUNCTION
# ============================================================================

# Embedded default prompt (previously in default_prompt_detailed.txt)
DEFAULT_PROMPT_DETAILED = """
You are an expert at extracting hardware peripheral specifications from microcontroller reference manuals.

Your task is to extract structured information suitable for creating a SystemC software model.

FOCUS ON:
- Register definitions with bit fields and access types (R/W/R/W)
- Software operation procedures (step-by-step operations)
- State machines if present
- Interrupt sources and control bits
- Configuration parameters

IGNORE:
- Physical/electrical characteristics
- Detailed timing diagrams (unless critical for software behavior)
- Manufacturing/testing information
- Pin descriptions (unless they're control signals)

IMPORTANT GUIDELINES:
1. Extract ALL registers mentioned in the text
2. For each register, extract ALL bit fields with their positions
3. Preserve operation procedures as sequential steps
4. Note interdependencies between registers
5. Identify state machines from operational descriptions
6. Extract interrupt enable/flag bits carefully
7. Use exact names from documentation (preserve case and naming)
8. If information is unclear, extract what you can and note in descriptions
"""

async def extract_peripheral_data(provider: str, mode: instructor.Mode, text: str, prompt_text: str):
    """
    Extracts peripheral data from markdown documentation using the specified provider and prompt.
    """
    client = instructor.from_provider(f"ollama/{provider}", mode=mode)

    system_prompt = prompt_text
    user_prompt = f"Extract complete peripheral information from this microcontroller reference manual chapter.\n\nDocumentation:\n{text}"

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = client.chat.completions.create(
            response_model=PeripheralData,
            messages=messages,
            max_retries=2,
        )

        if inspect.iscoroutine(result):
            response = await result
        else:
            response = result

        print(f"\n{'='*80}")
        print(f"EXTRACTION SUCCESSFUL: {provider} ({mode.value})")
        print(f"{'='*80}\n")

        return response

    except Exception as e:
        print(f"\n{'='*80}")
        print(f"ERROR during extraction with {provider} ({mode.value})")
        print(f"{'='*80}")
        print(f"Error: {e}")
        return None

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def get_output_filename(input_file: str, provider: str) -> str:
    """
    Generates a descriptive output filename based on the input file and provider.
    """
    input_stem = Path(input_file).stem
    safe_provider = provider.replace(":", "_").replace("/", "_")
    return f"{input_stem}_extracted_{safe_provider}.json"

async def main():
    """
    Main function to run the CLI.
    """
    parser = argparse.ArgumentParser(
        description="Extract hardware peripheral data from markdown documentation.",
        epilog="Example: python json_extraction_cli.py --input my_doc.md --provider minimax-m2:cloud"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input markdown file."
    )
    parser.add_argument(
        "--provider",
        default="minimax-m2:cloud",
        help="The LLM provider to use (default: minimax-m2:cloud)."
    )
    parser.add_argument(
        "--output",
        help="Optional path for the output JSON file. If not provided, a name will be generated based on the input file."
    )

    args = parser.parse_args()

    # Print resolved options for this run so the user can see what settings are being used.
    # Note: The detailed prompt is embedded in the script (no external prompt file required).
    print("\nRUN OPTIONS")
    print("-----------")
    print(f"Input:    {args.input}")
    print(f"Provider: {args.provider}")
    print("Prompt:   (embedded detailed prompt)")
    print(f"Output:   {args.output if args.output else '(auto-generated)'}")
    print("")

    # --- Read Input File ---
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.input}'")
        return

    # --- Use Embedded Prompt ---
    prompt_text = DEFAULT_PROMPT_DETAILED


    # --- Run Extraction ---
    mode = instructor.Mode.JSON
    result = await extract_peripheral_data(args.provider, mode, text, prompt_text)

    # --- Save Output ---
    if result:
        output_file = args.output if args.output else get_output_filename(args.input, args.provider)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2)
        print(f"✓ Saved extracted data to {output_file}")

        # --- Print Summary ---
        print(f"\n{'='*80}")
        print("EXTRACTION SUMMARY")
        print(f"{'='*80}")
        print(f"Peripheral: {result.peripheral_name}")
        print(f"Registers: {len(result.registers)}")
        print(f"Operations: {len(result.operations)}")
        print(f"State Machine: {'Yes' if result.state_machine else 'No'}")
        print(f"Interrupts: {'Yes' if result.interrupts else 'No'}")

if __name__ == "__main__":
    asyncio.run(main())
