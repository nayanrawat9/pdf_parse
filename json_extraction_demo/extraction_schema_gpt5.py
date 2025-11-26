#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configurable Pydantic schemas and prompts for JSON extraction.
Each schema option includes a Pydantic model and corresponding extraction prompt.

This version is the "structured" upgrade (Variant B):
- Register addresses are numeric (int) with hex parsing support.
- Bit field positions are represented using BitSlice (msb/lsb).
- Access types and side effects are encoded with enums and structured actions.
- Still focused on SystemC code generation, but now generic enough for other peripherals.
"""

from typing import List, Optional, Union, Dict, Literal
from enum import Enum
from pydantic import BaseModel, Field, conint, validator

# =============================================
# COMMON LOW-LEVEL TYPES
# =============================================

class AccessType(str, Enum):
    """Canonical access types for registers and bitfields."""
    R = "R"      # Read-only
    W = "W"      # Write-only
    RW = "R/W"   # Read/Write
    RO = "RO"
    WO = "WO"
    RW_ALT = "RW"  # alias for convenience


class BitSlice(BaseModel):
    """Structured bit slice: msb:lsb, inclusive."""
    msb: conint(ge=0)
    lsb: conint(ge=0)

    @property
    def width(self) -> int:
        return self.msb - self.lsb + 1


class SourceType(str, Enum):
    REGISTER = "Register"
    PORT = "Port"
    INTERNAL_VAR = "InternalVar"
    PARAMETER = "Parameter"


class TimingType(str, Enum):
    CLOCK_CYCLES = "ClockCycles"
    TIME_ABSOLUTE = "TimeAbsolute"


class TriggerType(str, Enum):
    LEVEL_HIGH = "LevelHigh"      # When bit == 1
    LEVEL_LOW = "LevelLow"        # When bit == 0
    RISING_EDGE = "RisingEdge"    # 0 -> 1 transition
    FALLING_EDGE = "FallingEdge"  # 1 -> 0 transition
    ALWAYS = "Always"             # On any write


class ActionType(str, Enum):
    """How a trigger is executed (for TriggerLogic)."""
    CALL_METHOD = "MethodCall"     # Call a helper function immediately
    NOTIFY_EVENT = "EventNotify"   # Notify an SC_EVENT (for threaded logic)
    UPDATE_STATE = "StateUpdate"   # Set an internal bool/int directly


class ActionKind(str, Enum):
    """Generic side-effect kinds used in read/write behaviors."""
    SET_REGISTER = "set_register"
    CLEAR_REGISTER = "clear_register"
    WRITE_REGISTER = "write_register"
    TOGGLE_BIT = "toggle_bit"
    SET_FLAG = "set_flag"
    CLEAR_FLAG = "clear_flag"
    BLOCK_UPDATE = "block_update"          # e.g., lock data registers
    UNBLOCK_UPDATE = "unblock_update"      # e.g., unlock data registers
    NOTIFY_IRQ = "notify_irq"
    CALL_METHOD = "call_method"
    UPDATE_STATE = "update_state"


# =============================================
# SCHEMA OPTION 1: SYSTEMC CODE GENERATION
# =============================================

class Variable(BaseModel):
    """A variable definition in a formula."""
    name: str = Field(..., description="Variable name (e.g., 'V_IN', 'V_REF', 'UBRR').")
    description: str = Field(..., description="Description of what this variable represents.")


class BitValue(BaseModel):
    """Mapping for specific bit-field values (enums)."""
    value: int = Field(..., description="Numeric value (e.g., 0..31) of the encoded bit pattern.")
    name: str = Field(..., description="Short name or symbol (e.g., 'ADC0', 'DIFF_ADC1_ADC0_10x').")
    description: Optional[str] = Field(
        None,
        description="Detailed description (e.g., 'Single Ended Input ADC0' or 'Pos: ADC1, Neg: ADC0, Gain: 10x')."
    )


class BitFieldInfo(BaseModel):
    """Bit field information for register documentation and implementation."""
    name: str = Field(..., description="Bit field name (e.g., 'ADEN', 'ADSC', 'MUX').")
    slice: BitSlice = Field(..., description="Bit slice (msb:lsb) within the register.")
    access: AccessType = Field(..., description="Access type: 'R', 'W', 'R/W', etc.")
    description: str = Field(..., description="What this bit field does.")
    special_behavior: Optional[str] = Field(
        None,
        description="Special behaviors like 'self-clearing', 'write-1-to-clear', 'read-only when X'."
    )
    enum_values: List[BitValue] = Field(
        default_factory=list,
        description="If this field has specific value mappings (like a MUX), list them here."
    )


class RegisterInfo(BaseModel):
    """Register information for SystemC implementation."""
    name: str = Field(..., description="Register name (e.g., 'ADCSRA', 'ADMUX', 'ADCL').")
    address: str = Field(..., description="Memory address/offset in hex (e.g., '0x7A', '0x7C'). MUST be provided.")
    size_bits: int = Field(8, description="Register size in bits (typically 8, 16, or 32).")
    reset_value: str = Field(..., description="Reset value in hex (e.g., '0x00', '0xFF')")
    description: str = Field(..., description="Brief description of register purpose.")
    access: AccessType = Field(AccessType.RW, description="Default access for the whole register.")
    bit_fields: List[BitFieldInfo] = Field(default_factory=list, description="List of bit fields in this register.")


class SourceMap(BaseModel):
    """Structured mapping for where data comes from."""
    source_type: SourceType = Field(..., description="Type of the source.")
    name: str = Field(..., description="Name of the register, port, or variable.")
    slice: Optional[str] = Field(
        None,
        description="Bit slice if applicable (e.g., '7:6'). None implies full width."
    )


class TimingInfo(BaseModel):
    """Structured timing information for generating wait() statements."""
    type: TimingType = Field(..., description="Is this based on clocks or absolute time?")
    value: float = Field(..., description="The value (e.g., 13, 125.0).")
    unit: str = Field(
        "ns",
        description="Unit for absolute time (ns, us, ms) or 'cycles' / 'ADC_Clock' for clock-based."
    )


class TriggerLogic(BaseModel):
    """Logic connecting a Register Write to an Action/Formula."""
    trigger_type: TriggerType = Field(..., description="What condition triggers this?")
    bit_mask: Optional[str] = Field(
        None,
        description="Hex mask of bits involved (e.g., '0x40' for ADSC)."
    )
    target_id: str = Field(..., description="ID of the Formula, Method, or State Variable to target.")
    action_type: ActionType = Field(..., description="How to execute this logic.")


class Action(BaseModel):
    """Generic, machine-actionable side-effect description."""
    kind: ActionKind = Field(..., description="Type of side effect.")
    target: Optional[str] = Field(
        None,
        description="Register/bit/state/IRQ target (e.g., 'ADIF', 'ADCL/ADCH', 'irq_pin')."
    )
    value: Optional[int] = Field(
        None,
        description="Value associated with this action (e.g., 0 or 1, or full register value)."
    )
    condition: Optional[str] = Field(
        None,
        description="Boolean condition expression for this action (e.g., 'ADEN==1 && ADSC==1')."
    )
    timing: Optional[TimingInfo] = Field(
        None,
        description="Optional timing associated with this action (e.g., when it takes effect)."
    )


class ReadBehavior(BaseModel):
    """Behavior when reading a register."""
    returns_value: str = Field(
        ...,
        description="What value is returned (e.g., 'register variable', 'calculated from state')."
    )
    side_effects: List[Action] = Field(
        default_factory=list,
        description="Structured side effects of reading (e.g., 'lock data registers', 'clear flag')."
    )
    special_conditions: List[str] = Field(
        default_factory=list,
        description="Special read conditions (e.g., 'must read ADCL before ADCH', 'returns 0 if ADEN=0')."
    )


class WriteBehavior(BaseModel):
    """Behavior when writing to a register."""
    direct_write: bool = Field(
        True,
        description="True if value is written to backing storage, False if strictly logic/side-effects."
    )
    calculations_triggered: List[TriggerLogic] = Field(
        default_factory=list,
        description="Structured logic triggers associated with this write."
    )
    effects: List[Action] = Field(
        default_factory=list,
        description="Structured list of side effects (state updates, flag changes, IRQs, etc.)."
    )
    # Optional purely-documentation fields (keep them, but they are not primary for codegen)
    bit_actions: List[str] = Field(
        default_factory=list,
        description="Human readable description of bit actions (documentation only)."
    )
    state_updates: List[str] = Field(
        default_factory=list,
        description="Description of internal state changes (documentation only)."
    )
    register_updates: List[str] = Field(
        default_factory=list,
        description="Description of other register effects (documentation only)."
    )


class RegisterBehavior(BaseModel):
    """Complete register behavior for Read/Write implementation."""
    register_name: str = Field(..., description="Register name (e.g., 'ADCSRA', 'ADMUX').")
    read_behavior: Optional[ReadBehavior] = Field(
        None,
        description="Read behavior (None if write-only)."
    )
    write_behavior: Optional[WriteBehavior] = Field(
        None,
        description="Write behavior (None if read-only)."
    )


class PortDirection(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"


class PortInfo(BaseModel):
    """External port/interface information."""
    name: str = Field(..., description="Port name (e.g., 'channels', 'interrupt_socket').")
    port_type: str = Field(
        ...,
        description="Port type (e.g., 'tlm_initiator_socket', 'tlm_target_socket', 'sc_port_vector<ReadInterface>')."
    )
    data_type: Optional[str] = Field(
        None,
        description="Data type for port vectors if applicable (e.g., 'double', 'uint8_t', 'bool')."
    )
    count: int = Field(1, description="Number of ports (1 for single, N for vector).")
    direction: PortDirection = Field(..., description="Direction: 'input', 'output', or 'bidirectional'.")
    description: str = Field(..., description="Purpose of this port.")
    usage: List[str] = Field(default_factory=list, description="Where/how this port is used.")
    clock_domain: Optional[str] = Field(
        None,
        description="Name of the clock domain this port belongs to (if applicable)."
    )


class InternalVariable(BaseModel):
    """Internal state variable (not a hardware register)."""
    name: str = Field(..., description="Variable name (e.g., 'conversion_active', 'selected_channel').")
    data_type: str = Field(..., description="C++ data type (e.g., 'bool', 'int', 'uint8_t', 'double', 'sc_time').")
    initial_value: str = Field(..., description="Initial/reset value.")
    description: str = Field(..., description="What this variable tracks.")
    updated_by: List[str] = Field(
        default_factory=list,
        description="Which operations update this (e.g., 'write to ADMUX.MUX bits', 'conversion completion')."
    )
    used_by: List[str] = Field(
        default_factory=list,
        description="Which operations use this (e.g., 'ADC conversion calculation', 'channel selection')."
    )


class FormulaInfo(BaseModel):
    """Mathematical formula/calculation."""
    id: str = Field(
        ...,
        description="Unique ID for code linking (e.g., 'calc_adc_conversion')."
    )
    name: str = Field(..., description="Display name.")
    formula: str = Field(
        ...,
        description="The formula string (e.g., 'ADC = (V_IN * 1023) / V_REF')."
    )
    variables: List[Variable] = Field(
        default_factory=list,
        description="Variables used in this formula."
    )
    trigger_condition: Optional[str] = Field(
        None,
        description="Human readable condition; linkage should primarily use WriteBehavior/TriggerLogic."
    )
    input_sources: List[SourceMap] = Field(
        default_factory=list,
        description="Where inputs come from."
    )
    output_destination: List[str] = Field(
        default_factory=list,
        description="Where results are stored (e.g., internal variables or registers)."
    )
    timing: Optional[TimingInfo] = Field(
        None,
        description="Execution time structure."
    )
    # Optional codegen metadata
    output_width: Optional[int] = Field(
        None,
        description="Bit-width of the output (e.g., 10, 16)."
    )
    output_signed: Optional[bool] = Field(
        None,
        description="Whether output is treated as signed (two's complement) or unsigned."
    )
    clamp_min: Optional[int] = Field(
        None,
        description="Minimum clamp value applied after computation."
    )
    clamp_max: Optional[int] = Field(
        None,
        description="Maximum clamp value applied after computation."
    )
    rounding_mode: Optional[str] = Field(
        None,
        description="Rounding mode (e.g., 'trunc', 'round')."
    )


class InterruptInfo(BaseModel):
    """Interrupt configuration."""
    name: str = Field(..., description="Interrupt name (e.g., 'ADC Conversion Complete').")
    trigger_condition: str = Field(
        ...,
        description="Condition that triggers interrupt (e.g., 'ADIF=1 AND ADIE=1')."
    )
    flag_bit: Optional[str] = Field(
        None,
        description="Interrupt flag bit with register (e.g., 'ADIF in ADCSRA')."
    )
    enable_bit: Optional[str] = Field(
        None,
        description="Interrupt enable bit with register (e.g., 'ADIE in ADCSRA')."
    )
    clear_method: str = Field(
        ...,
        description="How interrupt is cleared (e.g., 'write 1 to ADIF', 'automatically by hardware')."
    )
    irq_pin_param: Optional[str] = Field(
        None,
        description="Configuration parameter name for IRQ pin (e.g., 'irq_pin')."
    )
    irq_vector: Optional[int] = Field(
        None,
        description="Optional interrupt vector number or index."
    )


class ConfigParam(BaseModel):
    """Configuration parameter (initialized at construction)."""
    name: str = Field(..., description="Parameter name (e.g., 'a_ref', 'a_vcc', 'inter_', 'irq_pin').")
    data_type: str = Field(..., description="Data type (e.g., 'double', 'int', 'string').")
    description: str = Field(..., description="What this parameter configures.")
    usage: List[str] = Field(default_factory=list, description="Where used.")


class OperationStep(BaseModel):
    """Single step in an operation sequence."""
    text: str = Field(..., description="Step description, including numbering if desired.")
    timing: Optional[TimingInfo] = Field(
        None,
        description="Optional timing associated with this step."
    )


class OperationSequence(BaseModel):
    """Sequence of operations for a specific procedure."""
    name: str = Field(..., description="Operation name (e.g., 'Start Single Conversion').")
    description: str = Field(..., description="What this operation does.")
    steps: List[OperationStep] = Field(
        ...,
        description="Ordered steps (e.g., '1. Set ADEN=1', '2. Wait for initialization')."
    )
    registers_involved: List[str] = Field(
        default_factory=list,
        description="Registers accessed in this operation."
    )
    preconditions: List[str] = Field(
        default_factory=list,
        description="Conditions that must be met before operation."
    )
    postconditions: List[str] = Field(
        default_factory=list,
        description="State after operation completes."
    )


class ClockDomain(BaseModel):
    """Optional clock domain description (useful for timers, UART, etc.)."""
    name: str = Field(..., description="Clock domain name (e.g., 'cpu_clk', 'adc_clk').")
    frequency: float = Field(..., description="Frequency value.")
    unit: str = Field("Hz", description="Frequency unit: Hz, kHz, MHz.")


class PeripheralDataSystemCCodeGen(BaseModel):
    """
    Schema: SystemC code generation without macro-heavy details - focused on essential implementation details,
    but generic enough for any register-based peripheral (ADC, UART, Timer, GPIO, CAN, etc.).
    """

    version: str = Field(
        "1.1",
        description="Schema version to help with migrations."
    )

    # Basic Information
    peripheral_name: str = Field(..., description="Peripheral name (e.g., 'ADC', 'UART', 'Timer', 'GPIO').")
    description: str = Field(..., description="High-level description of peripheral functionality.")
    namespace_category: str = Field(..., description="Category namespace (e.g., 'hw_adc', 'hw_uart', 'hw_timer').")
    namespace_specific: str = Field(..., description="Specific namespace (e.g., 'avr_adc', 'avr_uart0').")

    # Optional metadata about origin
    source_doc: Optional[str] = Field(
        None,
        description="Source document reference (e.g., filename, section, page)."
    )

    # Register Definitions
    registers: List[RegisterInfo] = Field(
        ...,
        description="All hardware registers with addresses and bit fields."
    )
    register_behaviors: List[RegisterBehavior] = Field(
        ...,
        description="Read/Write behaviors for each register."
    )

    # External Interfaces
    ports: List[PortInfo] = Field(
        default_factory=list,
        description="External ports (channels, interrupts, buses, etc.)."
    )
    configuration_params: List[ConfigParam] = Field(
        default_factory=list,
        description="Configuration parameters from attributes."
    )

    # Internal Implementation
    internal_variables: List[InternalVariable] = Field(
        default_factory=list,
        description="Internal state variables (not registers)."
    )
    formulas: List[FormulaInfo] = Field(
        default_factory=list,
        description="Mathematical formulas and calculations."
    )

    # Interrupts
    interrupts: List[InterruptInfo] = Field(
        default_factory=list,
        description="Interrupt sources and handling."
    )

    # Operations
    key_operations: List[OperationSequence] = Field(
        default_factory=list,
        description="Key operational sequences."
    )

    # Misc global notes
    register_dependencies: List[str] = Field(
        default_factory=list,
        description="Dependencies between registers (e.g., access order requirements)."
    )
    timing_notes: List[str] = Field(
        default_factory=list,
        description="Important timing information."
    )
    special_notes: List[str] = Field(
        default_factory=list,
        description="Other important implementation notes."
    )

    # Optional generic extensions
    clock_domains: List[ClockDomain] = Field(
        default_factory=list,
        description="Clock domains used by this peripheral (if any)."
    )


# =========================================================
# PROMPT FOR SYSTEMC CODE GENERATION EXTRACTION
# =========================================================

PROMPT_SYSTEMC_CODEGEN = """You are extracting hardware peripheral specifications to generate SystemC code.

