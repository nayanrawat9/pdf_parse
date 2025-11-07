# json_extraction_gpt5_cli.py

from pydantic import BaseModel
from typing import List, Optional, Literal
import instructor
import json
import asyncio
import inspect
import argparse
from pathlib import Path
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


# --- CLI Setup ---
parser = argparse.ArgumentParser(
    description="Extract structured JSON from peripheral documentation markdown using instructor.",
    epilog='Example: python json_extraction_gpt5_cli.py --input 4__Memories_with_images.md --provider minimax-m2:cloud'
)
parser.add_argument("--input", required=True, help="Path to the input markdown file")
parser.add_argument("--provider", default="minimax-m2:cloud", help="Provider string (default: minimax-m2:cloud)")

args = parser.parse_args()

PROVIDER = args.provider
MODE = instructor.Mode.JSON

with open(args.input, "r", encoding="utf-8") as f:
    text = f.read()


# --- Extraction ---
async def extract_peripheral():
    client = instructor.from_provider(f"ollama/{PROVIDER}", mode=MODE)

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

    # Save to file with provider in name
    safe_provider = args.provider.replace(":", "_").replace("-", "_")
    input_stem = Path(args.input).stem
    output_file = f"{input_stem}_extraction_gpt5_{safe_provider}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(response.model_dump(), f, indent=2)
    
    print(f"Extraction completed. JSON saved to {output_file}")


if __name__ == "__main__":
    asyncio.run(extract_peripheral())
