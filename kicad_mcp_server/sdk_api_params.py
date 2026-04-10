from typing_extensions import TypedDict, List
from enum import Enum

class API_QUERY_RESULT( TypedDict):
    """
    Query Kicad result structure
    Field description:
    status: str, Status of the query operation (e.g., "ok", "error")
    msg: str, Message accompanying the query result (e.g., success message, error description)
    """
    status : str
    msg : str

class API_POINT_PARAMS( TypedDict ):
    """
    unit is millimeter
    Coordinate point parameter structure (strong type constraint)
    Field description:
    - x: float, X-axis value of the coordinate point (schematic coordinate system, unit is millimeter, consistent with KiCad configuration)
    - y: float, Y-axis value of the coordinate point (unit is millimeter, consistent with KiCad configuration)
    """
    x : float
    y : float

class API_SIZE_PARAMS( TypedDict):
    """
    Data structure for size parameters in PCB/EDA API requests.
    
    This TypedDict defines the 2D dimensional parameters (X/Y axes) used to specify
    physical dimensions of PCB elements (e.g., pads, footprints, copper areas) in EDA systems.
    Values are typically in millimeters (mm)  as per PCB design standards.
    
    Attributes:
        x: The size/coordinate value along the X-axis (horizontal dimension) in physical units
        y: The size/coordinate value along the Y-axis (vertical dimension) in physical units
    """
    x: float  # X-axis dimension/size value (mm)
    y: float  # Y-axis dimension/size value (mm)

class API_LINE_PARAMS( TypedDict):
    """
    unit is millimeter
    Single schematic wire drawing parameter structure (strong type constraint)
    Field description:
    - start: API_POINT_PARAMS, start coordinate of the wire
    - end: API_POINT_PARAMS, end coordinate of the wire
    """
    start : API_POINT_PARAMS
    end : API_POINT_PARAMS

class API_MULTI_LINES_PARAMS( TypedDict ):
    """
    unit is millimeter
    Batch schematic wires drawing parameter structure (strong type constraint)
    Field description:
    - lines: List[API_LINE_PARAMS], a list of single wire drawing parameters 
             used to batch draw multiple wires on the KiCad schematic. Each element 
             in the list represents a single wire's start/end coordinates, 
             following the definition of API_LINE_PARAMS.
    """
    lines : List[API_LINE_PARAMS]

class API_CIRCLE_PARAMS( TypedDict):
    """
    unit is millimeter
    Circle parameter structure (strong type constraint)
    Field description:
    - center: API_POINT_PARAMS, Center coordinate point of the circle (schematic coordinate system, unit is millimeter, consistent with KiCad configuration)
    - radius: float, Radius value of the circle (unit is millimeter, consistent with KiCad configuration)
    """
    center : API_POINT_PARAMS
    radius : float

class API_ARC_PARAMS( TypedDict):
    """
    Arc parameter structure (strong type constraint)
    Field description:
    - start: API_POINT_PARAMS, Start coordinate point of the arc (schematic coordinate system, unit is millimeter, consistent with KiCad configuration)
    - end: API_POINT_PARAMS, End coordinate point of the arc (schematic coordinate system, unit is millimeter, consistent with KiCad configuration)
    - center: API_POINT_PARAMS (optional), Center coordinate point of the arc (unit is millimeter, consistent with KiCad configuration); 
      Not required in the schematic module, but **must be specified** in the PCB module.
    """
    start : API_POINT_PARAMS
    end : API_POINT_PARAMS
    center : API_POINT_PARAMS

class API_BEZIER_PARAMS( TypedDict):
    """
    Bezier curve parameter structure (strong type constraint)
    Field description:
    - start: API_POINT_PARAMS, Start coordinate point of the Bezier curve (schematic coordinate system, unit is millimeter, consistent with KiCad configuration)
    - c1: API_POINT_PARAMS, First control point of the Bezier curve (schematic coordinate system, unit is millimeter, consistent with KiCad configuration)
    - c2: API_POINT_PARAMS, Second control point of the Bezier curve (schematic coordinate system, unit is millimeter, consistent with KiCad configuration)
    - end: API_POINT_PARAMS, End coordinate point of the Bezier curve (schematic coordinate system, unit is millimeter, consistent with KiCad configuration)
    """
    start : API_POINT_PARAMS
    c1 : API_POINT_PARAMS
    c2 : API_POINT_PARAMS
    end : API_POINT_PARAMS

class API_RECTANGLE_PARAMS( TypedDict):
    """
    Rectangle parameter structure (strong type constraint)
    Field description:
    - top_left: API_POINT_PARAMS, Top-left corner coordinate point of the rectangle (schematic coordinate system, unit is millimeter, consistent with KiCad configuration)
    - width: float, Width value of the rectangle (unit is millimeter, consistent with KiCad configuration, positive value represents rightward extension)
    - height: float, Height value of the rectangle (unit is millimeter, consistent with KiCad configuration, positive value represents downward extension)
    """
    top_left : API_POINT_PARAMS
    width : float
    height : float

class API_TEXTBOX_PARAMS( TypedDict):
    """
    Rectangle parameter structure (strong type constraint)
    Field description:
    - top_left: API_POINT_PARAMS, Top-left corner coordinate point of the rectangle (schematic coordinate system, unit is millimeter, consistent with KiCad configuration)
    - width: float, Width value of the rectangle (unit is millimeter, consistent with KiCad configuration, positive value represents rightward extension)
    - height: float, Height value of the rectangle (unit is millimeter, consistent with KiCad configuration, positive value represents downward extension)
    """
    box : API_RECTANGLE_PARAMS
    text : str

class API_TABLE_PARAMS( TypedDict):
    """
    Table parameter structure (strong type constraint)
    Field description:
    - pos: API_POINT_PARAMS, Top-left corner coordinate point of the table (schematic coordinate system, unit is millimeter, consistent with KiCad configuration; baseline position of table rendering)
    - rows: int, Number of rows in the table (positive integer, minimum value is 1, representing valid table row count)
    - cols: int, Number of columns in the table (positive integer, minimum value is 1, representing valid table column count)
    """
    pos : API_POINT_PARAMS
    rows : int
    cols : int