TARGET CODE STRUCTURE:
The extracted data will be used to generate three files:
1. IP_Interface.h - Defines external ports and interfaces
2. Basic.h       - Declares the implementation class with registers and internal variables
3. Basic.cpp     - Implements Read(), Write(), reset(), and other methods

SCHEMA STRUCTURE (IMPORTANT):

You are filling a structured JSON schema (PeripheralDataSystemCCodeGen) with:
- Typed register addresses.
- Bit fields with explicit msb/lsb slices (BitSlice).
- Access types using canonical values ('R', 'W', 'R/W').
- Structured read/write behaviors using 'Action' objects for side effects, and 'TriggerLogic' for write-triggered logic.
- Formulas with explicit inputs, outputs, and timing information.
- Ports, internal variables, interrupts, and operation sequences.

EXTRACTION FOCUS:

1. BASIC INFORMATION:
   - Peripheral name and description
   - Namespace names (e.g., hw_adc, avr_adc)

2. REGISTERS (CRITICAL):
   For each register extract:
   - Name (e.g., ADCSRA, ADMUX, ADCL, ADCH)
   - Memory address/offset in hex (e.g., 0x7A)
   - Size in bits (typically 8, 16, or 32)
   - Reset value in hex (e.g., 0x00)
   - Description
   - Access type (R, W, R/W)
   - Bit fields with:
       * name
       * slice.msb and slice.lsb (e.g., 7:6 for REFS1:0, 5:5 for ADLAR)
       * access type
       * description
       * special behavior if any
   - ENUM VALUES (CRITICAL): If a bit field acts as a Multiplexer (MUX) or Control Mode selection
     (defined in a table like "Input Channel and Gain Selections"), you MUST extract every row
     of that table into the 'enum_values' list.
     * Capture the numeric value (e.g., 0..31) corresponding to the binary code.
     * Capture the full meaning (e.g., "Differential: Pos=ADC1, Neg=ADC0, Gain=10x").

