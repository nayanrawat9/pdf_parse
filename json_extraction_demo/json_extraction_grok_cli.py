import argparse
from pydantic import BaseModel
from typing import List, Optional, Literal
import instructor
import json
import asyncio
import inspect
import os
import sys
if sys.platform != 'win32':
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
    if 'http_proxy' in os.environ:
        del os.environ['http_proxy']
    if 'https_proxy' in os.environ:
        del os.environ['https_proxy']
# --- Peripheral schema ---
class RegisterBitField(BaseModel):
    name: str
    bit_range: str
    description: Optional[str] = None
    access: Optional[Literal["R", "W", "R/W", "RO", "RW"]] = None
    reset_value: Optional[str] = None
    notes: Optional[str] = None

class Register(BaseModel):
    name: str
    address: Optional[str] = None
    description: Optional[str] = None
    bitfields: List[RegisterBitField] = []
    read_access: Optional[bool] = None
    write_access: Optional[bool] = None
    initial_value: Optional[str] = None
    behavior_notes: Optional[str] = None

class Interrupt(BaseModel):
    name: str
    trigger_condition: Optional[str] = None
    enable_register: Optional[str] = None
    flag_register: Optional[str] = None
    description: Optional[str] = None

class StateTransition(BaseModel):
    from_state: str
    to_state: str
    condition: str

class StateMachine(BaseModel):
    name: str
    states: List[str]
    transitions: List[StateTransition]

class Operation(BaseModel):
    name: str
    description: str
    related_registers: List[str] = []
    algorithm: Optional[str] = None

class Peripheral(BaseModel):
    name: str
    description: Optional[str] = None
    registers: List[Register] = []
    interrupts: List[Interrupt] = []
    operations: List[Operation] = []
    state_machines: List[StateMachine] = []
    memory_map: Optional[str] = None

# --- CLI ---
def main():
    parser = argparse.ArgumentParser(
        description="Extract peripheral data from markdown documentation.",
        epilog="Example: py json_extraction_grok_cli.py --input 4__Memories_with_images.md --provider minimax-m2:cloud"
    )
    parser.add_argument("--input", required=True, help="Path to the input markdown file")
    parser.add_argument("--provider", default="minimax-m2:cloud", help="Provider for the model (default: minimax-m2:cloud)")
    args = parser.parse_args()

    # Read input file
    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    # Run extraction
    asyncio.run(extract_peripheral(args.input, args.provider, text))

async def extract_peripheral(input_file, provider, text):
    MODE = instructor.Mode.JSON
    client = instructor.from_provider(f"ollama/{provider}", mode=MODE)

    messages = [
        {
            "role": "system",
            "content": "You are a hardware documentation analyzer. Extract structured information as defined in the response model, focusing only on software-visible registers, operations, interrupts, and states.",
        },
        {
            "role": "user",
            "content": f"Extract all register, bitfield, operation, and interrupt data from this peripheral documentation:\\n\\n{text}",
        },
    ]

    result = client.chat.completions.create(response_model=Peripheral, messages=messages)

    if inspect.iscoroutine(result):
        response = await result
    else:
        response = result

    # Generate output filename
    base_name = os.path.basename(input_file)
    name_without_ext = base_name.rsplit('.', 1)[0]
    safe_provider = provider.replace(':', '_').replace('/', '_')
    output_filename = f"{name_without_ext}_grok_{safe_provider}.json"

    # Save to file
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(response.model_dump(), f, indent=2)

    print(f"Extraction complete. Output saved to {output_filename}")

if __name__ == "__main__":
    main()
