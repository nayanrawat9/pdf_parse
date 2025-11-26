#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configurable Pydantic schemas and prompts for JSON extraction.
Each schema option includes a Pydantic model and corresponding extraction prompt.
"""

from typing import List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field

# =============================================
# SCHEMA OPTION 1: SYSTEMC CODE GENERATION 
# =============================================

class Variable(BaseModel):
    """A variable definition in a formula."""
    name: str = Field(..., description="Variable name (e.g., 'V_IN', 'V_REF', 'UBRR').")
    description: str = Field(..., description="Description of what this variable represents.")

class BitValue(BaseModel):
    """Mapping for specific bit values (enums)."""
    value: str = Field(..., description="Binary or Hex value (e.g., '00000', '0x01')")
    name: str = Field(..., description="Short name or symbol (e.g., 'ADC0', 'DIFF_ADC1_ADC0_10x')")
    description: str = Field(..., description="Detailed description (e.g., 'Single Ended Input ADC0' or 'Pos: ADC1, Neg: ADC0, Gain: 10x')")

class BitFieldInfo(BaseModel):
    """Bit field information for register documentation."""
    name: str = Field(..., description="Bit field name (e.g., 'ADEN', 'ADSC', 'MUX')")
    bit_position: str = Field(..., description="Bit position(s) (e.g., '7', '6:4', '2:0')")
    access: str = Field(..., description="Access type: 'R', 'W', 'R/W'")
    description: str = Field(..., description="What this bit field does")
    special_behavior: Optional[str] = Field(None, description="Special behaviors like 'self-clearing', 'write-1-to-clear', 'read-only when X'")
    enum_values: List[BitValue] = Field(default_factory=list, description="If this field has specific value mappings (like a MUX), list them here.")

class RegisterInfo(BaseModel):
    """Register information for SystemC implementation."""
    name: str = Field(..., description="Register name (e.g., 'ADCSRA', 'ADMUX', 'ADCL')")
    address: str = Field(..., description="Memory address/offset in hex (e.g., '0x7A', '0x7C'). MUST be provided.")
    size_bits: int = Field(8, description="Register size in bits (typically 8, 16, or 32)")
    reset_value: str = Field(..., description="Reset value in hex (e.g., '0x00', '0xFF')")
    description: str = Field(..., description="Brief description of register purpose")
    bit_fields: List[BitFieldInfo] = Field(default_factory=list, description="List of bit fields in this register")
    
class ReadBehavior(BaseModel):
    """Behavior when reading a register."""
    returns_value: str = Field(..., description="What value is returned (e.g., 'register variable', 'calculated from state', 'combination of ADCL and ADCH')")
    side_effects: List[str] = Field(default_factory=list, description="Side effects of reading (e.g., 'clears interrupt flag', 'unlocks ADCH access')")
    special_conditions: List[str] = Field(default_factory=list, description="Special read conditions (e.g., 'must read ADCL before ADCH', 'returns 0 if ADEN=0')")

# ==========================================
# 1. NEW HELPER CLASSES
# ==========================================

class SourceType(str, Enum):
    REGISTER = "Register"
    PORT = "Port"
    INTERNAL_VAR = "InternalVar"
    PARAMETER = "Parameter"

class SourceMap(BaseModel):
    """Structured mapping for where data comes from."""
    source_type: SourceType = Field(..., description="Type of the source")
    name: str = Field(..., description="Name of the register, port, or variable")
    slice: Optional[str] = Field(None, description="Bit slice if applicable (e.g., '7:6'). None implies full width.")

class TimingType(str, Enum):
    CLOCK_CYCLES = "ClockCycles"
    TIME_ABSOLUTE = "TimeAbsolute"

class TimingInfo(BaseModel):
    """Structured timing information for generating wait() statements."""
    type: TimingType = Field(..., description="Is this based on system/ADC clocks or absolute time?")
    value: float = Field(..., description="The value (e.g., 13, 125.0)")
    unit: str = Field("ns", description="Unit for absolute time (ns, us, ms) or 'cycles' for clock based")

class TriggerType(str, Enum):
    LEVEL_HIGH = "LevelHigh"   # When bit == 1
    LEVEL_LOW = "LevelLow"     # When bit == 0
    RISING_EDGE = "RisingEdge" # 0 -> 1 transition
    FALLING_EDGE = "FallingEdge" # 1 -> 0 transition
    ALWAYS = "Always"          # On any write

class ActionType(str, Enum):
    CALL_METHOD = "MethodCall"     # Call a helper function immediately
    NOTIFY_EVENT = "EventNotify"   # Notify an SC_EVENT (for threaded logic)
    UPDATE_STATE = "StateUpdate"   # Set an internal bool/int directly

class TriggerLogic(BaseModel):
    """Logic connecting a Register Write to an Action/Formula."""
    trigger_type: TriggerType = Field(..., description="What condition triggers this?")
    bit_mask: Optional[str] = Field(None, description="Hex mask of bits involved (e.g., '0x40' for ADSC)")
    target_id: str = Field(..., description="ID of the Formula, Method, or State Variable to target")
    action_type: ActionType = Field(..., description="How to execute this logic")

class WriteBehavior(BaseModel):
    """Behavior when writing to a register."""
    direct_write: bool = Field(True, description="True if value is written to storage, False if strictly logic")
    calculations_triggered: List[TriggerLogic] = Field(default_factory=list, description="Structured logic triggers")
    bit_actions: List[str] = Field(default_factory=list, description="Human readable description of bit actions")
    state_updates: List[str] = Field(default_factory=list, description="Description of internal state changes")
    register_updates: List[str] = Field(default_factory=list, description="Description of other register effects")

class RegisterBehavior(BaseModel):
    """Complete register behavior for Read/Write implementation."""
    register_name: str = Field(..., description="Register name")
    read_behavior: Optional[ReadBehavior] = Field(None, description="Read behavior (None if write-only)")
    write_behavior: Optional[WriteBehavior] = Field(None, description="Write behavior (None if read-only)")

class PortInfo(BaseModel):
    """External port/interface information."""
    name: str = Field(..., description="Port name (e.g., 'channels', 'interrupt_socket')")
    port_type: str = Field(..., description="Port type: 'tlm_initiator_socket', 'tlm_target_socket', 'sc_port_vector<ReadInterface>', 'sc_port_vector<WriteInterface>'")
    data_type: Optional[str] = Field(None, description="Data type for port vector (e.g., 'double', 'uint8_t', 'bool')")
    count: int = Field(1, description="Number of ports (1 for single, N for vector)")
    direction: str = Field(..., description="Direction: 'input', 'output', 'bidirectional'")
    description: str = Field(..., description="Purpose of this port")
    usage: List[str] = Field(default_factory=list, description="Where/how this port is used (e.g., 'read analog voltage in conversion', 'trigger interrupt on completion')")

class InternalVariable(BaseModel):
    """Internal state variable (not a hardware register)."""
    name: str = Field(..., description="Variable name (e.g., 'conversion_active', 'selected_channel', 'voltage_reference')")
    data_type: str = Field(..., description="C++ data type (e.g., 'bool', 'int', 'uint8_t', 'double', 'sc_time')")
    initial_value: str = Field(..., description="Initial/reset value")
    description: str = Field(..., description="What this variable tracks")
    updated_by: List[str] = Field(default_factory=list, description="Which operations update this (e.g., 'Write to ADMUX.MUX bits', 'conversion completion')")
    used_by: List[str] = Field(default_factory=list, description="Which operations use this (e.g., 'ADC conversion calculation', 'channel selection')")

class FormulaInfo(BaseModel):
    """Mathematical formula/calculation."""
    id: str = Field(..., description="Unique ID for code linking (e.g., 'calc_adc_conversion')") # NEW FIELD
    name: str = Field(..., description="Display name")
    formula: str = Field(..., description="The formula string (e.g., 'ADC = (V_IN * 1023) / V_REF')")
    variables: List[Variable] = Field(default_factory=list, description="Variables used")
    trigger_condition: Optional[str] = Field(None, description="Human readable condition (deprecated in favor of WriteBehavior linkage)")
    input_sources: List[SourceMap] = Field(default_factory=list, description="Where inputs come from")
    output_destination: List[str] = Field(default_factory=list, description="Where results are stored")
    timing: Optional[TimingInfo] = Field(None, description="Execution time structure")

class InterruptInfo(BaseModel):
    """Interrupt configuration."""
    name: str = Field(..., description="Interrupt name (e.g., 'ADC Conversion Complete')")
    trigger_condition: str = Field(..., description="Condition that triggers interrupt (e.g., 'ADIF=1 AND ADIE=1')")
    flag_bit: Optional[str] = Field(None, description="Interrupt flag bit with register (e.g., 'ADIF in ADCSRA')")
    enable_bit: Optional[str] = Field(None, description="Interrupt enable bit with register (e.g., 'ADIE in ADCSRA')")
    clear_method: str = Field(..., description="How interrupt is cleared (e.g., 'write 1 to ADIF', 'automatically by hardware', 'read ADCH')")
    irq_pin_param: Optional[str] = Field(None, description="Configuration parameter name for IRQ pin (e.g., 'irq_pin')")

class ConfigParam(BaseModel):
    """Configuration parameter (initialized at construction)."""
    name: str = Field(..., description="Parameter name (e.g., 'a_ref', 'a_vcc', 'inter_', 'irq_pin')")
    data_type: str = Field(..., description="Data type (e.g., 'double', 'int', 'string')")
    description: str = Field(..., description="What this parameter configures")
    usage: List[str] = Field(default_factory=list, description="Where used (e.g., 'voltage reference selection', 'interrupt pin number')")

class OperationSequence(BaseModel):
    """Sequence of operations for a specific procedure."""
    name: str = Field(..., description="Operation name (e.g., 'Start Single Conversion', 'Initialize ADC', 'Read Conversion Result')")
    description: str = Field(..., description="What this operation does")
    steps: List[str] = Field(..., description="Ordered steps (e.g., '1. Set ADEN=1', '2. Wait for initialization', '3. Set ADSC=1')")
    registers_involved: List[str] = Field(default_factory=list, description="Registers accessed in this operation")
    preconditions: List[str] = Field(default_factory=list, description="Conditions that must be met before operation")
    postconditions: List[str] = Field(default_factory=list, description="State after operation completes")

class PeripheralDataSystemCCodeGen(BaseModel):
    """Schema: SystemC code generation without macros - focused on essential implementation details."""
    
    # Basic Information
    peripheral_name: str = Field(..., description="Peripheral name (e.g., 'ADC', 'UART', 'Timer', 'GPIO')")
    description: str = Field(..., description="High-level description of peripheral functionality")
    namespace_category: str = Field(..., description="Category namespace (e.g., 'hw_adc', 'hw_uart', 'hw_timer')")
    namespace_specific: str = Field(..., description="Specific namespace (e.g., 'avr_adc', 'avr_uart0')")
    
    # Register Definitions
    registers: List[RegisterInfo] = Field(..., description="All hardware registers with addresses and bit fields")
    register_behaviors: List[RegisterBehavior] = Field(..., description="Read/Write behaviors for each register")
    
    # External Interfaces
    ports: List[PortInfo] = Field(default_factory=list, description="External ports (channels, interrupts, etc.)")
    configuration_params: List[ConfigParam] = Field(default_factory=list, description="Configuration parameters from attribs")
    
    # Internal Implementation
    internal_variables: List[InternalVariable] = Field(default_factory=list, description="Internal state variables (not registers)")
    formulas: List[FormulaInfo] = Field(default_factory=list, description="Mathematical formulas and calculations")
    
    # Interrupts
    interrupts: List[InterruptInfo] = Field(default_factory=list, description="Interrupt sources and handling")
    
    # Operations
    key_operations: List[OperationSequence] = Field(default_factory=list, description="Key operational sequences")
    
    # Additional Notes
    register_dependencies: List[str] = Field(default_factory=list, description="Dependencies between registers (e.g., 'ADCL must be read before ADCH')")
    timing_notes: List[str] = Field(default_factory=list, description="Important timing information")
    special_notes: List[str] = Field(default_factory=list, description="Other important implementation notes")


PROMPT_SYSTEMC_CODEGEN = """You are extracting hardware peripheral specifications to generate SystemC code.

