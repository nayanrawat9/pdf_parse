# json_extraction_claude_cli.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import instructor
import json
import asyncio
import inspect
import argparse
import os
import sys
if sys.platform != 'win32':
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
    if 'http_proxy' in os.environ:
        del os.environ['http_proxy']
    if 'https_proxy' in os.environ:
        del os.environ['https_proxy']

# ============================================================================
# PYDANTIC SCHEMAS FOR PERIPHERAL EXTRACTION
# ============================================================================

class BitField(BaseModel):
    """Individual bit or bit range within a register"""
    name: str = Field(description="Bit field name (e.g., EEWE, EERIE)")
    bit_position: str = Field(description="Bit position or range (e.g., '7', '5:3', '7..4')")
    access_type: str = Field(description="Access type: R (read-only), W (write-only), R/W (read-write)")
    reset_value: str = Field(description="Reset/initial value (e.g., '0', '1', 'X' for undefined)")
    description: str = Field(description="Detailed description of bit field functionality")
    special_behavior: Optional[str] = Field(None, description="Special behavior like auto-clear, timing constraints")


class Register(BaseModel):
    """Hardware register definition"""
    name: str = Field(description="Register name (e.g., EECR, EEDR)")
    address: Optional[str] = Field(None, description="Register address or offset (e.g., 0x3F)")
    size_bits: int = Field(description="Register size in bits (typically 8, 16, or 32)")
    reset_value: str = Field(description="Complete reset value (e.g., 0x00, 0xXXXX)")
    description: str = Field(description="Purpose and functionality of the register")
    bit_fields: List[BitField] = Field(default_factory=list, description="Bit fields within register")


class OperationStep(BaseModel):
    """Single step in an operation procedure"""
    step_number: int
    description: str
    pseudo_code: Optional[str] = Field(None, description="Code representation if applicable")
    registers_accessed: List[str] = Field(default_factory=list, description="Registers used in this step")


class Operation(BaseModel):
    """Operation or procedure (e.g., EEPROM write, ADC conversion)"""
    name: str = Field(description="Operation name (e.g., 'EEPROM Write', 'ADC Read')")
    description: str = Field(description="What this operation does")
    steps: List[OperationStep] = Field(default_factory=list, description="Sequential steps")
    preconditions: List[str] = Field(default_factory=list, description="Conditions that must be met before operation")
    postconditions: List[str] = Field(default_factory=list, description="State after operation completes")
    notes: Optional[str] = Field(None, description="Important notes, warnings, or cautions")


class StateTransition(BaseModel):
    """State machine transition"""
    from_state: str
    to_state: str
    condition: str = Field(description="What triggers this transition")
    actions: List[str] = Field(default_factory=list, description="Actions performed during transition")


class StateMachine(BaseModel):
    """State machine definition (if peripheral has one)"""
    name: str = Field(description="State machine name")
    states: List[str] = Field(description="All possible states")
    initial_state: str = Field(description="Starting state")
    transitions: List[StateTransition] = Field(default_factory=list)
    description: Optional[str] = Field(None, description="State machine purpose")


class InterruptSource(BaseModel):
    """Interrupt source information"""
    name: str = Field(description="Interrupt name")
    enable_bit: Optional[str] = Field(None, description="Bit to enable this interrupt")
    flag_bit: Optional[str] = Field(None, description="Bit that indicates interrupt occurred")
    condition: str = Field(description="What triggers this interrupt")
    priority: Optional[int] = Field(None, description="Interrupt priority if specified")


class Interrupts(BaseModel):
    """Interrupt configuration for peripheral"""
    sources: List[InterruptSource] = Field(default_factory=list)
    global_enable: Optional[str] = Field(None, description="Global interrupt enable mechanism")
    notes: Optional[str] = Field(None, description="Additional interrupt handling information")


class ConfigParameter(BaseModel):
    """Configuration parameter or constant"""
    name: str
    value: Optional[str] = Field(None, description="Default or constant value")
    data_type: str = Field(description="Data type (int, double, bool, etc.)")
    description: str
    configurable: bool = Field(True, description="Whether this can be changed by user")


class PeripheralMemoryMap(BaseModel):
    """Memory layout for peripheral"""
    base_address: Optional[str] = Field(None, description="Base address in memory map")
    address_range: Optional[str] = Field(None, description="Address range (e.g., 0x0000-0x03FF)")
    size: Optional[str] = Field(None, description="Total size (e.g., '1K bytes')")


class PeripheralData(BaseModel):
    """Complete peripheral extraction"""
    peripheral_name: str = Field(description="Peripheral name (e.g., 'EEPROM', 'GPIO', 'ADC')")
    description: str = Field(description="High-level description of peripheral functionality")
    memory_map: Optional[PeripheralMemoryMap] = Field(None)

    # Core components
    registers: List[Register] = Field(default_factory=list, description="All registers")
    operations: List[Operation] = Field(default_factory=list, description="Key operations/procedures")

    # Optional components
    state_machine: Optional[StateMachine] = Field(None, description="State machine if applicable")
    interrupts: Optional[Interrupts] = Field(None, description="Interrupt configuration if applicable")
    configuration_parameters: List[ConfigParameter] = Field(default_factory=list, description="Configuration parameters")

    # Additional info
    dependencies: List[str] = Field(default_factory=list, description="Other peripherals/modules this depends on")
    timing_constraints: Optional[str] = Field(None, description="Brief timing notes if critical for software")
    special_notes: Optional[str] = Field(None, description="Important notes for software modeling")