class API_HIER_SHEET_PARAMS( TypedDict):
    """
    KiCad hierarchical sheet parameter structure (strong type constraint)
    Hierarchical sheet is a core element in KiCad schematic for organizing multi-level circuit design.
    Field description:
    - box: API_RECTANGLE_PARAMS, Bounding rectangle of the hierarchical sheet (schematic coordinate system, unit is millimeter, consistent with KiCad configuration; defines the position and size of the hierarchical sheet in the schematic)
    - title: str, Title text of the hierarchical sheet (displayed on the top of the sheet in KiCad, usually used to identify the function of the sub-circuit corresponding to the sheet)
    """
    box : API_RECTANGLE_PARAMS
    title : str

class API_LABEL_PARAMS( TypedDict):
    """
    KiCad label parameter structure (strong type constraint)
    Label is a core text element in KiCad schematic/PCB, used for net labeling, component annotation, or positional marking.
    Field description:
    - position: API_POINT_PARAMS, Anchor coordinate point of the label (schematic/PCB coordinate system, unit is millimeter, consistent with KiCad configuration; the label text is rendered around this anchor point)
    - text: str, Content of the label (supports ASCII characters and KiCad-compatible Chinese characters; for net labels, follow KiCad's net naming rules to ensure circuit connectivity)
    """
    position : API_POINT_PARAMS
    text : str

class API_CLASS_LABEL_PARAMS( TypedDict):
    """
    KiCad Class Label parameter structure (strong type constraint)
    Class Label is a special label in KiCad for classifying nets/components, used to manage design rules, optimize layout/routing, and improve design standardization.
    Field description:
    - position: API_POINT_PARAMS, Anchor coordinate point of the class label (schematic/PCB coordinate system, unit is millimeter, consistent with KiCad configuration; the label is rendered around this anchor point)
    - net_class: str, Name of the KiCad net class (naming rules: alphanumeric + underscores, no spaces/special chars; default net classes: "Default", "Power", "GND", "HighSpeed"; custom net classes like "USB_2.0", "DDR4", "CAN_BUS")
                  Usage scenario: Bind nets to specific classes to apply unified design rules (e.g., trace width, clearance, impedance control for HighSpeed net class)
    - component_class: str, Name of the KiCad component class (naming rules: alphanumeric + underscores, no spaces/special chars; default classes: empty (unclassified), custom classes like "MCU", "POWER_IC", "CONNECTOR", "PASSIVE")
                  Usage scenario: Group components by function to batch modify attributes (e.g., assign footprint libraries, set placement zones, filter components in BOM/selection)
    """
    position : API_POINT_PARAMS
    net_class : str
    component_class : str

class API_SYMBOL_PIN_LABEL( TypedDict):
    """
    KiCad Symbol Pin Label parameter structure (strong type constraint)
    Symbol Pin Label is a core element in KiCad schematic for marking attribute information of component pins, directly associated with the pin definition of schematic symbols (e.g., resistor, MCU, IC).
    Field description:
    - reference: str, Reference designator of the component corresponding to the pin (naming rules: KiCad standard reference prefix + serial number, e.g., "R1", "U5", "C12", "J3"; prefix rules: R=Resistor, U=IC/MCU, C=Capacitor, J=Connector, D=Diode, L=Inductor)
                  Function: Bind the pin label to a specific component, the core identifier for distinguishing pins of different components in the schematic
    - pin_number: str, Physical pin number of the component (naming rules: consistent with the component datasheet, supports numeric (e.g., "1", "28"), alphanumeric (e.g., "A1", "B10"), or special format (e.g., "VDD", "GND") defined by the datasheet)
                  Function: Map the pin label to the actual physical pin of the component, the key link between schematic pin and physical device pin (critical for PCB footprint matching and wiring)
    - label_text: str, Functional label text of the pin (naming rules: follow component datasheet or circuit design norms, supports ASCII/Chinese characters, e.g., "VCC", "GND", "GPIO_0", "TXD", "SDA", "RESET")
                  Function: Describe the functional purpose of the pin (e.g., power supply, signal input/output, control), the core for engineers to understand pin function in schematic design
    """
    reference : str
    pin_number : str
    label_text : str

class API_QUERY_SYMBOL( TypedDict):
    """
    Query symbol parameter structure
    Field description:
    - reference: str, Reference designator of the symbol to query
    """
    reference : str

class API_SYMBOL_LIBRARY( TypedDict):
    """
    Query symbol library parameter structure
    Field description:
    - symbol_library_name: str, Name of the symbol library to query
    """
    symbol_library_name : str

class API_SYMBOL_LIBARARY_LIST( TypedDict):
    """
    Query symbol library list parameter structure
    Field description:
    - symbol_library_list: List[API_SYMBOL_LIBRARY], List of symbol libraries to query
    """
    library_list : List[API_SYMBOL_LIBRARY]