TARGET CODE STRUCTURE:
The extracted data will be used to generate three files:
1. IP_Interface.h - Defines external ports and interfaces
2. Basic.h - Declares the implementation class with registers and internal variables
3. Basic.cpp - Implements Read(), Write(), reset(), and other methods

EXTRACTION FOCUS:

1. BASIC INFORMATION:
   - Peripheral name and description
   - Namespace names (e.g., hw_adc, avr_adc)

2. REGISTERS (CRITICAL):
   For each register extract:
   - Name (e.g., ADCSRA, ADMUX, ADCL, ADCH)
   - Memory address/offset in hex (e.g., 0x7A) - MUST be provided
   - Size in bits (typically 8)
   - Reset value in hex (e.g., 0x00)
   - Description
   - Bit fields with positions, access type, and descriptions
   - ENUM VALUES (CRITICAL): If a bit field acts as a Multiplexer (MUX) or Control Mode selection (defined in a table like "Input Channel and Gain Selections"), you MUST extract every row of that table into the 'enum_values' list.
     * Capture the specific binary value (e.g., "01001")
     * Capture the full meaning (e.g., "Differential: Pos=ADC1, Neg=ADC0, Gain=10x")

3. REGISTER BEHAVIORS:
   For each register, describe:
   
   READ BEHAVIOR:
   - What value is returned (register variable, calculated value, etc.)
   - Side effects (flag clearing, unlocking access, etc.)
   - Special conditions (read order requirements, state dependencies)
   
   WRITE BEHAVIOR:
   - Is it a direct write or does it trigger logic?
   - Actions triggered by specific bits (e.g., "ADSC=1: starts conversion")
   - Calculations triggered (e.g., "triggers ADC conversion formula")
   - Internal state updates (e.g., "sets conversion_active flag")
   - Other registers affected (e.g., "sets ADIF when conversion completes")

