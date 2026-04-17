import json
import logging
from kicad_mcp.server import mcp
from kicad_mcp.utils import typechat_get_llm
from kicad_mcp.sdk_api_params import (
    API_MULTI_LINES_PARAMS, API_HIER_SHEET_PARAMS, API_CLASS_LABEL_PARAMS,
    API_TEXTBOX_PARAMS, API_LABEL_PARAMS, API_TABLE_PARAMS, API_QUERY_SYMBOL,
    API_SYMBOL_LIBARARY_LIST, API_PLACE_SYMBOL, API_MOVE_SYMBOL,
    API_ROTATE_SYMBOL, API_MODIFY_SYMBOL_VALUE, API_MODIFY_SYMBOL_REFERENCE,
    API_CREATE_SYMBOL_LIBARARY, API_CREATE_LIB_SYMBOL_PIN, API_QUERY_RESULT
)
from kicad_mcp.schema import API_PLACE_NETLABELS
from typechat import TypeChatValidator, TypeChatJsonTranslator

logger = logging.getLogger(__name__)
KICAD_CLIENT = None

def init_context(client, log):
    global KICAD_CLIENT, logger
    KICAD_CLIENT = client
    logger = log

@mcp.tool()
async def generate_net_labels(net_list: str) -> "API_PLACE_NETLABELS | None":
    """
    Given the full XML representation of a KiCad project, and build its connections using net labels.

    Returns a list of API_PLACE_NETLABELS representing connections.
    Expected to be used with the place_all_net_labels tool to automatically place all net labels into KiCad to apply the connections.
    """
    model = typechat_get_llm()
    validator = TypeChatValidator(API_PLACE_NETLABELS)
    translator = TypeChatJsonTranslator(model, validator, API_PLACE_NETLABELS)

    instruction = f"""
You are an assistant that generates all net label connections for a KiCad project.
Return a JSON object with a single field "nets", which is a list of objects
following API_PLACE_NETLABEL_PARAMS:

API_PLACE_NETLABEL_PARAMS:
  net_name: string
  pins: list of objects with:
    - designator: string
    - pin_num: integer

Use the XML provided below to generate the net labels.
--- BEGIN NETLIST XML ---
{net_list}
--- END NETLIST XML ---
"""
    from typechat import Failure
    result = await translator.translate(instruction)

    if isinstance(result, Failure):
        logger.error(f"TypeChat error: {result.message}")
        return None

    return result.value

@mcp.tool()
def place_all_net_labels(nets: API_PLACE_NETLABELS):
    """
    Send multiple net label placements to the KiCad SDK HTTP server.

    Wraps each net in an AGENT_ACTION JSON payload and posts to /placeNetLabels.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return
    for net_params in nets["nets"]:
        KICAD_CLIENT.place_net_label(net_params)

@mcp.tool()
def get_current_kicad_project() -> str | None:
    """
    Get the complete xml representation of the current KiCad project using NNG.

    Returns:
        str | None: XML content of the current KiCad project.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.get_netlist()