class API_SYMBOL_CATEGORY( str, Enum):
    """
    Enumeration of EDA symbol categories (aligned with KiCad/Multisim/Altium component classification)
    This enum defines standardized category identifiers for common electronic components,
    used to specify the type of symbol to place in KiCad schematic/PCB design.
    
    Enum Value Definitions:
    -----------------------
    RESISTOR: Passive component - Fixed resistor (e.g., through-hole/SMD resistor)
    CAPACITOR: Passive component - Capacitor (non-polarized, e.g., ceramic capacitor)
    INDUCTOR: Passive component - Inductor (including air-core/iron-core inductors)
    POTENTIOMETER: Passive component - Variable resistor/potentiometer (adjustable resistance)
    CRYSTAL_OSCILLATOR: Passive component - Crystal oscillator (frequency reference component)
    TRANSFORMER: Passive component - Transformer (AC voltage/current conversion)
    FUSE: Protective component - Electrical fuse (overcurrent protection)
    FERRITE_BEAD: Passive component - Ferrite bead (EMI/RFI suppression)
    POWER_DC: Power component - DC power source (direct current supply)
    POWER_AC: Power component - AC power source (alternating current supply)
    DIODE: Semiconductor - General-purpose diode (rectification/switching)
    ZENER_DIODE: Semiconductor - Zener diode (voltage regulation)
    SCHOTTKY_DIODE: Semiconductor - Schottky diode (low forward voltage, fast switching)
    VARACTOR_DIODE: Semiconductor - Varactor diode (voltage-controlled capacitance)
    LED: Semiconductor - Light-emitting diode (visible/invisible light emission)
    PHOTODIODE: Semiconductor - Photodiode (light-to-electrical signal conversion)
    TRANSISTOR_NPN: Semiconductor - NPN bipolar transistor (amplification/switching)
    TRANSISTOR_PNP: Semiconductor - PNP bipolar transistor (amplification/switching)
    MOSFET_N_CHANNEL: Semiconductor - N-channel MOSFET (field-effect transistor)
    MOSFET_P_CHANNEL: Semiconductor - P-channel MOSFET (field-effect transistor)
    JFET_N_CHANNEL: Semiconductor - N-channel JFET (junction field-effect transistor)
    JFET_P_CHANNEL: Semiconductor - P-channel JFET (junction field-effect transistor)
    IGBT: Semiconductor - Insulated-gate bipolar transistor (high-power switching)
    THYRISTOR: Semiconductor - Thyristor/SCR (silicon-controlled rectifier)
    TRIAC: Semiconductor - Triac (bidirectional thyristor for AC control)
    OPERATIONAL_AMPLIFIER: Active component - Op-amp (analog signal amplification)
    GROUND: Power component - Electrical ground (reference potential point)
    BUTTON: Electromechanical - Push button switch (momentary contact)
    BUZZER: Electromechanical - Buzzer (audio signaling component)
    SPEAKER: Electromechanical - Loudspeaker (audio output device)
    MOTOR: Electromechanical - Electric motor (electrical-to-mechanical energy conversion)
    """
    RESISTOR = "RESISTOR"
    CAPACITOR = "CAPACITOR"
    INDUCTOR = "INDUCTOR"
    POTENTIOMETER = "POTENTIOMETER"
    CRYSTAL_OSCILLATOR = "CRYSTAL_OSCILLATOR"
    TRANSFORMER = "TRANSFORMER"
    FUSE = "FUSE"
    FERRITE_BEAD = "FERRITE_BEAD"
    POWER_DC = "POWER_DC"
    GROUND = "GROUND"
    POWER_AC = "POWER_AC"
    DIODE = "DIODE"
    ZENER_DIODE = "ZENER_DIODE"
    SCHOTTKY_DIODE = "SCHOTTKY_DIODE"
    VARACTOR_DIODE = "VARACTOR_DIODE"
    LED = "LED"
    PHOTODIODE = "PHOTODIODE"
    TRANSISTOR_NPN = "TRANSISTOR_NPN"
    TRANSISTOR_PNP = "TRANSISTOR_PNP"
    MOSFET_N_CHANNEL = "MOSFET_N_CHANNEL"
    MOSFET_P_CHANNEL = "MOSFET_P_CHANNEL"
    JFET_N_CHANNEL = "JFET_N_CHANNEL"
    JFET_P_CHANNEL = "JFET_P_CHANNEL"
    IGBT = "IGBT"
    THYRISTOR = "THYRISTOR"
    TRIAC = "TRIAC"
    OPERATIONAL_AMPLIFIER = "OPERATIONAL_AMPLIFIER"
    BUTTON = "BUTTON"
    BUZZER = "BUZZER"
    SPEAKER = "SPEAKER"
    MOTOR = "MOTOR"

class API_PLACE_SYMBOL(TypedDict):
    """
    Parameter structure for placing electronic symbols in KiCad schematic
    
    This TypedDict defines the complete set of parameters required to place a component symbol
    in KiCad, including category identification, component value, positional coordinates,
    and reference designator (following KiCad's standard naming conventions).
    
    Field Description:
    ------------------
    category : API_SYMBOL_CATEGORY
        Standardized category of the symbol to place (e.g., "RESISTOR", "POWER_DC", "MOSFET_N_CHANNEL").
        Must be a valid enum member from API_SYMBOL_CATEGORY to ensure type safety.
    value : str
        Physical/electrical value of the component (e.g., "100K" for 100kΩ resistor, "0.1uF" for capacitor,
        "12V" for DC power source, "SMD_0805" for package type).
    position : API_POINT_PARAMS
        Anchor coordinate point for symbol placement (KiCad schematic/PCB coordinate system, unit: millimeter).
        The symbol is rendered centered/aligned around this anchor point per KiCad's default placement rules.
    reference : str
        Unique reference designator for the component (follows KiCad standard naming rules):
        - Prefix rules: R=Resistor, C=Capacitor, L=Inductor, D=Diode, U=IC/MCU/Op-amp,
          J=Connector, Q=Transistor/MOSFET, X=Crystal, T=Transformer, F=Fuse, SW=Switch.
        - Format example: "R1" (Resistor 1), "U5" (IC 5), "C12" (Capacitor 12), "Q3" (Transistor 3).
        Must be unique within the schematic/PCB to avoid KiCad validation errors.
    """
    category : API_SYMBOL_CATEGORY
    value : str
    position : API_POINT_PARAMS
    reference : str

class API_MOVE_SYMBOL( TypedDict):
    """
    Parameter structure for moving a placed symbol in KiCad schematic/PCB (via MCP/CPP SDK)
    
    This TypedDict defines the complete set of parameters required to reposition an existing
    electronic component symbol in KiCad, supporting precise offset-based movement relative to
    the symbol's current position (or absolute positioning via offset calibration).
    It adheres to KiCad's symbol reference/unit naming conventions for multi-unit components.

    Field Description:
    ------------------
    reference : str
        Unique reference designator of the symbol to move (follows KiCad standard naming rules):
        - Prefix rules: R=Resistor, C=Capacitor, U=IC/MCU, D=Diode, Q=Transistor, J=Connector, etc.
        - Format example: "R1", "U5", "C12", "J3", "Q2" (must exist in the active KiCad document)
    unit : str
        Unit identifier for multi-unit symbols (e.g., ICs with multiple functional blocks):
        - Default value: "" (automatically used if the parameter is omitted, empty string, or null)
    offset : API_POINT_PARAMS
        Relative offset coordinates for symbol movement (KiCad schematic/PCB coordinate system, unit: millimeter):
        - Positive x: Move symbol to the right (east)
        - Negative x: Move symbol to the left (west)
        - Positive y: Move symbol up (north)
        - Negative y: Move symbol down (south)
        - For absolute positioning: Calculate offset as (target_x - current_x, target_y - current_y)
        - Example: {"x": 5.0, "y": -2.5} → Move symbol 5mm right and 2.5mm down
    """
    reference : str
    unit : str
    offset : API_POINT_PARAMS