3. REGISTER BEHAVIORS:
   For each register, describe:

   READ BEHAVIOR:
   - 'returns_value' text: what is returned (backing variable vs computed value).
   - 'side_effects': list of structured Action objects for side effects:
       * For example: reading ADCL locks the data registers:
           kind: "block_update"
           target: "ADCL/ADCH"
       * reading ADCH unlocks them:
           kind: "unblock_update"
           target: "ADCL/ADCH"
   - 'special_conditions': textual notes (e.g., "must read ADCL before ADCH").

   WRITE BEHAVIOR:
   - 'direct_write': True if the write updates the backing storage, False if it only triggers logic.
   - 'calculations_triggered': TriggerLogic list:
       * trigger_type: for ADSC rising edge, use 'RisingEdge'
       * bit_mask: hex mask for relevant bits (e.g., '0x40' for ADSC)
       * target_id: ID of formula or method triggered (e.g., 'calc_adc_single_ended', 'start_conversion_method').
       * action_type: e.g., 'MethodCall'.
   - 'effects': structured Action list representing side effects:
       * enabling/disabling ADC
       * setting/clearing flags (ADIF, ADSC)
       * notifying IRQ when ADIF and ADIE are set
   - 'bit_actions', 'state_updates', 'register_updates': human-readable explanatory texts (optional).