@mcp.tool()
def draw_multi_wires(lines: API_MULTI_LINES_PARAMS):
    """
    Asynchronous API function for drawing multiple electrical wires in KiCad for connecting component symbols.

    Key Differentiation:
    This function creates **electrical connection wires** for schematic circuit connectivity,
    used to connect component pins and form electrical circuits.

    Unit Note:
    All coordinate values use millimeters as the unit, consistent with KiCad's schematic coordinate system.

    Parameters:
        lines (API_MULTI_LINES_PARAMS): Strongly typed parameter structure for batch electrical wire drawing:
            - lines: List[API_LINE_PARAMS], a list of single electrical wire parameters. Each API_LINE_PARAMS element contains:
                - start (API_POINT_PARAMS): Start coordinate (x/y in mm) of the electrical wire (component pin/connection point).
                - end (API_POINT_PARAMS): End coordinate (x/y in mm) of the electrical wire (component pin/connection point).

    Returns:
        None: No explicit return value; only logs the API call result to the console.

    Log Behavior:
        - Prints the response from KiCad C++ SDK API if the call succeeds.
        - Prints an error prompt if no valid response is received from the SDK API.

    Example Usage:
        >>> wire1 = {"start": {"x": 10.0, "y": 20.0}, "end": {"x": 30.0, "y": 40.0}}
        >>> wire2 = {"start": {"x": 50.0, "y": 60.0}, "end": {"x": 70.0, "y": 80.0}}
        >>> multi_wires_params = {"lines": [wire1, wire2]}
        >>> await draw_multi_wires(multi_wires_params)
        [Draw Multi Wires] Response: {"status": "success", "drawn_wires_count": 2}
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawMultiWire", params=lines)

@mcp.tool()
def draw_multi_buses(lines: API_MULTI_LINES_PARAMS):
    """
    [KiCad Schematic Multi-Bus Drawing Interface]
    Asynchronously call the drawBus interface of KiCad CPP SDK to create multiple bus lines on the schematic.
    
    Core Function Overview:
    1. Specialized for drawing "bus lines" (aggregated signal groups) in KiCad schematic, distinct from single signal wires;
    2. Encapsulates remote API call logic, supports batch creation of multi-segment bus lines with unified parameter serialization;
    3. Automatically handles request timeout (30s default) and response validation, outputs standardized logs for success/failure;
    4. Adapts to KiCad's bus naming rules (e.g., D[0:7], ADDR[15:0]) and schematic coordinate system (unit: millimeter).

    Key Differences from draw_multi_wire:
    ----------
    | Aspect                | draw_multi_buses                          | draw_multi_wire                          |
    |-----------------------|-------------------------------------------|------------------------------------------|
    | Core Purpose          | Draw aggregated bus lines (signal groups) | Draw individual signal wires (single net)|
    | KiCad Object Type     | Bus (logical signal aggregation)          | Wire (physical single net connection)    |
    | Parameter Feature     | Requires bus name (e.g., D[0:7])          | No bus name, only coordinate points      |
    | Schematic Role        | Organize parallel signals (e.g., data/addr buses) | Connect discrete component pins  |
    | Electrical Meaning    | Logical grouping (no direct connectivity) | Physical electrical connection           |

    Parameter Description:
    ----------
    lines : API_MULTI_LINES_PARAMS
        Strongly typed core parameters for multi-bus drawing, including:
        - start: API_POINT_PARAMS (required), top-left/starting coordinate of the bus line
          - x: float, X-axis coordinate (unit: mm, KiCad schematic system)
          - y: float, Y-axis coordinate (unit: mm, KiCad schematic system)
        - end: API_POINT_PARAMS (required), bottom-right/ending coordinate of the bus line
          - x: float, X-axis coordinate (unit: mm)
          - y: float, Y-axis coordinate (unit: mm)
        - bus_name: str (required), KiCad-compliant bus name (e.g., "D[0:7]", "ADDR[15:0]", "DATA_BUS")
        - line_width: float (optional), bus line width (mm, default: KiCad schematic default 0.254mm)
    
    Return:
    ----------
    None
        Outputs response logs directly; returns no explicit value (adjustable to return response dict if needed)
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawBus", params=lines)

@mcp.tool()
def create_hier_sheet(sheet: API_HIER_SHEET_PARAMS):
    """
    [KiCad Schematic Hierarchical Sheet Creation Interface]
    Asynchronously call the createHierSheet interface of KiCad CPP SDK to create a hierarchical sheet on the schematic.
    
    Function Overview:
    1. Encapsulates KiCad remote API call logic, triggers hierarchical sheet creation via HTTP POST request;
    2. Automatically handles parameter serialization, request timeout control, and response status verification;
    3. Adapts to the interface specification of KiCad CPP SDK, with parameter format as nested rectangle (box) and title;
    4. Full coverage of exception scenarios, including connection failure, timeout, server error, etc., and outputs detailed logs.

    Parameter Description:
    ----------
    sheet : API_HIER_SHEET_PARAMS
        Core parameters for hierarchical sheet creation, constrained by TypedDict strong type, including the following fields:
        - box: API_RECTANGLE_PARAMS, required, bounding rectangle of the hierarchical sheet
          - top_left: API_POINT_PARAMS, top-left corner coordinate of the rectangle
            - x: float, top-left X coordinate (e.g., 100.0)
            - y: float, top-left Y coordinate (e.g., 200.0)
          - width: float, width of the rectangle (e.g., 200.0)
          - height: float, height of the rectangle (e.g., 150.0)
        - title: str, required, title text of the hierarchical sheet (e.g., "Power Supply")
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawHierSheet", params=sheet)

@mcp.tool()
def create_class_label(label: API_CLASS_LABEL_PARAMS):
    """
    [KiCad Schematic Class Label Creation Interface]
    Asynchronously call the createClassLabel interface of KiCad CPP SDK to create a class label on the schematic.
    
    Function Overview:
    1. Encapsulates KiCad remote API call logic, triggers class label creation via HTTP POST request;
    2. Automatically handles parameter serialization, request timeout control, and response status verification;
    3. Adapts to the interface specification of KiCad CPP SDK, with parameter format as position and class information;
    4. Full coverage of exception scenarios, including connection failure, timeout, server error, etc., and outputs detailed logs.

    Parameter Description:
    ----------
    label : API_CLASS_LABEL_PARAMS
        Core parameters for class label creation, constrained by TypedDict strong type, including the following fields:
        - position: API_POINT_PARAMS, required, anchor coordinate point of the class label
          - x: float, anchor X coordinate (e.g., 100.0)
          - y: float, anchor Y coordinate (e.g., 200.0)
        - net_class: str, required, name of the KiCad net class (e.g., "Power")
        - component_class: str, required, name of the KiCad component class (e.g., "MCU")
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="placeClassLabel", params=label)