class API_ROTATE_SYMBOL( TypedDict):
    """
    Parameter structure for rotating a placed symbol in KiCad schematic/PCB (via MCP/CPP SDK)
    
    This TypedDict defines the parameters required to rotate an existing electronic component symbol
    in KiCad by a fixed 90-degree increment, with control over rotation direction (clockwise/counterclockwise).
    It adheres to KiCad's symbol reference/unit naming conventions and native rotation behavior.

    Field Description:
    ------------------
    reference : str
        Unique reference designator of the symbol to rotate (follows KiCad standard naming rules):
        - Prefix rules: R=Resistor, C=Capacitor, U=IC/MCU, D=Diode, Q=Transistor, J=Connector, etc.
        - Format example: "R1", "U5", "C12", "J3", "Q2" (must exist in the active KiCad document)
    unit : str
        Unit identifier for multi-unit symbols (e.g., ICs with multiple functional blocks/op-amps):
        - Default value: Empty string ("") (automatically used if the parameter is omitted or set to empty)
        - For single-unit symbols: Use empty string ("") (KiCad's native default for single-unit components)
        - For multi-unit symbols: Use "1", "2", "3", etc. (matches KiCad's unit numbering for multi-channel devices)
        - Example: "2" for rotating the second unit of a dual-opamp (U1.2); empty string targets the default unit
    ccw : bool
        Rotation direction control (fixed 90-degree increment per rotation):
        - True: Rotate symbol 90 degrees COUNTERCLOCKWISE (CCW, anti-clockwise) around its anchor point
        - False: Rotate symbol 90 degrees CLOCKWISE (CW) around its anchor point
        - KiCad native behavior: Rotation is centered on the symbol's anchor (origin) point (consistent with placement anchor)
    """
    reference : str
    unit : str
    ccw : bool

class API_MODIFY_SYMBOL_VALUE(TypedDict):
    """
    Parameter structure for modifying the value of a placed symbol in KiCad schematic/PCB (via MCP/CPP SDK)
    
    This TypedDict defines the complete set of parameters required to update the physical/electrical value
    of an existing electronic component symbol in KiCad. It enforces KiCad's standard value formatting rules
    and ensures type safety for critical fields (reference designator and component value).
    The modification applies to the active KiCad schematic/PCB document and is validated by the KiCad CPP SDK.

    Field Description:
    ------------------
    reference : str
        Unique reference designator of the symbol to modify (follows KiCad's industry-standard naming rules):
        - Prefix rules (mandatory for KiCad validation):
          R=Resistor, C=Capacitor, L=Inductor, D=Diode, Q=Transistor/MOSFET, U=IC/MCU/Op-amp,
          J=Connector, X=Crystal/Oscillator, T=Transformer, F=Fuse, SW=Switch, LED=Light-emitting diode
        - Format example: "R1", "C12", "U5", "Q3", "LED7" (must exist in the active KiCad document)
        - Validation: The reference must be unique (no duplicate designators) and match an existing symbol.
    
    value : str
        New physical/electrical value to assign to the target symbol (follows KiCad's value format conventions):
        - Resistors: "100K" (100 kiloohms), "4.7M" (4.7 megaohms), "0Ω" (zero-ohm resistor), "100R±1%" (tolerance)
        - Capacitors: "0.1uF" (0.1 microfarad), "100nF" (100 nanofarad), "22pF" (22 picofarad), "10µF/16V" (voltage rating)
        - Inductors: "100uH" (100 microhenry), "1mH" (1 millihenry), "47nH" (47 nanohenry)
        - ICs/MCU: "STM32F103C8T6" (part number), "ATmega328P" (chip identifier)
        - Passive components: "SMD_0805" (package type, if value is package-specific)
        - General rule: Use KiCad's native unit abbreviations (R=ohm, F=farad, H=henry) to ensure compatibility.
    """
    reference : str
    value : str

class API_MODIFY_SYMBOL_REFERENCE(TypedDict):
    """
    Parameter structure for modifying the reference designator of a placed symbol in KiCad schematic/PCB (via MCP/CPP SDK)
    
    This TypedDict defines the parameters required to rename the unique reference designator of an existing
    electronic component symbol in KiCad. It enforces KiCad's industry-standard reference naming rules to
    ensure compatibility with the KiCad CPP SDK and avoid validation errors (e.g., duplicate designators, invalid prefixes).
    The modification updates the core identifier of the symbol in the active KiCad schematic/PCB document.

    Field Description:
    ------------------
    old_reference : str
        Current/old reference designator of the symbol to rename (must exist in the active KiCad document):
        - Must follow KiCad's existing reference format (prefix + numeric suffix):
          R=Resistor, C=Capacitor, L=Inductor, D=Diode, Q=Transistor/MOSFET, U=IC/MCU/Op-amp,
          J=Connector, X=Crystal/Oscillator, T=Transformer, F=Fuse, SW=Switch, LED=Light-emitting diode
        - Format example: "R1", "C12", "U5", "Q3", "LED7" (case-sensitive for KiCad SDK validation)
        - Validation: The old reference must map to an existing symbol (SDK returns error if not found).
    
    new_reference : str
        New/desired reference designator to assign to the symbol (compliant with KiCad's naming rules):
        - Mandatory prefix rules (enforced by KiCad):
          - Prefix must match the component type (e.g., "R" for resistors, "U" for ICs — cannot rename R1 to U1 unless component type changes)
          - Numeric suffix must be unique (no duplicate designators in the same document, e.g., "R1" cannot be assigned to two resistors)
        - Format example: "R2", "C15", "U8", "LED9" (prefix + integer suffix; no special characters except underscores for multi-unit symbols: "U5_2")
        - Additional rules:
          - No whitespace or special characters (except underscore for multi-unit symbols: "U5.2" → "U5_2" for SDK compatibility)
          - Case-sensitive in KiCad SDK (e.g., "R1" ≠ "r1" — use uppercase prefixes per KiCad convention)
    """
    old_reference : str
    new_reference : str


class API_CREATE_SYMBOL_LIBARARY(TypedDict):
    """
    Parameter structure for creating a local project-specific symbol library in KiCad (via MCP/CPP SDK)
    
    This TypedDict defines the single required parameter to initialize a new, project-scoped symbol library
    in the active KiCad project. The library is created locally (tied to the project directory, not global KiCad libraries)
    and is empty by default — symbols can be added to it via subsequent KiCad SDK calls (e.g., placeSymbol).
    This aligns with KiCad's native library management workflow (project-specific libs vs global system libs).

    Field Description:
    ------------------
    symbol_library_name : str
        Name of the local project symbol library to create (KiCad-compatible naming rules apply):
    """
    symbol_library_name : str

