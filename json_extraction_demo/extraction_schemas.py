#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configurable Pydantic schemas and prompts for JSON extraction.
Each schema option includes a Pydantic model and corresponding extraction prompt.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# SCHEMA OPTION 1: DETAILED PERIPHERAL EXTRACTION (Original)
# ============================================================================

class Variable(BaseModel):
    """A variable definition in a formula."""
    name: str = Field(..., description="Variable name (e.g., 'V_IN', 'V_REF', 'UBRR').")
    description: str = Field(..., description="Description of what this variable represents.")

class ConversionFormula(BaseModel):
    """Mathematical formula for data conversion, calculation, or transformation."""
    name: str = Field(..., description="Name of the formula (e.g., 'Single-Ended Conversion', 'Differential Conversion', 'Baud Rate Calculation').")
    formula: str = Field(..., description="The mathematical formula in LaTeX or plain text format (e.g., 'ADC = (V_IN * 1023) / V_REF').")
    variables: List[Variable] = Field(default_factory=list, description="List of variable definitions used in the formula.")
    description: str = Field(..., description="When and how this formula is used in the peripheral operation.")
    applies_to: List[str] = Field(default_factory=list, description="Which modes, channels, or conditions this formula applies to (e.g., ['single-ended mode', 'all channels']).")

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

class PeripheralDataDetailed(BaseModel):
    """The complete set of extracted data for a hardware peripheral."""
    peripheral_name: str = Field(..., description="The name of the peripheral (e.g., 'EEPROM', 'GPIO', 'ADC').")
    description: str = Field(..., description="A high-level description of the peripheral's functionality.")
    registers: List[Register] = Field(..., description="A list of all registers for this peripheral.")
    operations: List[Operation] = Field(default_factory=list, description="A list of key operations or procedures.")
    state_machine: Optional[StateMachine] = Field(None, description="The state machine for the peripheral, if one exists.")
    interrupts: Optional[Interrupts] = Field(None, description="The interrupt configuration for the peripheral, if applicable.")
    conversion_formulas: List[ConversionFormula] = Field(default_factory=list, description="Mathematical formulas for data conversion, calculation, or transformation. CRITICAL for software modeling (e.g., ADC conversion formulas, baud rate calculations, timer prescaler formulas).")
    configuration_parameters: List[ConfigParameter] = Field(default_factory=list, description="A list of configuration parameters.")
    dependencies: List[str] = Field(default_factory=list, description="A list of other peripherals or modules this peripheral depends on.")
    timing_constraints: Optional[str] = Field(None, description="A brief summary of any timing constraints that are critical for software.")
    special_notes: Optional[str] = Field(None, description="Any other special notes or important information for software modeling.")


PROMPT_DETAILED = """You are an expert at extracting hardware peripheral specifications from microcontroller reference manuals.

Your task is to extract structured information suitable for creating a SystemC software model.

FOCUS ON:
- Register definitions with bit fields and access types (R/W/R/W)
- Software operation procedures (step-by-step operations)
- State machines if present
- Interrupt sources and control bits
- Configuration parameters
- **CONVERSION FORMULAS: Extract ALL mathematical formulas that describe data conversion, calculation, or transformation (e.g., ADC conversion formulas, baud rate calculations, timer prescaler formulas, PWM duty cycle calculations). These are CRITICAL for software modeling and MUST be extracted with their variable definitions.**

IGNORE:
- Physical/electrical characteristics (voltage levels, current ratings, capacitance values, pin impedance)
- Detailed timing diagrams (unless critical for software behavior)
- Manufacturing/testing information
- Pin descriptions (unless they're control signals)

IMPORTANT GUIDELINES:
1. Extract ALL registers mentioned in the text
2. For each register, extract ALL bit fields with their positions
3. **Extract ALL mathematical formulas with their variable definitions - these are essential for implementing Read/Write functions**
4. Preserve operation procedures as sequential steps
5. Note interdependencies between registers
6. Identify state machines from operational descriptions
7. Extract interrupt enable/flag bits carefully
8. Use exact names from documentation (preserve case and naming)
9. If information is unclear, extract what you can and note in descriptions
10. **Pay special attention to sections describing conversion results, calculations, or data transformations**

CONTEXT FOR SOFTWARE MODELING:
The extracted information will be used to generate SystemC models with:
- Read() functions that return register values based on peripheral state
- Write() functions that:
  * Update register values
  * Trigger peripheral operations (e.g., start conversion, transmit data)
  * Perform data conversions using mathematical formulas
  * Update internal state based on calculations
  * Generate interrupts when operations complete

Therefore, pay special attention to:
- How register writes trigger conversions or operations
- Mathematical formulas used in data transformation (these go in Read/Write implementations)
- Relationships between input data and output results
- Timing of when conversions occur and complete
- Which register bits control which operations
- How data flows through the peripheral (input → processing → output)

FORMULA EXTRACTION EXAMPLES:
- ADC: "ADC = (V_IN * 1023) / V_REF" for single-ended conversion
- UART: "UBRR = (f_osc / (16 * BAUD)) - 1" for baud rate generation
- Timer: "f_output = f_clock / (2 * N * (1 + OCRnx))" for PWM frequency
- Any equation showing how input values are transformed to output values
"""