@mcp.tool()
def create_textbox(textbox: API_TEXTBOX_PARAMS):
    """
    [KiCad Schematic Textbox Creation Interface]
    Asynchronously call the createTextbox interface of KiCad CPP SDK to create a textbox on the schematic.
    
    Function Overview:
    1. Encapsulates KiCad remote API call logic, triggers textbox creation via HTTP POST request;
    2. Automatically handles parameter serialization, request timeout control, and response status verification;
    3. Adapts to the interface specification of KiCad CPP SDK, with parameter format as rectangle (box) and text content;
    4. Full coverage of exception scenarios, including connection failure, timeout, server error, etc., and outputs detailed logs.

    Parameter Description:
    ----------
    textbox : API_TEXTBOX_PARAMS
        Core parameters for textbox creation, constrained by TypedDict strong type, including the following fields:
        - box: API_RECTANGLE_PARAMS, required, bounding rectangle of the textbox
          - top_left: API_POINT_PARAMS, top-left corner coordinate of the rectangle
            - x: float, top-left X coordinate (e.g., 100.0)
            - y: float, top-left Y coordinate (e.g., 200.0)
          - width: float, width of the rectangle (e.g., 200.0)
          - height: float, height of the rectangle (e.g., 150.0)
        - text: str, required, content of the textbox (e.g., "This is a textbox")
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawTextbox", params=textbox)

@mcp.tool()
def create_common_text(text: API_LABEL_PARAMS):
    """
    [KiCad Schematic Common Text Annotation Creation Interface]
    Asynchronously call the drawSchematicText interface of KiCad CPP SDK to create NON-ELECTRICAL plain text annotations on the schematic.
    
    Core Function Overview:
    1. Specialized for creating "common text annotations" (pure descriptive text) with NO electrical meaning in KiCad schematic;
    2. Encapsulates remote API call logic with strong-typed parameter validation (position + text content);
    3. Automatically handles request timeout (30s default) and response validation, outputs standardized success/failure logs;
    4. Adapts to KiCad's schematic coordinate system (unit: millimeter) and text rendering rules (supports ASCII/Chinese characters).

    Key Characteristics of Common Text Annotations:
    ----------
    - Electrical Meaning: NONE (only for human-readable description, no impact on circuit connectivity/ERC checks);
    - Core Purpose: Add comments, notes, or documentation (e.g., "Revision: V1.2", "Power Consumption: 500mA", "Designer: XXX");
    - Distinction from Labels (Local/Global/Hier): Labels have electrical connectivity logic, while common text is purely descriptive;
    - Rendering Rule: Text is displayed at the specified coordinate without binding to any net/component (movable freely).

    Critical Differences vs Label Functions (create_local/global/hier_label):
    ----------
    | Aspect                | create_common_text                | Label Functions (Local/Global/Hier) |
    |-----------------------|-----------------------------------|-------------------------------------|
    | Electrical Logic      | No electrical meaning             | Defines net connectivity            |
    | ERC Impact            | No ERC checks/errors              | Triggers ERC errors on duplicate    |
    | Binding Target        | No binding (free text)            | Bound to nets/components            |
    | Core Use Case         | Documentation/notes               | Net connection (intra/cross sheet)  |

    Parameter Description:
    ----------
    text : API_LABEL_PARAMS
        Strongly typed core parameters for common text creation, including:
        - position: API_POINT_PARAMS (required), anchor coordinate of the text annotation
          - x: float, X-axis coordinate (unit: mm, KiCad schematic coordinate system)
          - y: float, Y-axis coordinate (unit: mm, KiCad schematic coordinate system)
        - text: str (required), Content of the plain text annotation (e.g., "Revision: V1.2", "Note: Connect to GND via 0Ω resistor", "Design Date: 2025-12");
                Supports ASCII characters and KiCad-compatible Chinese characters (no strict naming rules like labels).
    
    Return:
    ----------
    None
        Outputs success/failure logs directly; no explicit return value (adjustable to return response dict if needed).
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawSchematicText", params=text)