class API_CREATE_LIB_SYMBOL_PIN(TypedDict):
    """
    Parameter structure for creating a pin in a KiCad symbol library (via MCP/CPP SDK).
    
    This TypedDict defines all mandatory parameters required to add a new pin to a symbol in a KiCad project-specific
    symbol library (created via `create_symbol_library`). The pin configuration adheres to KiCad's symbol editor
    standards for pin naming, positioning, electrical behavior, and graphical representation.
    All parameters are required (no defaults) to ensure valid pin creation in the KiCad Symbol Editor context.

    Field Description:
    ------------------
    pin_name : str
        Human-readable name of the pin (displayed on the KiCad schematic symbol):
    
    pin_number : str
        Numeric/alpha-numeric identifier for the pin (matches physical component pinout):

    
    position : API_POINT_PARAMS

    
    """
    pin_name : str
    pin_number : str
    position : API_POINT_PARAMS


class API_PCB_LAYER_NAME( TypedDict):
    """
    Data structure for representing a single PCB layer name in EDA systems (e.g., KiCad).
    
    This TypedDict defines the field for storing the unique identifier/name of a single PCB layer,
    which is used to reference specific layers in PCB design operations (e.g., placing pads, routing traces,
    assigning copper areas). Layer names follow EDA tool conventions (e.g., "F.Cu", "B.SilkS", "Edge.Cuts").
    
    Attributes:
        pcb_layer_name: Unique name/identifier of a single PCB layer (conforms to KiCad/EDA layer naming standards)
                        Examples: "F.Cu" (Front Copper), "B.SilkS" (Back Silkscreen), "Edge.Cuts" (Board Outline)
    """
    pcb_layer_name : str

class API_PCB_LAYER_NAME_LIST( TypedDict):
    """
    Data structure for representing a list of PCB layer names in EDA systems (e.g., KiCad).
    
    This TypedDict defines a field for storing a collection of PCB layer names, typically used in API requests
    that involve multi-layer operations (e.g., copying pads across layers, checking layer visibility,
    assigning pads to multiple layers). Each element in the list follows the API_PCB_LAYER_NAME structure.
    
    Attributes:
        pcb_layer_name_list: List of API_PCB_LAYER_NAME objects, each representing a single PCB layer name
                             Used for batch operations on multiple PCB layers (supports 0+ layer entries)
    """
    pcb_layer_name_list : List[API_PCB_LAYER_NAME]



class API_PCB_TRACK_PARAMS(TypedDict):
    """
    MCP data structure interface for PCB track (copper trace) parameters
    This structure is used to define the basic attributes of a PCB track in KiCad MCP communication.
    - start: (required) - Start coordinate point of the PCB track...
    - end : (required) - End coordinate point of the PCB track...
    - layer_name : (optional) - Name of the PCB layer where the track is placed...
    """
    start : API_POINT_PARAMS
    end : API_POINT_PARAMS
    layer_name : API_PCB_LAYER_NAME

class API_PCB_VIA_TYPE(str, Enum):
    """
    Enumeration of KiCad PCB via types for MCP API communication.
    Defines the standard via types supported by KiCad's PCBnew module, 
    aligned with industry-standard PCB manufacturing specifications.
    """
    THROUGH = "THROUGH"
    """Through-hole via (standard via) - Connects all copper layers of the PCB.
       Passes completely through the board, the most common and manufacturable via type.
    """

    BLIND_BURIED = "BLIND_BURIED"
    """Blind/Buried via - Blind vias connect an outer layer to one or more inner layers;
       Buried vias connect only inner layers (no exposure on outer layers).
       Requires advanced PCB manufacturing processes (sequential lamination).
    """

    MICROVIA = "MICROVIA"
    """Microvia - Small-sized via (typically <0.2mm diameter) that connects an outer layer
       to the adjacent inner layer only. Used for high-density/high-frequency PCBs (e.g., HDI boards).
    """

    NOT_DEFINED = "NOT_DEFINED"
    """Undefined via type - Default value for unassigned or unspecified via types.
       Indicates the via type has not been set or is invalid in the current context.
    """

class API_PCB_LAYER_ID( str, Enum):
    """
    KiCad PCB layer identifier enumeration (string-based enum for MCP API compatibility)
    Aligned with KiCad's native PCB_LAYER_ID enum (C++), maps layer names to string values 
    (consistent with MCP API parameter format).
    Integer ID reference (for internal KiCad SDK interaction):
    - Special layers: -1 (UNDEFINED), -2 (UNSELECTED)
    - Copper layers: 0 (F_Cu), 2 (B_Cu), 4-62 (Inner Cu layers, step=2)
    - Non-copper layers: 1 (F_Mask), 3 (B_Mask), 5 (F_SilkS), etc.
    """
    UNDEFINED_LAYER = "UNDEFINED_LAYER"    # -1: Undefined/invalid layer (unassigned objects)
    UNSELECTED_LAYER = "UNSELECTED_LAYER"  # -2: Placeholder for unselected layer in UI

    # Copper layers (conductive, for electrical tracks/vias)
    F_Cu = "F_Cu"                          # 0: Front Copper (top signal layer)
    B_Cu = "B_Cu"                          # 2: Back Copper (bottom signal layer)


class API_PCB_VIA_PARAMS( TypedDict ):
    """
    Typed dictionary for defining PCB via parameters in KiCad MCP API calls.
    This structure encapsulates all required attributes to create a via in KiCad's PCBnew module,
    aligned with KiCad's via creation logic and manufacturing constraints.
    """
    position : API_POINT_PARAMS
    """API_POINT_PARAMS (required) - Exact position of the via's center point in the PCB coordinate system.
       Coordinates use millimeter as unit (consistent with KiCad's default unit), origin at bottom-left of the board.
    """

    via_type : API_PCB_VIA_TYPE
    """API_PCB_VIA_TYPE (required) - Type of the PCB via (through-hole, blind/buried, microvia).
       Determines the manufacturing process and layer connection rules (e.g., microvia only connects adjacent layers).
    """

    start_layer : API_PCB_LAYER_ID
    """API_PCB_LAYER_ID (required) - Starting copper layer of the via (the outermost layer the via connects from).
       Must be a valid conductive copper layer (F_Cu, B_Cu, InX_Cu), not non-conductive layers (e.g., F_SilkS).
    """

    end_layer : API_PCB_LAYER_ID
    """API_PCB_LAYER_ID (required) - Ending copper layer of the via (the outermost layer the via connects to).
       For through-hole vias: must be F_Cu (start) and B_Cu (end) (or vice versa).
       For blind/buried vias: must be a subset of copper layers (e.g., F_Cu to In1_Cu for blind via).
       For microvias: must be adjacent copper layers (e.g., F_Cu to In1_Cu).
    """