# ============================================================================
# SCHEMA OPTION 2: SIMPLIFIED REGISTER-FOCUSED EXTRACTION
# ============================================================================

class SimpleBitField(BaseModel):
    """Simplified bit field definition."""
    name: str = Field(..., description="Bit field name")
    bits: str = Field(..., description="Bit position(s)")
    access: str = Field(..., description="R/W/R/W")
    description: str = Field(..., description="Brief description")

class SimpleRegister(BaseModel):
    """Simplified register definition."""
    name: str = Field(..., description="Register name")
    address: Optional[str] = Field(None, description="Memory address")
    bit_fields: List[SimpleBitField] = Field(..., description="Bit fields")

class PeripheralDataSimple(BaseModel):
    """Simplified peripheral data focused on registers."""
    peripheral_name: str = Field(..., description="Peripheral name")
    description: str = Field(..., description="Brief description")
    registers: List[SimpleRegister] = Field(..., description="All registers")
    notes: Optional[str] = Field(None, description="Additional notes")


PROMPT_SIMPLE = """Extract register information from this hardware documentation.

Focus on:
- Register names and addresses
- Bit field names and positions
- Read/Write access types
- Brief descriptions

Keep it concise and focused on register definitions only.
"""


# ============================================================================
# SCHEMA OPTION 3: OPERATION-FOCUSED EXTRACTION
# ============================================================================

class SimpleOperationStep(BaseModel):
    """A step in an operation."""
    step: int = Field(..., description="Step number")
    action: str = Field(..., description="What to do")
    registers: List[str] = Field(default_factory=list, description="Registers involved")

class SimpleOperation(BaseModel):
    """An operation or procedure."""
    name: str = Field(..., description="Operation name")
    description: str = Field(..., description="What it does")
    steps: List[SimpleOperationStep] = Field(..., description="Steps to perform")

class PeripheralDataOperations(BaseModel):
    """Peripheral data focused on operations."""
    peripheral_name: str = Field(..., description="Peripheral name")
    description: str = Field(..., description="Brief description")
    operations: List[SimpleOperation] = Field(..., description="All operations")


PROMPT_OPERATIONS = """Extract operational procedures from this hardware documentation.

Focus on:
- Step-by-step procedures
- Initialization sequences
- Configuration workflows
- Register access sequences

Organize as clear, numbered steps with register names.
"""


# ============================================================================
# SCHEMA OPTION 4: SYSTEMC MODEL-FOCUSED EXTRACTION
# ============================================================================

class RegisterBitFieldAction(BaseModel):
    """Action triggered by a bit field write."""
    bit_field: str = Field(..., description="Bit field name (e.g., 'ADSC', 'ADEN')")
    bit_position: str = Field(..., description="Bit position(s) (e.g., '7', '6:4')")
    trigger_condition: str = Field(..., description="When this action occurs (e.g., 'written to 1', 'cleared', 'any write')")
    action_description: str = Field(..., description="What happens (e.g., 'starts ADC conversion', 'enables peripheral')")
    side_effects: List[str] = Field(default_factory=list, description="Side effects (e.g., 'clears ADIF flag', 'triggers interrupt')")
    affects_registers: List[str] = Field(default_factory=list, description="Other registers affected by this action")