@mcp.tool()
def create_table(table: API_TABLE_PARAMS):
    """
    [KiCad Schematic Table Creation Interface]
    Asynchronously call the createTable interface of KiCad CPP SDK to create a table on the schematic.
    
    Function Overview:
    1. Encapsulates KiCad remote API call logic, triggers table creation via HTTP POST request;
    2. Automatically handles parameter serialization, request timeout control, and response status verification;
    3. Adapts to the interface specification of KiCad CPP SDK, with parameter format as position and dimensions (rows/cols);
    4. Full coverage of exception scenarios, including connection failure, timeout, server error, etc., and outputs detailed logs.

    Parameter Description:
    ----------
    table : API_TABLE_PARAMS
        Core parameters for table creation, constrained by TypedDict strong type, including the following fields:
        - pos: API_POINT_PARAMS, required, top-left corner coordinate point of the table
          - x: float, top-left X coordinate (e.g., 100.0)
          - y: float, top-left Y coordinate (e.g., 200.0)
        - rows: int, required, number of rows in the table (e.g., 5)
        - cols: int, required, number of columns in the table (e.g., 3)
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawTable", params=table)

@mcp.tool()
def create_local_label(label: API_LABEL_PARAMS):
    """
    [KiCad Schematic Local Label Creation Interface]
    Asynchronously call the placeLocalLabel interface of KiCad CPP SDK to create a LOCAL label on the schematic.
    
    Core Function Overview:
    1. Specialized for creating "Local Labels" (intra-sheet net labels) that only connect nets within the SAME schematic sheet;
    2. Encapsulates remote API call logic with strong-typed parameter validation (position + text);
    3. Automatically handles request timeout (30s default) and response validation, outputs standardized logs;
    4. Adapts to KiCad's local label naming rules (no duplicate names within a single sheet) and schematic coordinate system (unit: millimeter).

    Key Characteristics of Local Labels:
    ----------
    - Scope: Valid ONLY within the current schematic sheet (no cross-sheet connectivity);
    - Use Case: Connect discrete nets (e.g., component pins) on the same sheet without physical wires;
    - Uniqueness: Must have unique text within the sheet (duplicates cause KiCad ERC errors);
    - Electrical Logic: Nets with the same local label text on the same sheet are electrically connected.

    Parameter Description:
    ----------
    label : API_LABEL_PARAMS
        Strongly typed core parameters for local label creation, including:
        - position: API_POINT_PARAMS (required), anchor coordinate of the local label
          - x: float, X-axis coordinate (unit: mm, KiCad schematic coordinate system)
          - y: float, Y-axis coordinate (unit: mm, KiCad schematic coordinate system)
        - text: str (required), Local label text (e.g., "LED_CTRL", "VCC_3V3", "UART_TX");
                Must follow KiCad net naming rules (alphanumeric + underscores, no spaces/special chars).
    
    Return:
    ----------
    None
        Outputs success/failure logs directly; no explicit return value (adjustable to return response dict if needed).
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="placeLocalLabel", params=label)

@mcp.tool()
def create_global_label(label: API_LABEL_PARAMS):
    """
    [KiCad Schematic Global Label Creation Interface]
    Asynchronously call the placeGlobalLabel interface of KiCad CPP SDK to create a GLOBAL label on the schematic.
    
    Core Function Overview:
    1. Specialized for creating "Global Labels" (cross-sheet net labels) that connect nets ACROSS ALL schematic sheets;
    2. Encapsulates remote API call logic with strong-typed parameter validation (position + text);
    3. Automatically handles request timeout (30s default) and response validation, outputs standardized logs;
    4. Adapts to KiCad's global label naming rules (unique across the entire project) and schematic coordinate system (unit: millimeter).

    Key Characteristics of Global Labels:
    ----------
    - Scope: Valid ACROSS ALL sheets in the entire KiCad project (cross-sheet connectivity);
    - Use Case: Connect nets between different schematic sheets (e.g., power supply, global control signals);
    - Uniqueness: Must have unique text across the entire project (duplicates cause KiCad ERC errors);
    - Electrical Logic: Nets with the same global label text on any sheet are electrically connected project-wide.

    Critical Notes vs Local Labels:
    ----------
    | Aspect                | Local Label                  | Global Label                  |
    |-----------------------|------------------------------|-------------------------------|
    | Scope                 | Single sheet                 | Entire project                |
    | Cross-sheet Connectivity | No                          | Yes                           |
    | Duplicate Rule        | Unique per sheet             | Unique per project            |
    | Typical Use Case      | Intra-sheet signal routing   | Inter-sheet power/control     |

    Parameter Description:
    ----------
    label : API_LABEL_PARAMS
        Strongly typed core parameters for global label creation, including:
        - position: API_POINT_PARAMS (required), anchor coordinate of the global label
          - x: float, X-axis coordinate (unit: mm, KiCad schematic coordinate system)
          - y: float, Y-axis coordinate (unit: mm, KiCad schematic coordinate system)
        - text: str (required), Global label text (e.g., "5V_GLOBAL", "RESET_ALL", "I2C_SDA");
                Must follow KiCad net naming rules (alphanumeric + underscores, no spaces/special chars);
                Must be unique across the entire project to avoid ERC errors.
    
    Return:
    ----------
    None
        Outputs success/failure logs directly; no explicit return value (adjustable to return response dict if needed).
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="placeGlobalLabel", params=label)

@mcp.tool()
def create_hier_label(label: API_LABEL_PARAMS):
    """
    [KiCad Schematic Hierarchical Label Creation Interface]
    Asynchronously call the placeHierLabel interface of KiCad CPP SDK to create a HIERARCHICAL label on the schematic.
    
    Core Function Overview:
    1. Specialized for creating "Hierarchical Labels" (inter-sheet labels for hierarchical schematics) that connect nets between parent/child sheets;
    2. Encapsulates remote API call logic with strong-typed parameter validation (position + text);
    3. Automatically handles request timeout (30s default) and response validation, outputs standardized logs;
    4. Adapts to KiCad's hierarchical label naming rules and schematic coordinate system (unit: millimeter).

    Key Characteristics of Hierarchical Labels:
    ----------
    - Scope: Valid ONLY between parent sheet and its direct child sheets (hierarchical connectivity);
    - Use Case: Connect signals in multi-level hierarchical schematics (e.g., parent sheet → child MCU sheet, child power sheet → parent);
    - Uniqueness: Must have unique text within the parent-child sheet pair (duplicates cause KiCad ERC errors);
    - Electrical Logic: Nets with the same hierarchical label text between parent and child sheets are electrically connected (no cross-child-sheet connectivity).

    Parameter Description:
    ----------
    label : API_LABEL_PARAMS
        Strongly typed core parameters for hierarchical label creation, including:
        - position: API_POINT_PARAMS (required), anchor coordinate of the hierarchical label
          - x: float, X-axis coordinate (unit: mm, KiCad schematic coordinate system)
          - y: float, Y-axis coordinate (unit: mm, KiCad schematic coordinate system)
        - text: str (required), Hierarchical label text (e.g., "MCU_GPIO_0", "POWER_VIN", "UART_RX");
                Must follow KiCad net naming rules (alphanumeric + underscores, no spaces/special chars);
                Must be unique within the parent-child sheet pair to avoid ERC errors.
    
    Return:
    ----------
    None
        Outputs success/failure logs directly; no explicit return value (adjustable to return response dict if needed).
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="placeHierLabel", params=label)