class API_PCB_PAD_PARAMS( TypedDict):
    """
    Typed dictionary for defining PCB pad parameters in KiCad MCP API calls.
    This structure encapsulates the core attributes required to place a conductive pad on a PCB,
    aligned with KiCad's PCBnew module pad creation logic and industry PCB design standards.
    - position : API_POINT_PARAMS (required) - Exact center position of the PCB pad in the PCB coordinate system.
                Coordinates use millimeter as the unit (consistent with KiCad's default unit), with the origin at the bottom-left of the board.
                This position determines where the pad is placed on the PCB relative to other components/tracks.

    - number : Unique identifier (pad number) for the PCB pad, typically corresponding to component pin numbers.
                Follows KiCad's pad numbering convention (e.g., "1", "2", "A1", "Pin_12") and must be non-empty.
                This number is used to map the pad to the component's schematic symbol and netlist connections.
    """
    position : API_POINT_PARAMS
    number : str

class API_MOVE_PCB_PAD_PARAMS( TypedDict):
    """
    Typed dictionary for defining parameters to move an existing PCB pad in KiCad MCP API calls.
    This structure encapsulates the core attributes required to translate (move) a conductive PCB pad
    from its current position by a specified offset, aligned with KiCad's PCBnew module pad manipulation logic.
    - offset : API_POINT_PARAMS (required) - Translation offset (delta X/Y) for moving the PCB pad.
       Values represent the distance to move the pad along the X and Y axes (unit: millimeter, consistent with KiCad's PCB coordinate system).
       Positive values move the pad right/up; negative values move it left/down (relative to KiCad's bottom-left origin).
    - number : "str (required) - Unique identifier (pad number) of the target PCB pad to be moved.
       Must match the pad number assigned during pad creation (e.g., "1", "A2", "Pin_15") and exist in the current PCB design.
       This field is used to uniquely locate the target pad in KiCad's PCB database.
    """
    offset : API_POINT_PARAMS
    number : str


class API_ROTATE_PCB_PAD( TypedDict):
    """
    Typed dictionary for defining parameters to rotate an existing PCB pad in KiCad MCP API calls.
    This structure encapsulates the core attributes required to rotate a conductive PCB pad around its center point
    by a specified angle, aligned with KiCad's PCBnew module pad rotation logic and industry PCB design standards.
    - number : str (required) - Unique identifier (pad number) of the target PCB pad to be rotated.
       Must match the pad number assigned during pad creation (e.g., "1", "A2", "Pin_15") and exist in the current PCB design.
       This field is used to uniquely locate the target pad in KiCad's PCB database for rotation operation.
    - degree : float (required) - Rotation angle in degrees for the target PCB pad (unit: degree).
       Follows KiCad's rotation convention: positive values = counterclockwise rotation, negative values = clockwise rotation.
       Rotation is performed around the pad's center point (not the PCB origin), consistent with KiCad's native pad rotation behavior.
       Valid range: any numeric value (e.g., 90.0 = 90° counterclockwise, -45.0 = 45° clockwise, 360.0 = full rotation).
    """
    number: str
    degree : float


class API_MODIFY_PAD_NUMBER( TypedDict):
    """
    Data structure for API request to modify PCB footprint pad number.
    
    This TypedDict defines the required payload fields for the API request
    that updates the identification number of a pad in a PCB footprint.
    It is typically used in PCB design/EDA (Electronic Design Automation) systems.
    
    Attributes:
        old_number: The original/ current identification number of the target PCB footprint pad
                    that requires modification (e.g., "1", "A2", "Pin_5")
        new_number: The new identification number to assign to the target PCB footprint pad
                    (must conform to the system's pad numbering rules)
    """
    old_number: str  # Original PCB footprint pad number to be changed
    new_number: str  # New PCB footprint pad number to assign


class API_MODIFY_PAD_SIZE(TypedDict):
    """
    Data structure for API request to modify the physical size of a PCB footprint pad.
    
    This TypedDict defines the required payload fields for the API request that updates
    the 2D physical dimensions of a specific PCB footprint pad in EDA systems (e.g., KiCad).
    It links a target pad (by its identification number) to its new X/Y size parameters.
    
    Attributes:
        number: Unique identification number of the target PCB footprint pad to be modified
                (e.g., "1", "A2", "Pin_5")
        size: 2D size parameters (X/Y axes) to assign to the target pad, defined by API_SIZE_PARAMS
              (units conform to PCB design standard: mm/mil)
    """
    number: str       # Identification number of the target PCB pad
    size: API_SIZE_PARAMS  # New 2D size parameters (X/Y) for the target pad


class API_MODIFY_PAD_DRILL_SIZE( TypedDict):
    """
    Data structure for API request to modify the drill size of a PCB footprint pad.
    
    This TypedDict defines the required payload fields for the API request that updates
    the physical size of the drill hole (plated/non-plated) of a specific through-hole PCB pad
    in EDA systems (e.g., KiCad). For circular drill holes, X and Y values are typically equal;
    for oval/rectangular drill holes, X/Y represent width/height respectively.
    
    Attributes:
        number: Unique identification number of the target through-hole PCB pad to be modified
                (e.g., "1", "A2", "Pin_5")
        size: 2D size parameters (X/Y axes) for the new drill hole size, defined by API_SIZE_PARAMS
              (units conform to PCB design standard: mm; X=Y for circular drills)
    """
    number: str       # Identification number of the target PCB pad (drill to modify)
    size: API_SIZE_PARAMS  # New drill hole size (X/Y) for the target pad (mm)