4. EXTERNAL PORTS:
   Identify all external interfaces:
   - Input ports (e.g., ADC channels reading analog voltages).
   - Output ports (e.g., interrupt pins).
   - Port types (tlm_initiator_socket, tlm_target_socket, sc_port_vector<ReadInterface<double>>, etc.).
   - Data types and counts.
   - Direction (input/output/bidirectional).
   - Usage description and optional clock_domain.

5. CONFIGURATION PARAMETERS:
   Parameters initialized at construction from attributes:
   - Name (e.g., a_ref, a_vcc, irq_pin)
   - Data type (double, int, etc.)
   - Description and usage

6. INTERNAL VARIABLES:
   State variables needed beyond registers:
   - Name (e.g., conversion_active, selected_channel)
   - Data type (bool, int, double, sc_time, etc.)
   - Initial value
   - What updates it and what uses it

7. FORMULAS:
   Extract ALL mathematical formulas:
   - Formula name and 'id'
   - Exact formula (e.g., "ADC = (V_IN * 1023) / V_REF")
   - Variable definitions
   - Input sources (registers, ports, parameters)
   - Output destinations (internal variables or registers)
   - Timing information (e.g., 13 ADC clock cycles)
   - If differential or signed output, specify output_signed=true and output_width.

8. INTERRUPTS:
   For each interrupt:
   - Interrupt name
   - Trigger condition (boolean expression)
   - Flag bit and enable bit (with register names)
   - How it's cleared
   - IRQ pin parameter name
   - Optional vector number (if documented)