@mcp.tool()
def query_symbol_pin(query: API_QUERY_SYMBOL):
    """
    [KiCad Schematic Symbol Pin Query Interface]
    Asynchronously call the querySymbolPin interface of KiCad CPP SDK to query symbol pin information.
    
    Parameter Description:
    ----------
    query : API_QUERY_SYMBOL
        Core parameters for symbol pin query, including:
        - reference: str, required, reference designator of the symbol to query (e.g. "U3")
    
    Return Description:
    ----------
    API_SYMBOL_PINS_INFO | None
        - Success: Structured pin information (API_SYMBOL_PINS_INFO type)
        - Failure: None (and print error log)
    
    Return  Details:
        - pins_info: List[API_PIN_INFO], list of pin details
          - pin_number: str, pin number (e.g. "12")
          - pin_position: API_POINT_PARAMS, pin coordinate (x/y float values)
        - reference: str, symbol reference designator (e.g. "U3")
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="querySymbolPin", params=query, cmd_type="cpp_sdk_query")

@mcp.tool()
def query_symbol_library() -> API_SYMBOL_LIBARARY_LIST:
    """
    [KiCad Symbol Library Query Interface]
    Asynchronously retrieve all symbol library names (global and project-level) from KiCad via the CPP SDK.

    Function Overview:
    ------------------
    This function calls KiCad's CPP SDK `getSymbolLibrary` API to fetch a complete list of symbol library names,
    including:
    - Global symbol libraries (configured in KiCad's global preferences)
    - Project-specific symbol libraries (linked to the currently open KiCad schematic/project)

    Returns:
    --------
    list[str] | None
        - Success: A list of string values representing symbol library names (e.g., {"symbol_library_name":"LMV824AIDT"})
        - Failure: None (returns None if API call fails, returns empty response, or raises an exception)
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    response: API_QUERY_RESULT = KICAD_CLIENT.cpp_sdk_action(api_name="getSymbolLibrary", params={}, cmd_type="cpp_sdk_query")
    if "msg" not in response:
        logger.error("lack msg")
        return None
    library: API_SYMBOL_LIBARARY_LIST = json.loads(response["msg"])
    return library

@mcp.tool()
def place_symbol(params: API_PLACE_SYMBOL):
    """
    [KiCad Schematic symbol Placement Interface]
    Asynchronously places an electronic component symbol in KiCad via the CPP SDK.

    Function Overview:
    ------------------
    This method sends a symbol placement request to the KiCad CPP SDK, rendering a specified
    electronic component (e.g., resistor, capacitor, transistor) at the given coordinate position
    in the active KiCad schematic or PCB document. It validates the input parameters against
    KiCad's component naming and coordinate standards, and returns SDK execution feedback via logs.

    Parameters:
    -----------
    params : API_PLACE_SYMBOL
        Strongly-typed parameter structure for symbol placement (compliant with KiCad's data model):
        - category: API_SYMBOL_CATEGORY
          Standardized component category (e.g., RESISTOR, MOSFET_N_CHANNEL, POWER_DC)
        - value: str
          Electrical/physical value of the component (e.g., "100K", "0.1uF", "12V", "IRF540N")
        - position: API_POINT_PARAMS
          Anchor coordinate (x/y in millimeters) for symbol placement (KiCad schematic/PCB coordinate system)
        - reference: str
          Unique KiCad-style reference designator (e.g., "R1", "Q2", "U5") following prefix rules:
          R=Resistor, C=Capacitor, Q=Transistor, U=IC, D=Diode, L=Inductor, etc.

    Returns:
    --------
    None
        No explicit return value; execution status is logged to the console:
        - Success: Prints raw response from KiCad CPP SDK
        - Failure: Prints "No valid response" message if SDK returns empty/error data
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="placeSymbol", params=params)

@mcp.tool()
def move_symbol(params: API_MOVE_SYMBOL):
    """
    [KiCad Schematic symbol Movement Interface]
    Asynchronously moves an electronic component symbol in KiCad via the CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="moveSymbol", params=params)