class RegisterReadBehavior(BaseModel):
    """Behavior when reading a register."""
    description: str = Field(..., description="What value is returned and why")
    side_effects: List[str] = Field(default_factory=list, description="Side effects of reading (e.g., 'clears interrupt flag', 'unlocks other registers')")
    special_conditions: List[str] = Field(default_factory=list, description="Special read conditions (e.g., 'must read ADCL before ADCH', 'returns 0 if peripheral disabled')")
    depends_on_state: List[str] = Field(default_factory=list, description="Internal state that affects read value")

class RegisterWriteBehavior(BaseModel):
    """Behavior when writing to a register."""
    description: str = Field(..., description="Overall write behavior summary")
    bit_actions: List[RegisterBitFieldAction] = Field(default_factory=list, description="Actions for individual bit fields")
    formulas_triggered: List[str] = Field(default_factory=list, description="Names of formulas/calculations triggered by write")
    state_changes: List[str] = Field(default_factory=list, description="Internal state changes caused by write")
    special_behaviors: List[str] = Field(default_factory=list, description="Special write behaviors (e.g., 'write-1-to-clear', 'self-clearing bits')")

class SystemCRegister(BaseModel):
    """Register definition optimized for SystemC Read/Write implementation."""
    name: str = Field(..., description="Register name (e.g., 'ADCSRA', 'ADMUX')")
    address: str = Field(..., description="Memory address or offset (e.g., '0x7A', '0x7C')")
    size_bits: int = Field(8, description="Register size in bits (typically 8, 16, or 32)")
    reset_value: str = Field(..., description="Value after reset (e.g., '0x00', '0b00000000')")
    access_type: str = Field(..., description="Access type (e.g., 'R/W', 'R', 'W', 'Mixed')")
    read_behavior: RegisterReadBehavior = Field(..., description="Behavior when Read() is called")
    write_behavior: RegisterWriteBehavior = Field(..., description="Behavior when Write() is called")

class InternalStateVariable(BaseModel):
    """Internal state variable needed in SystemC model."""
    name: str = Field(..., description="Variable name (e.g., 'conversion_in_progress', 'selected_channel')")
    data_type: str = Field(..., description="Data type (e.g., 'bool', 'uint8_t', 'int', 'double', 'enum')")
    initial_value: str = Field(..., description="Initial/reset value")
    description: str = Field(..., description="What this variable tracks")
    updated_by: List[str] = Field(default_factory=list, description="Which register writes update this variable")
    used_by: List[str] = Field(default_factory=list, description="Which operations/calculations use this variable")

class ExternalPort(BaseModel):
    """External interface port (input/output)."""
    name: str = Field(..., description="Port name (e.g., 'channels', 'interrupt_socket')")
    direction: str = Field(..., description="Direction: 'input', 'output', or 'bidirectional'")
    data_type: str = Field(..., description="Data type (e.g., 'double', 'bool', 'uint8_t')")
    count: int = Field(1, description="Number of ports (e.g., 8 for ADC channels)")
    description: str = Field(..., description="Purpose of this port")
    accessed_by: List[str] = Field(default_factory=list, description="Which operations access this port")

class ConfigurationParameter(BaseModel):
    """Configuration parameter for SystemC model."""
    name: str = Field(..., description="Parameter name (e.g., 'a_ref', 'a_vcc', 'irq_pin')")
    data_type: str = Field(..., description="Data type (e.g., 'double', 'int', 'string')")
    default_value: Optional[str] = Field(None, description="Default value if any")
    description: str = Field(..., description="What this parameter configures")
    used_in: List[str] = Field(default_factory=list, description="Where this parameter is used (e.g., 'voltage reference selection', 'interrupt generation')")

class CalculationFormula(BaseModel):
    """Mathematical formula/calculation performed by peripheral."""
    name: str = Field(..., description="Formula name (e.g., 'Single-Ended ADC Conversion', 'Prescaler Calculation')")
    formula: str = Field(..., description="The formula (e.g., 'ADC = (V_IN * 1023) / V_REF')")
    variables: List[Variable] = Field(default_factory=list, description="Variables used in formula")
    trigger_condition: str = Field(..., description="When this calculation is performed (e.g., 'when ADSC bit is set and ADEN=1')")
    input_sources: List[str] = Field(default_factory=list, description="Where inputs come from (e.g., 'channels[mux]', 'ADMUX register')")
    output_destination: List[str] = Field(default_factory=list, description="Where results are stored (e.g., 'ADCL', 'ADCH')")
    execution_time: Optional[str] = Field(None, description="How long calculation takes (e.g., '13 ADC clock cycles')")