9. KEY OPERATIONS:
   Important operational sequences:
   - Operation name (e.g., "Start Single Conversion")
   - Description
   - Ordered steps (OperationStep objects, each with 'text'; add 'timing' if given)
   - Registers involved
   - Pre/post conditions

10. DEPENDENCIES & NOTES:
    - Register access order requirements (e.g., ADCL must be read before ADCH).
    - Timing constraints.
    - Special behaviors and implementation warnings.

EXTRACTION GUIDELINES:
- Be specific and precise - this data will directly generate code.
- Use hex for addresses and reset values; you may parse hex or decimal from the text.
- For MUX registers (like ADMUX), do not just say "Selects channel".
  You MUST list all binary codes and what they select as BitField.enum_values.
- Always populate BitSlice.msb and BitSlice.lsb to match tables and bit layouts.
- Use structured Action objects for side effects rather than vague descriptions.
- Note all trigger conditions and state changes.
- Capture timing information in TimingInfo objects when cycles or time are specified.
- Focus on information needed for Read() and Write() implementation, plus interrupts and key operations.
"""

SCHEMA_OPTIONS = {
    "SystemC Code Generation": {
        "schema": PeripheralDataSystemCCodeGen,
        "prompt": PROMPT_SYSTEMC_CODEGEN,
        "description": "Schema: Essential information for SystemC code generation - structured registers, behaviors, ports, formulas, and implementation logic for any peripheral."
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