@mcp.tool()
def rotate_symbol(params: API_ROTATE_SYMBOL):
    """
    [KiCad Schematic/PCB Symbol Rotation Interface]
    Asynchronously rotates a placed electronic component symbol in KiCad via the CPP SDK.

    This MCP tool function sends a structured rotation request to the KiCad CPP SDK, rotating
    a target symbol by a fixed 90-degree increment (clockwise/counterclockwise) around its anchor point.
    It supports both single-unit and multi-unit symbols (e.g., dual-opamps, multi-channel ICs)
    and adheres to KiCad's native symbol rotation behavior.

    Parameters:
    -----------
    params : API_ROTATE_SYMBOL
        Strongly-typed parameter structure for symbol rotation (compliant with KiCad's data model):
        - reference: str
          Unique KiCad-style reference designator of the symbol to rotate (e.g., "R1", "U5", "C12", "Q2").
          Must follow KiCad prefix rules: R=Resistor, C=Capacitor, U=IC/MCU, D=Diode, Q=Transistor, J=Connector, etc.
          The symbol must exist in the active KiCad schematic/PCB document (no validation is performed here).
        - unit: str
          Unit identifier for multi-unit symbols (defaults to empty string "" for single-unit components):
          - Empty string (""): Targets the default unit (single-unit symbols or first unit of multi-unit symbols)
          - Numeric string ("1", "2", "3"): Targets the specified unit of a multi-unit symbol (e.g., "2" for U5.2)
        - ccw: bool
          Rotation direction control (fixed 90-degree increment per rotation):
          - True: Rotate 90 degrees COUNTERCLOCKWISE (anti-clockwise) around the symbol's anchor point
          - False: Rotate 90 degrees CLOCKWISE around the symbol's anchor point

    Returns:
    --------
    None
        No explicit return value; execution status and SDK responses are logged to the console:
        - Success: Prints the raw JSON response from the KiCad CPP SDK (e.g., {"status": "success", "symbol": "R1"})
        - Failure: Prints a warning if the SDK returns an empty/error response (no exception raised)
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="rotateSymbol", params=params)

@mcp.tool()
def modify_symbol_value(params: API_MODIFY_SYMBOL_VALUE):
    """
    [KiCad Schematic/PCB Symbol Value Modification Interface]
    Asynchronously updates the physical/electrical value of a placed electronic component symbol in KiCad via the CPP SDK.

    This MCP tool function sends a structured request to the KiCad CPP SDK to modify the value attribute of an existing
    component symbol in the active KiCad schematic or PCB document. It enforces KiCad's native value formatting rules
    (e.g., unit abbreviations, tolerance/voltage ratings) and supports all common component types (resistors, capacitors,
    ICs/MCUs, diodes, etc.). The operation is non-blocking (async) to avoid halting the MCP service event loop.

    Parameters:
    -----------
    params : API_MODIFY_SYMBOL_VALUE
        Strongly-typed parameter structure for symbol value modification (compliant with KiCad's data model):
        - reference: str
          Unique KiCad-style reference designator of the target symbol (case-sensitive for SDK validation):
          - Must follow KiCad prefix conventions: R=Resistor, C=Capacitor, U=IC/MCU, D=Diode, Q=Transistor, J=Connector, etc.
          - Example: "R1", "C12", "U5", "LED7" (must exist in the active KiCad document; no pre-validation is performed here)
        - value: str
          New physical/electrical value to assign to the symbol (KiCad-compatible format required):
          - Resistors: "100K±1%", "4.7M", "0Ω", "10R" (use R/ohm abbreviations per KiCad standards)
          - Capacitors: "0.1uF/25V", "100nF", "22pF" (include voltage ratings for electrolytic/tantalum caps)
          - ICs/MCUs: "STM32F103C8T6", "ATmega328P" (full part number for traceability)
          - General rule: Use KiCad's native unit abbreviations (K/M for ohms; uF/nF/pF for capacitance) to ensure SDK compatibility.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="modifySymbolValue", params=params)

@mcp.tool()
def modify_symbol_reference(params: API_MODIFY_SYMBOL_REFERENCE):
    """
    [KiCad Schematic/PCB Symbol Reference Designator Modification Interface]
    Asynchronously renames the unique reference designator of a placed electronic component symbol in KiCad via the CPP SDK.

    This MCP tool function sends a structured request to the KiCad CPP SDK to update the core identifier (reference designator)
    of an existing component symbol in the active KiCad schematic or PCB document. It enforces KiCad's strict reference naming
    rules (e.g., valid prefixes, unique numeric suffixes) and ensures compatibility with KiCad's internal validation logic.
    The operation is non-blocking (async) to maintain responsiveness of the MCP service.

    Parameters:
    -----------
    params : API_MODIFY_SYMBOL_REFERENCE
        Strongly-typed parameter structure for reference designator modification (KiCad-compliant):
        - old_reference : str
          Current/legacy reference designator of the target symbol (must exist in the active KiCad document):
          - Format: KiCad standard prefix + numeric suffix (e.g., "R1", "C12", "U5", "LED7", "Q3")
          - Case sensitivity: KiCad SDK treats this as case-sensitive (e.g., "R1" ≠ "r1"; use uppercase prefixes per convention)
          - Validation: SDK returns error if old_reference does not exist in the active document.
        
        - new_reference : str
          New/desired reference designator to assign (must comply with KiCad's naming constraints):
          - Mandatory rules (enforced by KiCad SDK):
            1. Prefix must match the component's type (e.g., resistors → "R", ICs → "U" — cannot rename R1 to U1)
            2. Numeric suffix must be unique (no duplicates in the same document, e.g., "R2" cannot exist already)
            3. No whitespace/special characters (underscores allowed for multi-unit symbols: "U5_2" for U5.2)
          - Format example: "R2", "C15", "U8", "LED9", "Q4" (uppercase prefix + integer suffix)

    Returns:
    --------
    None
        No explicit return value; execution status is logged to the console:
        - Success: Prints raw JSON response from KiCad CPP SDK (e.g., {"status":"success","old_ref":"R1","new_ref":"R2"})
        - Failure: Prints warning if SDK returns empty/error response (no exception raised by default)
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="modifySymbolReference", params=params)

@mcp.tool()
def create_symbol_library(params: API_CREATE_SYMBOL_LIBARARY):
    """
    [KiCad Symbol Editor - Local Project Symbol Library Creation Interface]
    Asynchronously creates a project-specific local symbol library in KiCad via the CPP SDK — restricted to KiCad's Symbol Editor context.

    This MCP tool function sends a structured request to the KiCad CPP SDK to initialize a new, empty symbol library tied to the active KiCad project.
    Critical Constraint: This function ONLY works when KiCad's Symbol Editor (not Schematic Editor/PCB Editor) is open and active — the SDK will reject
    requests if run in other KiCad editors or outside the Symbol Editor context. The library is created in the project's `symbols/` directory and
    automatically added to the project's symbol library table.

    Parameters:
    -----------
    params : API_CREATE_SYMBOL_LIBARARY
        Strongly-typed parameter structure for library creation (KiCad Symbol Editor-compatible):
        - symbol_library_name : str
          Name of the local project symbol library to create (KiCad naming rules enforced):
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="addSymbolLibrary", params=params)