4. EXTERNAL PORTS:
   Identify all external interfaces:
   - Input ports (e.g., ADC channels reading analog voltages)
   - Output ports (e.g., interrupt pins)
   - Port types (tlm_initiator_socket, sc_port_vector<ReadInterface<double>>, etc.)
   - Data types and counts
   - Usage description

5. CONFIGURATION PARAMETERS:
   Parameters initialized at construction from attribs:
   - Name (e.g., a_ref, a_vcc, irq_pin)
   - Data type (double, int, etc.)
   - Description and usage

6. INTERNAL VARIABLES:
   State variables needed beyond registers:
   - Name (e.g., conversion_active, selected_channel)
   - Data type (bool, int, double, sc_time)
   - Initial value
   - What updates it and what uses it

7. FORMULAS:
   Extract ALL mathematical formulas:
   - Formula name
   - Exact formula (e.g., "ADC = (V_IN * 1023) / V_REF")
   - Variable definitions
   - When it's executed (trigger condition)
   - Input sources (registers, ports, parameters)
   - Output destinations (which registers store results)
   - Timing information

8. INTERRUPTS:
   For each interrupt:
   - Interrupt name
   - Trigger condition (boolean expression)
   - Flag bit and enable bit (with register names)
   - How it's cleared
   - IRQ pin parameter name