class InterruptCondition(BaseModel):
    """Condition that generates an interrupt."""
    interrupt_name: str = Field(..., description="Interrupt name (e.g., 'ADC Conversion Complete')")
    trigger_condition: str = Field(..., description="Condition that triggers interrupt (e.g., 'ADIF=1 AND ADIE=1')")
    flag_bit: Optional[str] = Field(None, description="Interrupt flag bit (e.g., 'ADIF in ADCSRA')")
    enable_bit: Optional[str] = Field(None, description="Interrupt enable bit (e.g., 'ADIE in ADCSRA')")
    clear_condition: str = Field(..., description="How interrupt is cleared (e.g., 'write 1 to ADIF', 'automatically cleared')")
    irq_pin: Optional[str] = Field(None, description="IRQ pin or vector number")

class OperationalMode(BaseModel):
    """Operating mode of the peripheral."""
    mode_name: str = Field(..., description="Mode name (e.g., 'Single Conversion', 'Free Running', 'Auto Trigger')")
    description: str = Field(..., description="What this mode does")
    entry_condition: str = Field(..., description="How to enter this mode (e.g., 'set ADATE=0, write ADSC=1')")
    exit_condition: str = Field(..., description="How to exit this mode")
    behavior: str = Field(..., description="Behavior in this mode")
    affected_registers: List[str] = Field(default_factory=list, description="Registers that control or are affected by this mode")

class TimingConstraint(BaseModel):
    """Timing constraint or delay."""
    operation: str = Field(..., description="Operation name (e.g., 'ADC Conversion', 'Channel Settling')")
    duration: str = Field(..., description="Time duration (e.g., '13 ADC clock cycles', '125 µs')")
    condition: str = Field(..., description="When this timing applies")
    description: str = Field(..., description="Additional timing details")

class DataFlowPath(BaseModel):
    """Data flow through the peripheral."""
    flow_name: str = Field(..., description="Name of data flow (e.g., 'ADC Conversion Path')")
    steps: List[str] = Field(..., description="Ordered steps of data flow")
    input_source: str = Field(..., description="Where data enters (e.g., 'analog channel pins')")
    output_destination: str = Field(..., description="Where data exits (e.g., 'ADCL/ADCH registers')")
    transformations: List[str] = Field(default_factory=list, description="Transformations applied to data")

class PeripheralDataSystemC(BaseModel):
    """Complete peripheral data optimized for SystemC model generation."""
    peripheral_name: str = Field(..., description="Peripheral name (e.g., 'ADC', 'UART', 'Timer')")
    description: str = Field(..., description="High-level peripheral description")
    
    # Core register interface
    registers: List[SystemCRegister] = Field(..., description="All registers with Read/Write behaviors")
    
    # Internal implementation
    internal_state: List[InternalStateVariable] = Field(default_factory=list, description="Internal state variables needed")
    calculations: List[CalculationFormula] = Field(default_factory=list, description="Formulas and calculations performed")
    
    # External interfaces
    external_ports: List[ExternalPort] = Field(default_factory=list, description="Input/output ports")
    configuration_params: List[ConfigurationParameter] = Field(default_factory=list, description="Configuration parameters")
    
    # Behavior
    operational_modes: List[OperationalMode] = Field(default_factory=list, description="Operating modes")
    interrupts: List[InterruptCondition] = Field(default_factory=list, description="Interrupt conditions")
    timing_constraints: List[TimingConstraint] = Field(default_factory=list, description="Timing requirements")
    data_flows: List[DataFlowPath] = Field(default_factory=list, description="Data flow paths")
    
    # Additional notes
    register_dependencies: List[str] = Field(default_factory=list, description="Dependencies between registers (e.g., 'ADCL must be read before ADCH')")
    special_notes: List[str] = Field(default_factory=list, description="Important implementation notes")