@mcp.tool()
def create_symbol_pin(params: API_CREATE_LIB_SYMBOL_PIN):
    """
    [KiCad Symbol Editor - Local Project Symbol Pin Creation Interface]
    Asynchronously creates a configurable pin on a symbol in the active KiCad project symbol library via the CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="addLibSymbolPin", params=params)

@mcp.tool()
def importNonKicadSchematic():
    """
    Imports non-KiCad format schematic files into the current KiCad project via CPP SDK.
    
    This function invokes the KiCad CPP SDK's `importNonKicadSch` API through the pre-initialized
    KICAD_CLIENT instance, enabling the import of schematic files in non-native KiCad formats
    (e.g., Altium, Eagle, OrCAD, PADS schematic files) into the active KiCad project.
    
    The function serves as a programmatic wrapper for KiCad's "Import Non-KiCad Schematic" feature
    (bound to the `ID_IMPORT_NON_KICAD_SCH` menu event in the schematic editor), replacing manual
    menu clicks with an API-driven call.
    
    Returns:
        Optional[Dict]: Parsed JSON response from the KiCad CPP SDK if import succeeds, containing
                        status, imported file details, and conversion results; None if the client
                        is uninitialized or the import operation fails.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="importNonKicadSch", params={})

@mcp.tool()
def importVectorGraphicsFile():
    """
    Imports vector graphics files into the active KiCad schematic via CPP SDK.
    
    This function acts as a programmatic wrapper for KiCad's "Import Vector Graphics File" feature,
    invoking the CPP SDK's `importVectorGraphic` API through the pre-initialized KICAD_CLIENT instance.
    It enables importing vector graphics (e.g., SVG, EPS, DXF) directly into the current KiCad schematic
    editor frame, preserving the vector properties (scalable without quality loss, editable shapes/lines).
    
    Unlike raster image import (PNG/JPG), vector graphics retain mathematical shape definitions, making
    them ideal for adding logos, custom symbols, mechanical outlines, or branded elements to schematics.
    
    Returns:
        Optional[Dict]: Parsed JSON response from the KiCad CPP SDK if import succeeds, containing
                        status, imported file details (path, format), and placement metadata (scale, layer);
                        None if the KICAD_CLIENT is uninitialized or the import operation fails.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="importVectorGraphic", params={})

@mcp.tool()
def exportNetlist():
    """
    Exports a netlist file from the active KiCad schematic via CPP SDK.
    
    This function serves as a programmatic wrapper for KiCad's "Export Netlist" feature,
    invoking the CPP SDK's `exportNetlist` API through the pre-initialized KICAD_CLIENT instance.
    A netlist is a critical text-based file that describes the electrical connectivity of components
    in the schematic (e.g., component references, pin connections, net names), enabling seamless
    transfer of schematic logic to PCB layout tools.
    
    Returns:
        Optional[Dict]: Parsed JSON response from the KiCad CPP SDK if export succeeds, containing
                        status, exported netlist file path, format, and schematic metadata;
                        None if the KICAD_CLIENT is uninitialized or the export operation fails.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="exportNetlist", params={})