# ============================================================================
# EXTRACTION CONFIGURATION
# ============================================================================

PROVIDERS = [
    "minimax-m2:cloud",
    "qwen3-coder:480b-cloud",  # Good for technical documentation
    "deepseek-v3.1:671b-cloud",  # Strong reasoning
    # Add your preferred 60B model here
]

MODES = [
    instructor.Mode.JSON,
]


# ============================================================================
# EXTRACTION FUNCTION
# ============================================================================

async def extract_peripheral_data(provider: str, mode: instructor.Mode, text: str, peripheral_hint: str = ""):
    """
    Extract peripheral data from markdown documentation.

    Args:
        provider: LLM provider string
        mode: Instructor mode
        text: Peripheral documentation text
        peripheral_hint: Optional hint about peripheral type (e.g., "EEPROM", "GPIO")
    """
    client = instructor.from_provider(f"ollama/{provider}", mode=mode)

    # Construct detailed system prompt
    system_prompt = """You are an expert at extracting hardware peripheral specifications from microcontroller reference manuals.

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

    user_prompt = f"""Extract complete peripheral information from this microcontroller reference manual chapter.
{f'Peripheral type: {peripheral_hint}' if peripheral_hint else ''}

Documentation:
{text}

Extract ALL registers, bit fields, operations, state machines, and interrupt information.
Be thorough - this data will be used to generate SystemC code."""

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

        # Handle both sync and async results
        if inspect.iscoroutine(result):
            response = await result
        else:
            response = result

        print(f"\n{'='*80}")
        print(f"EXTRACTION RESULT: {provider} ({mode.value})")
        print(f"{'='*80}\n")
        print(json.dumps(response.model_dump(), indent=2))

        return response

    except Exception as e:
        print(f"\n{'='*80}")
        print(f"ERROR: {provider} ({mode.value})")
        print(f"{'='*80}")
        print(f"Error: {e}")
        return None


# ============================================================================
# VALIDATION AND SAVING
# ============================================================================

def validate_extraction(data: PeripheralData) -> List[str]:
    """Validate extracted data and return list of warnings/issues"""
    issues = []

    if not data.registers:
        issues.append("WARNING: No registers extracted")

    for reg in data.registers:
        if not reg.bit_fields:
            issues.append(f"WARNING: Register {reg.name} has no bit fields")

        # Check for common bit field patterns
        total_bits = sum(
            len(bf.bit_position.split(':')) if ':' in bf.bit_position else 1
            for bf in reg.bit_fields
        )
        if total_bits < reg.size_bits / 2:
            issues.append(f"WARNING: Register {reg.name} may have missing bit fields")

    if not data.operations:
        issues.append("WARNING: No operations extracted - check if peripheral has procedures")

    return issues


def save_extraction(data: PeripheralData, output_file: str):
    """Save extracted data to JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data.model_dump(), f, indent=2)
    print(f"\n✓ Saved to {output_file}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(description="Extract peripheral data from markdown documentation using Claude.")
    parser.add_argument("--input", required=True, help="Path to the input markdown file")
    parser.add_argument("--provider", required=True, help="LLM provider string (e.g., minimax-m2:cloud)")

    args = parser.parse_args()

    input_file = args.input
    provider = args.provider

    # Derive input filename without extension
    input_filename = os.path.splitext(os.path.basename(input_file))[0]
    provider_clean = provider.replace(":", "-")
    output_filename = f"{input_filename}_claude__{provider_clean}.json"

    peripheral_hint = ""  # Optional: can be set based on input or made as argument

    print(f"Loading {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()

    print(f"Document size: {len(text)} characters")
    print(f"Estimated tokens: ~{len(text) // 4}")

    # Extract with the specified provider
    mode = MODES[0]

    print(f"\nExtracting with {provider}...")
    result = await extract_peripheral_data(provider, mode, text, peripheral_hint)

    if result:
        # Validate
        issues = validate_extraction(result)
        if issues:
            print("\n VALIDATION WARNINGS:")
            for issue in issues:
                print(f"  - {issue}")

        # Save
        save_extraction(result, output_filename)

        # Print summary
        print(f"\n{'='*80}")
        print("EXTRACTION SUMMARY")
        print(f"{'='*80}")
        print(f"Peripheral: {result.peripheral_name}")
        print(f"Registers: {len(result.registers)}")
        print(f"Operations: {len(result.operations)}")
        print(f"State Machine: {'Yes' if result.state_machine else 'No'}")
        print(f"Interrupts: {'Yes' if result.interrupts else 'No'}")
        print(f"Config Parameters: {len(result.configuration_parameters)}")


if __name__ == "__main__":
    asyncio.run(main())