9. KEY OPERATIONS:
   Important operational sequences:
   - Operation name (e.g., "Start Single Conversion")
   - Description
   - Ordered steps
   - Registers involved
   - Pre/post conditions

10. DEPENDENCIES & NOTES:
    - Register access order requirements
    - Timing constraints
    - Special behaviors
    - Implementation warnings

EXTRACTION GUIDELINES:
- Be specific and precise - this data will directly generate code
- For MUX registers (like ADMUX), do not just say "Selects channel". You MUST list the binary codes and what they select (e.g., 00000=ADC0, 01001=ADC1/ADC0 10x).
- Extract exact formulas with all variables defined
- Note all trigger conditions and state changes
- Identify all register-to-register interactions
- Capture timing information (clock cycles, delays)
- Document special cases and edge conditions
- Focus on information needed for Read() and Write() implementation
- Ensure all register addresses are provided in hex format

EXAMPLE EXTRACTION PATTERN:
For ADCSRA register write:
- Direct write: False (triggers logic)
- Bit actions:
  * "ADEN (bit 7) = 1: Enables ADC, allows conversions"
  * "ADSC (bit 6) = 1: Starts conversion if ADEN=1"
  * "ADIF (bit 4) = 1: Clears interrupt flag (write-1-to-clear)"
  * "ADIE (bit 3) = 1: Enables ADC interrupt"
- Calculations triggered:
  * "When ADSC=1 and ADEN=1: Execute ADC conversion formula"
- State updates:
  * "Set conversion_active = true when ADSC=1"
  * "Update prescaler_value from ADPS bits"
- Register updates:
  * "Set ADIF=1 when conversion completes"
  * "Clear ADSC=0 when conversion completes (self-clearing)"
  * "If ADIE=1, trigger interrupt via SetIrq(irq_pin, 1)"

Extract at this level of detail for all registers and operations.
"""

SCHEMA_OPTIONS = {
    "SystemC Code Generation": {
        "schema": PeripheralDataSystemCCodeGen,
        "prompt": PROMPT_SYSTEMC_CODEGEN,
        "description": "Schema: Essential information for SystemC code generation - focused on registers, behaviors, ports, formulas, and implementation logic"
    }
}


def get_schema_option(option_name: str):
    """Get schema and prompt for a given option name."""
    if option_name not in SCHEMA_OPTIONS:
        raise ValueError(f"Unknown schema option: {option_name}")
    return SCHEMA_OPTIONS[option_name]


def get_available_options():
    """Get list of available schema option names."""
    return list(SCHEMA_OPTIONS.keys())