@mcp.tool()
def openSchematicSetupDlg():
    """
    Opens the Schematic Setup dialog for the active KiCad schematic editor via CPP SDK.
    
    Wraps KiCad's native "Settings → Schematic Setup" feature, providing access to schematic
    configuration (sheet size, electrical rules, text styles, etc.). Requires KICAD_CLIENT initialization.
    
    Returns:
        Optional[Dict]: Parsed SDK response (dialog status) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="schematicSetup", params={})

@mcp.tool()
def openSymbolLibraryBrowser():
    """
    Opens the Symbol Library Browser in the active KiCad schematic editor via CPP SDK.
    
    Wraps KiCad's native Symbol Library Browser feature, providing access to browse, search,
    and insert schematic symbols from local/remote symbol libraries. Requires KICAD_CLIENT initialization.
    
    Returns:
        Optional[Dict]: Parsed SDK response (browser open status) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="symbolLibraryBrowser", params={})

@mcp.tool()
def showBusSyntaxHelp():
    """
    Opens the Bus Syntax Help documentation window in the active KiCad schematic editor via CPP SDK.
    
    Wraps KiCad's native Bus Syntax Help feature, displaying a help window that details the syntax rules
    for defining and using bus nets in KiCad schematics (e.g., bus naming conventions, range specifications).
    Requires KICAD_CLIENT initialization before invocation.
    
    Returns:
        Optional[Dict]: Parsed SDK response (help window open status) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="showBusSyntaxHelp")

@mcp.tool()
def runERCCheck():
    """
    Runs the Electrical Rule Check (ERC) on the active KiCad schematic project via CPP SDK.
    
    Wraps KiCad's native ERC feature to validate schematic design against electrical rules,
    identifying errors/warnings such as unconnected pins, short circuits, invalid net connections,
    and mismatched pin types. The check results are displayed in the ERC report panel.
    
    Requires KICAD_CLIENT initialization before invocation.
    
    Returns:
        Optional[Dict]: Parsed SDK response (ERC check status, including error/warning counts) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="runERC")

@mcp.tool()
def showSpiceSimulator():
    """
    Opens the SPICE Simulator window in the active KiCad schematic editor via CPP SDK.
    
    Wraps KiCad's native SPICE Simulator feature, launching the simulation interface for
    performing analog/digital circuit simulations on KiCad schematic designs (e.g., DC sweep,
    AC analysis, transient simulation). Requires KICAD_CLIENT initialization before invocation.
    
    Returns: 
        Optional[Dict]: Parsed SDK response (simulator window open status) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.info("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="showSimulator")

TOOLS = [
    generate_net_labels,
    place_all_net_labels,
    get_current_kicad_project,
    draw_multi_wires,
    draw_multi_buses,
    create_hier_sheet,
    create_class_label,
    create_textbox,
    create_common_text,
    create_table,
    create_local_label,
    create_global_label,
    create_hier_label,
    query_symbol_pin,
    query_symbol_library,
    place_symbol,
    move_symbol,
    rotate_symbol,
    modify_symbol_value,
    modify_symbol_reference,
    create_symbol_library,
    create_symbol_pin,
    importNonKicadSchematic,
    importVectorGraphicsFile,
    exportNetlist,
    openSchematicSetupDlg,
    openSymbolLibraryBrowser,
    showBusSyntaxHelp,
    runERCCheck,
    showSpiceSimulator,
]