PROMPT_SYSTEMC = """You are extracting hardware peripheral specifications to generate a SystemC software model.

TARGET SYSTEMC MODEL STRUCTURE:
The model will have:
- Read(address, size) function: returns register values based on peripheral state
- Write(address, data, size) function: updates registers, triggers operations, performs calculations
- Internal state variables: track peripheral state beyond registers
- External ports: for inputs (e.g., sensor data) and outputs (e.g., interrupts)
- Configuration parameters: initialized at construction (e.g., voltage references, pin numbers)
- Timing-aware behavior: delays and clock cycle counts

EXTRACTION FOCUS:

1. REGISTERS - For each register, extract:
   READ BEHAVIOR:
   - What value is returned (from register variable or calculated from state)
   - Side effects of reading (flag clearing, unlocking access)
   - Special read sequences (e.g., "ADCL must be read before ADCH")
   - State dependencies (e.g., "returns 0 if peripheral disabled")
   
   WRITE BEHAVIOR:
   - For EACH bit field: what happens when written
   - Trigger conditions (e.g., "writing ADSC=1 starts conversion")
   - Which formulas/calculations are triggered
   - State changes caused
   - Other registers affected
   - Special behaviors (write-1-to-clear, self-clearing, write-once)

2. INTERNAL STATE VARIABLES:
   - What state must be tracked beyond register values
   - Examples: conversion_in_progress, selected_channel, current_mode
   - Data types and initial values
   - Which register writes update these variables
   - Which operations use these variables

3. CALCULATIONS/FORMULAS:
   - ALL mathematical formulas with exact syntax
   - When each formula is executed (trigger condition)
   - Input sources (registers, ports, parameters)
   - Output destinations (which registers store results)
   - Execution time/delays

4. EXTERNAL PORTS:
   - Input ports (e.g., ADC channels reading analog voltages)
   - Output ports (e.g., interrupt pins)
   - Data types and counts
   - Which operations access these ports

5. CONFIGURATION PARAMETERS:
   - Parameters set at initialization (e.g., voltage references, IRQ pin numbers)
   - Data types and default values
   - Where each parameter is used

6. OPERATIONAL MODES:
   - Different operating modes (e.g., single conversion, free-running, auto-trigger)
   - How to enter/exit each mode (register bit settings)
   - Behavior in each mode

7. INTERRUPTS:
   - Interrupt conditions (exact boolean expressions)
   - Flag and enable bits
   - How interrupts are cleared
   - IRQ pin/vector information

8. TIMING:
   - Operation durations in clock cycles or time units
   - Settling times, conversion times
   - When delays occur

9. DATA FLOW:
   - Trace data paths: input → processing → output
   - Example: "analog voltage → channel[mux] → ADC formula → ADCL/ADCH"

10. DEPENDENCIES & SPECIAL CASES:
    - Register access sequences and locking
    - Bit interdependencies
    - Edge cases and special behaviors

EXTRACTION GUIDELINES:
- Think like you're writing the Read() and Write() switch-case statements
- Extract cause-and-effect: "When X is written, do Y"
- Be specific about bit positions and values
- Include exact formulas with variable definitions
- Note timing for operations that take multiple cycles
- Identify all state that must persist between register accesses
- Capture register-to-register dependencies
- Extract boolean conditions exactly as specified

EXAMPLE THOUGHT PROCESS:
For ADCSRA register write:
- If ADEN bit (bit 7) is set → enable ADC, set internal aden_flag
- If ADSC bit (bit 6) is set AND ADEN=1 → start conversion:
  * Read channel from ADMUX.MUX bits
  * Read reference from ADMUX.REFS bits
  * Execute formula: ADC = (V_IN * 1023) / V_REF
  * Store result in ADCL/ADCH based on ADMUX.ADLAR
  * Set ADIF flag after 13 clock cycles
  * If ADIE=1, trigger interrupt on irq_pin
  * Clear ADSC bit (self-clearing)

Extract information at this level of detail for ALL registers and operations.
"""


# ============================================================================
# SCHEMA REGISTRY
# ============================================================================

SCHEMA_OPTIONS = {
    "Detailed Peripheral (Full)": {
        "schema": PeripheralDataDetailed,
        "prompt": PROMPT_DETAILED,
        "description": "Complete extraction with registers, operations, formulas, state machines, and interrupts"
    },
    "Simple Registers Only": {
        "schema": PeripheralDataSimple,
        "prompt": PROMPT_SIMPLE,
        "description": "Focused on register definitions and bit fields only"
    },
    "Operations Focused": {
        "schema": PeripheralDataOperations,
        "prompt": PROMPT_OPERATIONS,
        "description": "Focused on operational procedures and workflows"
    },
    "SystemC Model Generation": {
        "schema": PeripheralDataSystemC,
        "prompt": PROMPT_SYSTEMC,
        "description": "Optimized for SystemC Read/Write implementation with state, ports, formulas, and timing"
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