class API_PAD_DRILL_SHAPE( str, Enum):
    """
    Enumeration of valid drill hole shapes for through-hole PCB pads in EDA systems (e.g., KiCad).
    
    This Enum defines the standard drill hole shape types supported by KiCad and other PCB design tools,
    which directly impact PCB manufacturing processes (e.g., CNC drilling operations).
    
    Values:
        CIRCLE: Circular drill hole (most common type for through-hole pads, X=Y dimensions)
        OBLONG: Oblong/oval drill hole (elliptical shape, X≠Y dimensions for elongated holes)
        UNDEFINED: Default/unspecified drill shape (typically indicates unconfigured pad or invalid state)
    """
    CIRCLE = "CIRCLE"
    OBLONG = "OBLONG"
    UNDEFINED = "UNDEFINED"

class API_MODIFY_PAD_DRILL_SHAPE( TypedDict):
    """
    Data structure for API request to modify the drill hole shape of a through-hole PCB pad.
    
    This TypedDict defines the required payload fields for the API request that updates
    the geometric shape of the drill hole in a specific through-hole PCB footprint pad.
    It links a target pad (by its identification number) to the new drill shape (from API_PAD_DRILL_SHAPE).
    
    Attributes:
        number: Unique identification number of the target through-hole PCB pad to be modified
                (e.g., "1", "A2", "Pin_5")
        shape: New drill hole shape to assign to the target pad (from API_PAD_DRILL_SHAPE Enum)
               Only valid for through-hole pads (SMD pads do not have drill holes)
    """
    number : str
    shape : API_PAD_DRILL_SHAPE

class API_SET_PAD_POSITION( TypedDict):
    """
    Data structure for API request to set the absolute position of a PCB footprint pad.
    
    This TypedDict defines the required payload fields for the API request that updates
    the physical location of a specific PCB footprint pad to a new absolute coordinate on the PCB.
    IMPORTANT: `new_position` represents the absolute X/Y coordinates (relative to PCB origin),
    NOT a relative offset/movement delta from the current pad position.
    
    Attributes:
        number: Unique identification number of the target PCB footprint pad to reposition
                (e.g., "1", "A2", "Pin_5")
        new_position: API_POINT_PARAMS object containing the NEW ABSOLUTE X/Y coordinates
                      to assign to the target pad (relative to PCB origin, units: mm)
                      - This is NOT a relative offset (do not confuse with movement delta)
    """
    number : str
    new_position : API_POINT_PARAMS



class API_PCB_FOOTPRINT_INFO(TypedDict):
    """
    Data structure for representing basic information of a single PCB footprint in EDA systems (e.g., KiCad).
    
    This TypedDict defines the core identification fields for a PCB footprint (physical component outline),
    which is used to reference and manage footprints in PCB design workflows (e.g., placement, modification, query).
    
    Attributes:
        reference: Unique designator/reference of the footprint on the PCB (e.g., "R1", "C5", "U2")
                   This is the label used to identify the component instance in the PCB layout
        fpid: Fully qualified footprint ID in the format "footprint_library_name:footprint_name"
              Combines the footprint library name and the specific footprint name (colon-separated)
              Examples: "Resistor_SMD:R_0805", "Connector_PinHeader:PinHeader_1x04_P2.54mm"
        position: API_POINT_PARAMS object containing the ABSOLUTE X/Y coordinates of the footprint's origin point
                  (typically the footprint's reference pin/center, relative to PCB design origin)
                  Units conform to PCB design standards (mm); NOT a relative offset/movement delta
                  Example: {"x": 15.2, "y": 28.7} = footprint origin at X=15.2mm, Y=28.7mm from PCB origin
    """
    reference: str  # PCB footprint designator/reference (e.g., R1, U2)
    fpid: str       # Footprint ID (format: library_name:footprint_name, e.g., Resistor_SMD:R_0805)
    position : API_POINT_PARAMS # Absolute position (X/Y) of footprint origin (mm/ NOT offset)


class API_PCB_FOOTPRINT_INFO_LIST( TypedDict):
    """
    Data structure for representing a list of PCB footprint information entries in EDA systems (e.g., KiCad).
    
    This TypedDict defines a collection of PCB footprint identification data, typically used in API requests/responses
    for batch operations (e.g., querying all footprints on a PCB, bulk modifying footprint properties).
    Each entry in the list follows the API_PCB_FOOTPRINT_INFO structure.
    
    Attributes:
        footprint_list: List of API_PCB_FOOTPRINT_INFO objects, each representing a single PCB footprint's core info
                        Supports 0+ entries (empty list = no footprints found/selected)
    """
    footprint_list : List[API_PCB_FOOTPRINT_INFO]


class API_PCB_REFERENCE(TypedDict):
    """
    Data structure for representing a single PCB component reference designator in EDA systems (e.g., KiCad).
    
    This TypedDict defines the field for storing a unique reference designator (component label)
    used to identify individual component instances on a PCB. Reference designators follow industry
    standards (IPC-2221) and KiCad conventions (e.g., R for resistors, C for capacitors, U for ICs).
    
    Attributes:
        reference: Unique alphanumeric reference designator of a PCB component (e.g., "R1", "C5", "U2", "J1")
                   This label uniquely identifies a specific component instance in the PCB layout
    """
    reference : str

class API_PCB_REFERENCE_LIST(TypedDict):
    """
    Data structure for representing a list of PCB component reference designators in EDA systems (e.g., KiCad).
    
    This TypedDict defines a collection of PCB component reference designators, typically used in API requests/responses
    for batch operations (e.g., selecting multiple components, bulk modifying footprint properties, querying component info).
    Each entry in the list follows the API_PCB_REFERENCE structure.
    
    Attributes:
        reference_list: List of API_PCB_REFERENCE objects, each representing a single PCB component reference
                        Supports 0+ entries (empty list = no components selected/found)
    """
    reference_list : List[API_PCB_REFERENCE]

class API_MOVE_FOOTPRINT_PARAMS(TypedDict):
    """
    Data structure for API request to move a PCB footprint by a relative offset in EDA systems (e.g., KiCad).
    
    This TypedDict defines the required payload fields for the API request that moves a specific PCB footprint
    from its current position by a specified X/Y relative offset (incremental movement). Unlike absolute position setting,
    this structure uses delta values to adjust the footprint's location (e.g., +5mm in X, -2mm in Y).
    
    Attributes:
        reference: Unique designator/reference of the target PCB footprint to move (e.g., "R1", "C5", "U2")
                   Identifies the specific component instance to be repositioned incrementally
        offset: API_POINT_PARAMS object containing the RELATIVE X/Y offset values for the movement
                Positive values = movement in positive axis direction (right/up); Negative values = left/down
                Units conform to PCB design standards (mm); NOT absolute coordinates
                Example: {"x": 5.0, "y": -2.5} = move footprint 5mm right, 2.5mm down from current position
    """
    reference: str           # Target PCB footprint reference (e.g., R1, U2) to move incrementally
    offset: API_POINT_PARAMS  # Relative movement offset (X/Y, mm) - NOT absolute position


class API_MODIFY_FOOTPRINT_REFERENCE(TypedDict):
    """
    Data structure for API request to modify the reference designator of a PCB footprint in EDA systems (e.g., KiCad).
    
    This TypedDict defines the required payload fields for the API request that renames the unique reference designator
    of a specific PCB footprint (component instance). It maps the original reference to the new desired reference,
    adhering to PCB design standards (IPC-2221) and KiCad naming conventions (e.g., R for resistors, U for ICs).
    
    Attributes:
        old_reference: Original/ current unique reference designator of the target PCB footprint (e.g., "R1", "U2", "C5")
                       Must exactly match the existing reference in the PCB layout (case-sensitive in some EDA tools)
        new_reference: New unique reference designator to assign to the target PCB footprint (e.g., "R10", "U8", "C15")
                       Must follow EDA/KiCad naming rules (alphanumeric, no special characters) and be unique on the PCB
                       Example: Change "R1" (old) to "R10" (new) for resistor re-designation
    """
    old_reference: str  # Original PCB footprint reference (e.g., R1, U2)
    new_reference: str  # New PCB footprint reference (e.g., R10, U8) - must be unique


class API_SET_FOOTPRINT_POSITION(TypedDict):
    """
    API request parameters for setting the absolute position of a PCB footprint (KiCad/EDA systems).

    This structure defines the input fields required to reposition a specific PCB footprint to a fixed,
    absolute location on the PCB canvas. The position is referenced to the PCB's design origin (typically
    the bottom-left corner of the board) and represents the final location of the footprint's origin point
    (reference pin or geometric center) — NOT a relative movement from the current position.

    Attributes:
        reference: Unique reference designator of the target footprint (e.g., "R1", "U2", "C5")
                   Must exactly match the footprint's existing reference in the PCB layout (case-sensitive in KiCad)
        new_position: API_POINT_PARAMS object containing the absolute X/Y coordinates for the footprint's origin
                      Units follow PCB design standards (mm); relative/delta values are NOT supported
                      Example: {"x": 25.4, "y": 12.7} = Place footprint at 25.4mm X, 12.7mm Y from PCB origin
    """
    reference: str           # Target footprint reference designator (e.g., R1, U2)
    new_position: API_POINT_PARAMS  # Absolute X/Y position of footprint origin (mm, NOT offset)



class API_ROTATE_FOOTPRINT_PARAMS( TypedDict):
    """
    API request parameters for rotating a specific PCB footprint (KiCad/EDA systems).

    This structure defines the input fields required to rotate a target PCB footprint around its origin point
    (reference pin/geometric center) by a specified angle. Rotation direction follows KiCad conventions:
    positive values = counterclockwise rotation, negative values = clockwise rotation.

    Attributes:
        reference: Unique reference designator of the target footprint to rotate (e.g., "R1", "U2", "C5")
                   Must exactly match the footprint's reference in the KiCad PCB layout (case-sensitive)
        degree: Rotation angle in **degrees (not radians)** (float value, e.g., 90.0, -45.5, 180.0)
                Positive degree = counterclockwise rotation (KiCad default)
                Negative degree = clockwise rotation
                Example: 90.0 = rotate 90° counterclockwise; -45.0 = rotate 45° clockwise
    """
    reference: str  # Target footprint reference (e.g., R1, U2) to rotate
    degree: float   # Rotation angle (degrees, not radians) - +ve=CCW, -ve=CW (e.g., 90.0, -45.0)


class API_FRAME_TYPE_PARAMS( str, Enum):
    """
    Enumeration for different frame type parameters in EDA (Electronic Design Automation) tools.
    
    Field Explanations:
    - FRAME_SCH: General schematic editor frame (main context for schematic design)
    - FRAME_SCH_SYMBOL_EDITOR: Schematic symbol editor frame (for creating/editing schematic symbols)
    - FRAME_PCB_EDITOR: PCB editor frame (core context for PCB layout design)
    - FRAME_FOOTPRINT_EDITOR: Footprint editor frame (for designing/editing PCB footprints)
    - FRAME_GERBER: Gerber viewer frame (for visualizing and verifying Gerber files)
    """
    FRAME_SCH = "FRAME_SCH"
    FRAME_SCH_SYMBOL_EDITOR = "FRAME_SCH_SYMBOL_EDITOR"
    FRAME_PCB_EDITOR = "FRAME_PCB_EDITOR"
    FRAME_FOOTPRINT_EDITOR = "FRAME_FOOTPRINT_EDITOR"
    FRAME_GERBER = "FRAME_GERBER"


class API_FRAME_PARAMS( TypedDict):
    """
    Typed dictionary for EDA frame parameters.
    This structure is used to define the core parameters of a frame window in EDA tools.
    
    Fields:
        frame_type: Specifies the type of EDA frame (e.g., schematic editor, PCB editor, Gerber viewer).
                    The value is restricted to the API_FRAME_TYPE_PARAMS enumeration.
    """
    frame_type : API_FRAME_TYPE_PARAMS



class API_ZOOM_PARAMS(str, Enum):
    """
    Enumeration of parameters for controlling view zoom operations in KiCad editor.
    
    Each value represents a specific zoom behavior centered on the editor canvas or adapted to content:
    - zoomInCenter: Zoom in the view centered on the canvas middle point
    - zoomOutCenter: Zoom out the view centered on the canvas middle point
    - zoomFitScreen: Adjust zoom to fit all visible content to the editor screen
    - zoomFitObjects: Adjust zoom to fit all selected/loaded objects to the editor view
    """
    zoomInCenter = "zoomInCenter"    # Zoom in centered on canvas
    zoomOutCenter = "zoomOutCenter"  # Zoom out centered on canvas
    zoomFitScreen = "zoomFitScreen"  # Zoom to fit content to screen
    zoomFitObjects = "zoomFitObjects"# Zoom to fit objects to view


