import logging
from logging.handlers import RotatingFileHandler
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
import time
import json

from kicad_client import KiCadClient
from schema import API_PLACE_NETLABELS
from sdk_api_params import API_MULTI_LINES_PARAMS, API_CIRCLE_PARAMS, API_ARC_PARAMS, API_BEZIER_PARAMS
from sdk_api_params import API_HIER_SHEET_PARAMS, API_CLASS_LABEL_PARAMS, API_TEXTBOX_PARAMS, API_TABLE_PARAMS
from sdk_api_params import API_RECTANGLE_PARAMS, API_LABEL_PARAMS, API_QUERY_SYMBOL, API_QUERY_RESULT,API_SYMBOL_LIBARARY_LIST
from sdk_api_params import API_PLACE_SYMBOL, API_MOVE_SYMBOL,API_ROTATE_SYMBOL,API_MODIFY_SYMBOL_VALUE,API_MODIFY_SYMBOL_REFERENCE,API_CREATE_SYMBOL_LIBARARY
from sdk_api_params import API_CREATE_LIB_SYMBOL_PIN, API_PCB_TRACK_PARAMS, API_PCB_VIA_PARAMS
from sdk_api_params import API_PCB_PAD_PARAMS, API_MOVE_PCB_PAD_PARAMS, API_ROTATE_PCB_PAD,API_MODIFY_PAD_NUMBER, API_MODIFY_PAD_SIZE,API_MODIFY_PAD_DRILL_SIZE
from sdk_api_params import API_MODIFY_PAD_DRILL_SHAPE, API_SET_PAD_POSITION,API_PCB_LAYER_NAME_LIST
from sdk_api_params import API_PCB_FOOTPRINT_INFO_LIST,API_PCB_REFERENCE_LIST,API_MOVE_FOOTPRINT_PARAMS
from sdk_api_params import API_MODIFY_FOOTPRINT_REFERENCE,API_SET_FOOTPRINT_POSITION, API_ROTATE_FOOTPRINT_PARAMS,API_FRAME_PARAMS
from sdk_api_params import API_ZOOM_PARAMS


from typechat import (
    Failure,
    TypeChatJsonTranslator,
    TypeChatValidator,
    create_openai_language_model,
)

from valid_editors import VALID_EDITORS


def typechat_get_llm(model=os.getenv("OPENAI_MODEL") or "gpt-5-mini", api_key=None, base_url=None):
    llm = create_openai_language_model(
        model=model,
        api_key=api_key or os.getenv("OPENAI_API_KEY") or "",
        endpoint=base_url or os.getenv("OPENAI_BASE_URL") or "",
    )
    llm.timeout_seconds = 60 * 3  # 3 minutes
    return llm


# Load environment variables
load_dotenv()

def get_logger():
    # Check DEBUG flag
    DEBUG_KICAD_MCP_SERVER = os.getenv("DEBUG_KICAD_MCP_SERVER", "0") == "1"

    # Determine OS-independent writable directory
    if os.name == "nt":  # Windows
        log_dir = os.path.join(os.getenv("APPDATA", os.getenv("TEMP", os.getcwd())), "kicad-mcp", "kicad-mcp-client")
    else:  # Linux/MacOS
        log_dir = os.path.join(os.getenv("XDG_CACHE_HOME", os.path.join(os.getenv("HOME"), ".cache")), "kicad-mcp", "kicad-mcp-client")

    # Ensure the log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Configure logging
    log_file = os.path.join(log_dir, "kicad-mcp-server.log")

    # Always log to console
    console_handler = logging.StreamHandler()

    # Add file logging only if DEBUG_KICAD_MCP_SERVER is True
    if DEBUG_KICAD_MCP_SERVER:
        file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[console_handler, file_handler],
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[console_handler],  # Only console logging when not in DEBUG mode
        )

    return logging.getLogger(__name__)



logger = get_logger()




# Initialize MCP server
mcp = FastMCP("kicad-mcp-server")


# Global KiCad client instance
KICAD_CLIENT: KiCadClient 


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
def draw_multi_wires( lines : API_MULTI_LINES_PARAMS ):
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
    logger.info( "drawMultiWire")
    logger.info(f"lines : {lines}")
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    logger.info("Before cpp_sdk_action")
    return KICAD_CLIENT.cpp_sdk_action( api_name= "drawMultiWire",params=lines)  


@mcp.tool()
def draw_multi_buses( lines : API_MULTI_LINES_PARAMS):
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
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "drawBus",params=lines)  
   


@mcp.tool()
def draw_circle( circle : API_CIRCLE_PARAMS):
    """
    MCP Tool Function: Call KiCad CPP SDK API to draw circle in schematic/PCB
    ============================================================================
    Function Description:
        This asynchronous function encapsulates HTTP POST requests to call the drawCircle interface of KiCad's underlying CPP SDK.
        It is used to draw circles with specified position and radius on KiCad schematic or PCB canvas, supporting strong-typed parameter validation
        and adapting to KiCad coordinate system rules.
    Application Scenarios:
        - Automatically draw circular annotations (e.g., pin indicators, area markers) in KiCad schematics
        - Batch generate circular pads/keepout areas in PCB design
        - Customize KiCad graphic drawing process via scripting
    Parameter Description:
        circle: API_CIRCLE_PARAMS (strongly typed dictionary)
            Core parameters for drawing circles, including subfields:
            - center: API_POINT_PARAMS (required), circle center coordinate point
              - x: float, X-axis coordinate of center (unit: millimeter, KiCad schematic/PCB coordinate system)
              - y: float, Y-axis coordinate of center (unit: millimeter, KiCad schematic/PCB coordinate system)
            - radius: float (required), circle radius (unit: millimeter, positive value, comply with KiCad drawing precision requirements, min 0.01mm)
    API Call Specification:
        1. Request Method: POST
        2. Request URL: {KICAD_API_URL}/cpp_sdk (managed by KiCadEndPoint.CPP_SDK)
        3. Request Body Format: Comply with KiCad API unified specification, containing fixed "action" and context parameters
        4. Timeout: 30 seconds (adapt to time-consuming scenarios of KiCad underlying graphic drawing)
    Return Description:
        No explicit return value; print KiCad API response content on success, and error information on failure
    Notes:
        1. Ensure KiCad API service is started and listening on {KICAD_API_URL}
        2. Parameter unit must be millimeter (KiCad default unit) to avoid unit conversion errors
        3. Radius must be a positive value, otherwise KiCad SDK returns parameter validation failure
    ============================================================================
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "drawCircle",params=circle)  


@mcp.tool()
def draw_arc(arc : API_ARC_PARAMS):
    """
    [KiCad Schematic Arc Drawing Interface]
    Asynchronously call the drawArc interface of KiCad CPP SDK to draw an arc on the schematic.
    
    Function Overview:
    1. Encapsulates KiCad remote API call logic, triggers arc drawing via HTTP POST request;
    2. Automatically handles parameter serialization, request timeout control, and response status verification;
    3. Adapts to the interface specification of KiCad CPP SDK, with parameter format as nested coordinate objects (start/end);
    4. Full coverage of exception scenarios, including connection failure, timeout, server error, etc., and outputs detailed logs.

    Parameter Description:
    ----------
    arc : API_ARC_PARAMS
        Core parameters for arc drawing, constrained by TypedDict strong type, including the following fields:
        - start: API_POINT_PARAMS, required, start coordinate of the arc
          - x: float, start X coordinate (e.g., 100.0)
          - y: float, start Y coordinate (e.g., 200.0)
        - end: API_POINT_PARAMS, required, end coordinate of the arc
          - x: float, end X coordinate (e.g., 300.0)
          - y: float, end Y coordinate (e.g., 200.0)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "drawArc",params=arc)


@mcp.tool()
def draw_bezier(bezier : API_BEZIER_PARAMS):
    """
    [KiCad Schematic Bezier Curve Drawing Interface]
    Asynchronously call the drawBezier interface of KiCad CPP SDK to draw a bezier curve on the schematic.
    
    Function Overview:
    1. Encapsulates KiCad remote API call logic, triggers bezier curve drawing via HTTP POST request;
    2. Automatically handles parameter serialization, request timeout control, and response status verification;
    3. Adapts to the interface specification of KiCad CPP SDK, with parameter format as nested coordinate objects (start/c1/c2/end);
    4. Full coverage of exception scenarios, including connection failure, timeout, server error, etc., and outputs detailed logs.

    Parameter Description:
    ----------
    bezier : API_BEZIER_PARAMS
        Core parameters for bezier curve drawing, constrained by TypedDict strong type, including the following fields:
        - start: API_POINT_PARAMS, required, start coordinate of the bezier curve
          - x: float, start X coordinate (e.g., 100.0)
          - y: float, start Y coordinate (e.g., 200.0)
        - c1: API_POINT_PARAMS, required, first control point of the bezier curve
          - x: float, first control point X coordinate (e.g., 150.0)
          - y: float, first control point Y coordinate (e.g., 250.0)
        - c2: API_POINT_PARAMS, required, second control point of the bezier curve
          - x: float, second control point X coordinate (e.g., 250.0)
          - y: float, second control point Y coordinate (e.g., 250.0)
        - end: API_POINT_PARAMS, required, end coordinate of the bezier curve
          - x: float, end X coordinate (e.g., 300.0)
          - y: float, end Y coordinate (e.g., 200.0)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "drawBezier",params=bezier)


@mcp.tool()
def draw_rectangle(rectangle : API_RECTANGLE_PARAMS):
    """
    [KiCad Schematic Rectangle Drawing Interface]
    Asynchronously call the drawRectangle interface of KiCad CPP SDK to draw a rectangle on the schematic.
    
    Function Overview:
    1. Encapsulates KiCad remote API call logic, triggers rectangle drawing via HTTP POST request;
    2. Automatically handles parameter serialization, request timeout control, and response status verification;
    3. Adapts to the interface specification of KiCad CPP SDK, with parameter format as nested coordinate objects (top_left) and dimensions (width/height);
    4. Full coverage of exception scenarios, including connection failure, timeout, server error, etc., and outputs detailed logs.

    Parameter Description:
    ----------
    rectangle : API_RECTANGLE_PARAMS
        Core parameters for rectangle drawing, constrained by TypedDict strong type, including the following fields:
        - top_left: API_POINT_PARAMS, required, top-left corner coordinate of the rectangle
          - x: float, top-left X coordinate (e.g., 100.0)
          - y: float, top-left Y coordinate (e.g., 200.0)
        - width: float, required, width of the rectangle (e.g., 200.0)
        - height: float, required, height of the rectangle (e.g., 150.0)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "drawRectangle",params=rectangle)

@mcp.tool()
def create_hier_sheet(sheet : API_HIER_SHEET_PARAMS):
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
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "drawHierSheet",params=sheet)

@mcp.tool()
def create_class_label(label : API_CLASS_LABEL_PARAMS):
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
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "placeClassLabel",params=label)

@mcp.tool()
def create_textbox(textbox : API_TEXTBOX_PARAMS):
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
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "drawTextbox",params=textbox)


@mcp.tool()
def create_common_text( text : API_LABEL_PARAMS):
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
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "drawSchematicText",params=text)


@mcp.tool()
def create_table(table : API_TABLE_PARAMS):
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
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "drawTable",params=table)

@mcp.tool()
def create_local_label(label : API_LABEL_PARAMS):
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
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "placeLocalLabel",params=label)


@mcp.tool()
def create_global_label( label : API_LABEL_PARAMS):
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
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "placeGlobalLabel",params=label)


@mcp.tool()
def create_hier_label(label : API_LABEL_PARAMS):
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

    Critical Notes vs Local/Global Labels:
    ----------
    | Aspect                | Local Label                  | Global Label                  | Hierarchical Label           |
    |-----------------------|------------------------------|-------------------------------|------------------------------|
    | Scope                 | Single sheet                 | Entire project                | Parent ↔ Direct child sheets |
    | Connectivity          | Intra-sheet                  | Cross-all-sheets              | Cross-parent-child sheets    |
    | Use Case              | Simple single-sheet design   | Flat multi-sheet design       | Hierarchical multi-sheet design |
    | ERC Error Trigger     | Duplicate per sheet          | Duplicate per project         | Duplicate per parent-child pair |

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
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "placeHierLabel",params=label)

@mcp.tool()
def query_symbol_pin(query : API_QUERY_SYMBOL) :
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
        logger.error( "Client not initialized")

    response = KICAD_CLIENT.cpp_sdk_action( api_name= "querySymbolPin",params=query, cmd_type="cpp_sdk_query")
    return response


@mcp.tool()
def query_symbol_library()->API_SYMBOL_LIBARARY_LIST:
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
        - Success: A list of string values representing symbol library names (e.g., {\"symbol_library_name\":\"LMV824AIDT\"})
        - Failure: None (returns None if API call fails, returns empty response, or raises an exception)

    Error Handling:
    ---------------
    - Catches all exceptions during API invocation and returns None to avoid runtime crashes
    - Returns None if no valid response is received from the KiCad CPP SDK API
    - Ignores invalid/empty responses gracefully

    Notes:
    ------
    - Requires an active KiCad session (SDK context) to access library data
    - Library names are returned as raw string values (matching KiCad's internal library naming convention)
    - No input parameters are required (queries all available libraries by default)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    response : API_QUERY_RESULT = KICAD_CLIENT.cpp_sdk_action( api_name= "getSymbolLibrary",params={}, cmd_type="cpp_sdk_query")
    if "msg" not in response:
        logger.error("lack msg")
        return None
    library : API_SYMBOL_LIBARARY_LIST = json.loads(response["msg"])
    return library


@mcp.tool()
def place_symbol( params : API_PLACE_SYMBOL):
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

    Error Handling:
    ---------------
    - Silently handles empty SDK responses (logs warning, no exception raised)
    - Relies on upstream `call_kicad_cpp_sdk_api` for low-level error handling (e.g., connection issues)
    - Assumes input `params` adheres to API_PLACE_SYMBOL schema (validate before calling for robustness)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "placeSymbol",params=params)


@mcp.tool()
def move_symbol( params : API_MOVE_SYMBOL):
    """
    [KiCad Schematic symbol Movement Interface]
    Asynchronously moves an electronic component symbol in KiCad via the CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "moveSymbol",params=params)


@mcp.tool()
def rotate_symbol( params : API_ROTATE_SYMBOL):
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

    Behavior Notes:
    ---------------
    - Rotation Anchor: Symbols are rotated around their native KiCad anchor point (typically the symbol's origin/center pin)
    - Fixed Increment: Rotation is always 90 degrees (KiCad's standard symbol rotation step; no custom angles supported)
    - Multi-Unit Support: Rotates only the specified unit of a multi-unit symbol (other units remain unchanged)
    - Async Execution: Uses non-blocking I/O to call the KiCad CPP SDK, avoiding blocking the main event loop of the MCP service

    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "rotateSymbol",params=params)


@mcp.tool()
def modify_symbol_value( params : API_MODIFY_SYMBOL_VALUE):
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

    Behavior Notes:
    ---------------
    - Scope: Modifies the "Value" field of the symbol (visible in KiCad schematic/PCB property panel) — does not alter other attributes (e.g., footprint, pin mappings)
    - Case Sensitivity: The `reference` field is case-sensitive in KiCad's CPP SDK (e.g., "R1" ≠ "r1"), even if the schematic display is case-insensitive
    - Validation: The KiCad SDK validates value format (e.g., rejects invalid units like "100microF" — use "100uF" instead)
    - Async Execution: Uses non-blocking I/O to call the CPP SDK, ensuring the MCP service remains responsive to other requests
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "modifySymbolValue",params=params)



@mcp.tool()
def modify_symbol_reference( params : API_MODIFY_SYMBOL_REFERENCE):
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
          - Prefix rules (matching component type):
            R=Resistor, C=Capacitor, U=IC/MCU/Op-amp, D=Diode, Q=Transistor/MOSFET, J=Connector,
            X=Crystal, T=Transformer, F=Fuse, SW=Switch, LED=Light-emitting diode
          - Case sensitivity: KiCad SDK treats this as case-sensitive (e.g., "R1" ≠ "r1"; use uppercase prefixes per convention)
          - Validation: SDK returns error if old_reference does not exist in the active document.
        
        - new_reference : str
          New/desired reference designator to assign (must comply with KiCad's naming constraints):
          - Mandatory rules (enforced by KiCad SDK):
            1. Prefix must match the component's type (e.g., resistors → "R", ICs → "U" — cannot rename R1 to U1)
            2. Numeric suffix must be unique (no duplicates in the same document, e.g., "R2" cannot exist already)
            3. No whitespace/special characters (underscores allowed for multi-unit symbols: "U5_2" for U5.2)
          - Format example: "R2", "C15", "U8", "LED9", "Q4" (uppercase prefix + integer suffix)
          - Multi-unit symbols: Use underscores instead of dots (SDK-compatible: "U5_2" vs UI display: "U5.2")

    Returns:
    --------
    None
        No explicit return value; execution status is logged to the console:
        - Success: Prints raw JSON response from KiCad CPP SDK (e.g., {"status":"success","old_ref":"R1","new_ref":"R2"})
        - Failure: Prints warning if SDK returns empty/error response (no exception raised by default)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "modifySymbolReference",params=params)



@mcp.tool()
def create_symbol_library( params : API_CREATE_SYMBOL_LIBARARY):
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
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "addSymbolLibrary",params=params)


@mcp.tool()
def create_symbol_pin( params :API_CREATE_LIB_SYMBOL_PIN):
    """
    [KiCad Symbol Editor - Local Project Symbol Pin Creation Interface]
    Asynchronously creates a configurable pin on a symbol in the active KiCad project symbol library via the CPP SDK.

    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "addLibSymbolPin",params=params)

@mcp.tool()
def create_pcb_track( params : API_PCB_TRACK_PARAMS):
    """
    Asynchronously creates a PCB track (copper trace) in KiCad via the C++ SDK MCP API.
    
    This function sends a request to the KiCad C++ SDK API ("drawPcbTrack") with the specified
    track parameters to draw a copper trace on the PCB. It handles the asynchronous API call,
    logs the response status, and returns no value.
    
    Args:
        params: API_PCB_TRACK_PARAMS - A typed dictionary containing PCB track parameters:
            - start: Start coordinate of the track (required, API_POINT_PARAMS type)
            - end: End coordinate of the track (required, API_POINT_PARAMS type)
            - layer_name: Optional layer name for the track (defaults to active layer if omitted)
    
    Returns:
        None - This function only logs the API response and has no return value.
    
    Notes:
        - The coordinate system follows KiCad PCB standards (unit: millimeter, origin at bottom-left of the board).
        - Valid layer names include "F.Cu" (Front Copper), "B.Cu" (Back Copper), "In1.Cu" (Inner Layer 1), etc.
        - If the API response is empty, it indicates the KiCad SDK did not return a valid result (e.g., invalid parameters).
    
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "drawPcbTrack",params=params)


@mcp.tool()
def create_pcb_via( params : API_PCB_VIA_PARAMS):
    """
    MCP tool function to asynchronously create a conductive PCB via in KiCad via the C++ SDK API.
    
    This function is decorated with @mcp.tool() to register it as a standard MCP (Multi-Channel Protocol) tool,
    enabling integration with KiCad's MCP framework for AI-driven PCB design workflows. It invokes the KiCad C++ SDK's
    "placePcbVia" endpoint to create a via (through-hole/blind-buried/microvia) on the PCB, logs the API response status,
    and returns no value to the caller.
    
    Args:
        params: API_PCB_VIA_PARAMS - A strongly-typed dictionary containing mandatory PCB via parameters:
            - position: API_POINT_PARAMS (required) - Center coordinate of the via (mm, KiCad PCB coordinate system)
            - via_type: API_PCB_VIA_TYPE (required) - Type of via (THROUGH/BLIND_BURIED/MICROVIA/NOT_DEFINED)
            - start_layer: API_PCB_LAYER_ID (required) - Starting conductive copper layer for the via
            - end_layer: API_PCB_LAYER_ID (required) - Ending conductive copper layer for the via
    
    Returns:
        None - This function only logs the API response information (success/failure) and has no return value.
    
    Notes:
        - The `start_layer` and `end_layer` must be valid conductive copper layers (F_Cu/B_Cu/InX_Cu), not non-conductive layers (e.g., F_SilkS).
        - Via type constraints apply: 
          - THROUGH vias must connect F_Cu and B_Cu;
          - MICROVIAs only connect adjacent copper layers (e.g., F_Cu ↔ In1_Cu);
          - BLIND_BURIED vias connect outer ↔ inner or inner ↔ inner layers (no outer layer exposure for buried).
        - An empty response indicates invalid parameters (e.g., invalid layer combination) or KiCad SDK communication failures.
        - This function is registered as an MCP tool and can be invoked by AI agents in KiCad's MCP workflow.
    
    Examples:
        >>> via_params: API_PCB_VIA_PARAMS = {
        ...     "position": {"x": 15.0, "y": 25.0},
        ...     "via_type": API_PCB_VIA_TYPE.THROUGH,
        ...     "start_layer": API_PCB_LAYER_ID.F_Cu,
        ...     "end_layer": API_PCB_LAYER_ID.B_Cu
        ... }
        >>> await create_pcb_via(via_params)
        [Place PCB via] Response: {'status': 'success', 'via_id': 12345}
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "placePcbVia",params=params)


@mcp.tool()
def create_pcb_pad( params : API_PCB_PAD_PARAMS):
    """
    MCP tool function to asynchronously create a conductive PCB pad in KiCad via the C++ SDK API.
    
    This function is decorated with @mcp.tool() to register it as a standard MCP (Multi-Channel Protocol) tool,
    enabling integration with KiCad's MCP framework for AI-driven PCB design workflows. It sends a request to
    the KiCad C++ SDK's "createPcbPad" endpoint with the specified pad parameters, logs the API response status,
    and returns no value to the caller.
    
    Args:
        params: API_PCB_PAD_PARAMS - A strongly-typed dictionary containing mandatory PCB pad parameters:
            - position: API_POINT_PARAMS (required) - Center coordinate of the pad (mm, KiCad PCB coordinate system)
            - number: str (required) - Unique pad number (maps to component pin/netlist, non-empty string)
    
    Returns:
        None - This function only logs the API response information (success/failure) and has no return value.
    
    Notes:
        - The pad number must be unique within the component to avoid netlist mapping errors in KiCad.
        - The position coordinate uses KiCad's default PCB coordinate system (origin at bottom-left, unit: millimeter).
        - An empty response indicates invalid parameters (e.g., empty pad number) or KiCad SDK communication failures.
        - This function is registered as an MCP tool and can be invoked by AI agents in KiCad's MCP workflow.
    
    Examples:
        >>> pad_params: API_PCB_PAD_PARAMS = {
        ...     "position": {"x": 18.5, "y": 22.3},
        ...     "number": "1"
        ... }
        >>> await create_pcb_pad(pad_params)
        [Place PCB Pad] Response: {'status': 'success'}
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "createPcbPad",params=params)


@mcp.tool()
def move_pcb_pad( params : API_MOVE_PCB_PAD_PARAMS ):
    """
    MCP tool function to asynchronously move an existing PCB pad in KiCad via the C++ SDK API.
    
    This function is decorated with @mcp.tool() to register it as a standard MCP (Multi-Channel Protocol) tool,
    enabling integration with KiCad's MCP framework for AI-driven PCB design workflows. It invokes the KiCad C++ SDK's
    "movePcbPad" endpoint to translate (move) a target PCB pad by a specified X/Y offset, logs the API response status,
    and returns no value to the caller.
    
    Args:
        params: API_MOVE_PCB_PAD_PARAMS - A strongly-typed dictionary containing mandatory pad movement parameters:
            - offset: API_POINT_PARAMS (required) - X/Y translation offset (mm, +right/up, -left/down)
            - number: str (required) - Unique pad number to identify the target pad for movement
    
    Returns:
        None - This function only logs the API response information (success/failure) and has no return value.
    
    Notes:
        - The offset is relative to the pad's current position (not absolute coordinates) in KiCad's PCB coordinate system.
        - The target pad number must exist in the current PCB design (no movement is performed for non-existent pads).
        - KiCad's coordinate system uses bottom-left as origin: positive X = right, positive Y = up.
        - An empty response indicates invalid parameters (e.g., empty pad number) or KiCad SDK communication failures.
        - This function is registered as an MCP tool and can be invoked by AI agents in KiCad's MCP workflow.
    
    Examples:
        >>> move_params: API_MOVE_PCB_PAD_PARAMS = {
        ...     "offset": {"x": 0.5, "y": -0.3},  # Move right 0.5mm, down 0.3mm
        ...     "number": "1"
        ... }
        >>> await move_pcb_pad(move_params)
        [Move PCB Pad] Response: {'status': 'success'}
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "movePcbPad",params=params)


@mcp.tool()
def rotate_pcb_pad( params : API_ROTATE_PCB_PAD):
    """
    MCP tool function to asynchronously rotate an existing PCB pad in KiCad via the C++ SDK API.
    
    This function is decorated with @mcp.tool() to register it as a standard MCP (Multi-Channel Protocol) tool,
    enabling integration with KiCad's MCP framework for AI-driven PCB design workflows. It invokes the KiCad C++ SDK's
    "rotatePcbPad" endpoint to rotate a target PCB pad around its center point by a specified angle, logs the API response
    status, and returns no value to the caller.
    
    Args:
        params: API_ROTATE_PCB_PAD - A strongly-typed dictionary containing mandatory pad rotation parameters:
            - number: str (required) - Unique pad number to identify the target pad for rotation
            - degree: float (required) - Rotation angle (degrees: +counterclockwise, -clockwise)
    
    Returns:
        None - This function only logs the API response information (success/failure) and has no return value.
    
    Notes:
        - Rotation is performed around the pad's own center point (not the PCB's origin or any other reference point).
        - KiCad's rotation convention applies: positive angles = counterclockwise (CCW), negative angles = clockwise (CW).
        - The target pad number must exist in the current PCB design (no rotation is performed for non-existent pads).
        - Valid angle values include any numeric value (e.g., 180.0 = half rotation, -30.0 = 30° clockwise).
        - An empty response indicates invalid parameters (e.g., non-numeric degree) or KiCad SDK communication failures.
        - This function is registered as an MCP tool and can be invoked by AI agents in KiCad's MCP workflow.
    
    Examples:
        >>> rotate_params: API_ROTATE_PCB_PAD = {
        ...     "number": "1",
        ...     "degree": 90.0  # Rotate 90° counterclockwise around pad center
        ... }
        >>> await rotate_pcb_pad(rotate_params)
        [Rotate PCB Pad] Response: {'status': 'success'}
        
        >>> # Clockwise rotation example (45°)
        >>> rotate_cw_params = {"number": "2", "degree": -45.0}
        >>> await rotate_pcb_pad(rotate_cw_params)
        [Rotate PCB Pad] Response: {'status': 'success'}
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "rotatePcbPad",params=params)


@mcp.tool()
def modify_pcb_pad_number( params : API_MODIFY_PAD_NUMBER):
    """
    Asynchronous tool function to modify the identification number of a PCB footprint pad via KiCad C++ SDK API.
    
    This function acts as a Python wrapper for the KiCad C++ SDK's `modifyPadNumber` API,
    responsible for sending pad number modification requests and handling the API response.
    It validates the presence of a response and provides logging for debugging/monitoring purposes.
    
    Args:
        params: A typed dictionary containing the old and new pad numbers
                - old_number: Original pad number to be replaced
                - new_number: New pad number to assign to the target PCB footprint pad
    
    Returns:
        Any: The raw response from the KiCad C++ SDK API if available; None if no valid response is received
    
    Raises:
        (Implicit) Any exceptions raised by `call_kicad_cpp_sdk_api` (e.g., network/API connection errors)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "modifyPadNumber",params=params)


@mcp.tool()
def modify_pcb_pad_size( params : API_MODIFY_PAD_SIZE):
    """
    Asynchronous tool function to modify the physical size of a specific PCB footprint pad via KiCad C++ SDK API.
    
    This function serves as a Python wrapper for the KiCad C++ SDK's `modifyPadSize` API endpoint,
    responsible for sending pad size modification requests (target pad number + new X/Y dimensions)
    and handling the API response. It provides logging for response status to aid in debugging and
    monitoring of PCB design modifications.
    
    Args:
        params: Typed dictionary containing target pad identifier and new size parameters
                - number: Unique ID of the PCB pad to be resized (e.g., "1", "A2")
                - size: API_SIZE_PARAMS object with X/Y dimension values (mm) for the new pad size
    
    Returns:
        Any: Raw response data from the KiCad C++ SDK API if the request succeeds; None if no valid response
             is received (e.g., API timeout, invalid parameters, connection errors)
    
    Raises:
        (Implicit) Exceptions may be raised by `call_kicad_cpp_sdk_api` (e.g., network errors,
        invalid API payload, KiCad SDK runtime errors)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "modifyPadSize",params=params)


@mcp.tool()
def modify_pcb_pad_drill_size( params : API_MODIFY_PAD_DRILL_SIZE):
    """
    Asynchronous tool function to modify the drill hole size of a specific through-hole PCB pad via KiCad C++ SDK API.
    
    This function acts as a Python asynchronous wrapper for the KiCad C++ SDK's `modifyPadDrillSize` API endpoint,
    dedicated to sending requests to update the physical dimensions of drill holes in through-hole PCB pads.
    It handles API response validation and provides logging for operational monitoring, which is critical for
    PCB manufacturing accuracy (drill size directly impacts component soldering and mechanical fit).
    
    Args:
        params: Typed dictionary containing target pad identifier and new drill size parameters
                - number: Unique ID of the through-hole PCB pad to modify (e.g., "1", "A2", "Pin_5")
                - size: API_SIZE_PARAMS object with X/Y values for the new drill size
                        (X=Y for circular drills; X/Y = width/height for oval/rectangular drills, units: mm)
    
    Returns:
        Any: Raw response data from the KiCad C++ SDK API if the request is processed successfully;
             None if no valid response is received (e.g., API timeout, invalid pad number, non-through-hole pad)
    
    Raises:
        (Implicit) Exceptions may be raised by `call_kicad_cpp_sdk_api` (e.g., network connectivity issues,
        invalid drill size parameters, KiCad SDK runtime errors, or attempts to modify drill size of SMD pads)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "modifyPadDrillSize",params=params)



@mcp.tool()
def modify_pcb_pad_drill_shape( params : API_MODIFY_PAD_DRILL_SHAPE):
    """
    Asynchronous tool function to modify the drill hole shape of a specific through-hole PCB pad via KiCad C++ SDK API.
    
    This function serves as a Python asynchronous wrapper for the KiCad C++ SDK's `modifyPadDrillShape` API endpoint,
    dedicated to updating the geometric shape of drill holes in through-hole PCB pads (supports CIRCLE/OBLONG types).
    It validates API responses and provides logging for operational monitoring, which is critical for ensuring
    consistency between PCB design and CNC drilling manufacturing processes.
    
    Args:
        params: Typed dictionary containing target pad identifier and new drill shape parameters
                - number: Unique ID of the through-hole PCB pad to modify (e.g., "1", "A2", "Pin_5")
                - shape: API_PAD_DRILL_SHAPE Enum value (CIRCLE/OBLONG/UNDEFINED) for the new drill hole shape
                          Note: UNDEFINED typically resets the shape to default or marks the pad as unconfigured
    
    Returns:
        Any: Raw response data from the KiCad C++ SDK API if the request is processed successfully;
             None if no valid response is received (e.g., API timeout, invalid pad number, attempt to modify SMD pad drill shape)
    
    Raises:
        (Implicit) Exceptions may be raised by `call_kicad_cpp_sdk_api` (e.g., network connectivity issues,
        invalid drill shape enum values, KiCad SDK runtime errors, or attempts to set drill shape for non-through-hole pads)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "modifyPadDrillShape",params=params)



@mcp.tool()
def set_pcb_pad_new_position( params : API_SET_PAD_POSITION):
    """
    Asynchronous tool function to set the ABSOLUTE position of a specific PCB footprint pad via KiCad C++ SDK API.
    
    This function acts as a Python asynchronous wrapper for the KiCad C++ SDK's `setPadPosition` API endpoint,
    dedicated to repositioning a target PCB pad to a specified absolute coordinate on the PCB canvas.
    CRITICAL NOTE: The `new_position` parameter specifies the FINAL absolute X/Y coordinates (relative to PCB origin),
    NOT a relative offset or movement delta from the pad's current position (do NOT use this function for incremental moves).
    
    Args:
        params: Typed dictionary containing target pad identifier and new absolute position parameters
                - number: Unique ID of the PCB pad to reposition (e.g., "1", "A2", "Pin_5")
                - new_position: API_POINT_PARAMS object with ABSOLUTE X/Y coordinates (mm/mil) relative to PCB origin
                                - Example: {"x": 10.0, "y": 25.5} = pad placed at X=10mm, Y=25.5mm from PCB origin
                                - This is NOT a delta/offset (e.g., +5mm in X direction is invalid here)
    
    Returns:
        Any: Raw response data from the KiCad C++ SDK API if the position update succeeds;
             None if no valid response is received (e.g., API timeout, invalid pad number, out-of-bounds coordinates)
    
    Raises:
        (Implicit) Exceptions may be raised by `call_kicad_cpp_sdk_api` (e.g., network errors,
        invalid coordinate values, attempts to use relative offsets instead of absolute positions)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "setPadPosition",params=params) 


@mcp.tool()
def query_pcb_layer_names() ->API_PCB_LAYER_NAME_LIST:
    """
    Asynchronous tool function to query all available PCB layer names from KiCad C++ SDK API.
    
    This function acts as a Python asynchronous wrapper for the KiCad C++ SDK's `queryLayerNames` API endpoint,
    dedicated to fetching the complete list of valid PCB layer names (e.g., "F.Cu", "B.SilkS") configured in the
    current KiCad PCB design environment. It handles API response validation, JSON parsing, and error handling
    to ensure reliable retrieval of layer name data for multi-layer PCB design operations.
    
    Returns:
        API_PCB_LAYER_NAME_LIST | None: 
            - On success: Typed dictionary containing a list of API_PCB_LAYER_NAME objects (all valid PCB layers)
              Example: {"pcb_layer_name_list": [{"pcb_layer_name": "F.Cu"}, {"pcb_layer_name": "B.SilkS"}]}
            - On failure: None (e.g., missing "msg" field in API response, JSON parsing errors, network issues)
    
    Raises:
        (Handled) All exceptions are caught and logged; no explicit exceptions are raised to the caller.
        Common failure scenarios:
            - Missing "msg" field in KiCad API response (invalid response format)
            - JSON parsing errors (malformed layer name data in "msg" field)
            - Network/SDK errors (failed connection to KiCad C++ SDK)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    response : API_QUERY_RESULT = KICAD_CLIENT.cpp_sdk_action( api_name= "queryLayerNames",params={}, cmd_type="cpp_sdk_query")
    if "msg" not in response:
        logger.error("lack msg")
        return None
    library : API_PCB_LAYER_NAME_LIST = json.loads(response["msg"])
    return library


@mcp.tool()
def query_pcb_all_footprint_info()->API_PCB_FOOTPRINT_INFO_LIST:
    """
    Asynchronous tool function to query core information of ALL footprints on the current KiCad PCB.
    
    This function acts as a Python asynchronous wrapper for the KiCad C++ SDK's `queryAllFootprintInfo` API endpoint,
    dedicated to fetching comprehensive identification data for every footprint (component physical outline)
    present in the active KiCad PCB design. The returned data includes each footprint's unique reference designator
    (e.g., R1, U2) and fully qualified footprint ID (fpid, format: library_name:footprint_name).
    
    Returns:
        API_PCB_FOOTPRINT_INFO_LIST | None:
            - On success: Typed dictionary containing a list of API_PCB_FOOTPRINT_INFO objects
              Example: {"footprint_list": [{"reference": "R1", "fpid": "Resistor_SMD:R_0805"}, 
                                           {"reference": "U2", "fpid": "IC_SOIC:SOIC-8"}]}
            - On failure: None (e.g., missing "msg" field in API response, JSON parsing errors, SDK connection issues)
    
    Raises:
        (Handled) All exceptions are caught and logged; no explicit exceptions are raised to the caller.
        Common failure scenarios:
            - Missing mandatory "msg" field in KiCad API response (invalid response format)
            - Malformed JSON in "msg" field (corrupted footprint info data)
            - KiCad SDK connection/execution errors (e.g., no active PCB design open)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    response : API_QUERY_RESULT = KICAD_CLIENT.cpp_sdk_action( api_name= "queryAllFootprintInfo",params={}, cmd_type="cpp_sdk_query")
    if "msg" not in response:
        logger.error("lack msg")
        return None
    library : API_PCB_FOOTPRINT_INFO_LIST = json.loads(response["msg"])
    return library


@mcp.tool()
def query_pcb_footprint_info( params : API_PCB_REFERENCE_LIST)->API_PCB_FOOTPRINT_INFO_LIST:
    """
    Asynchronous tool function to query footprint information for SPECIFIC PCB components via reference designators.
    
    This function acts as a Python asynchronous wrapper for the KiCad C++ SDK's `queryFootprintInfo` API endpoint,
    dedicated to fetching core footprint identification data (reference + fpid) for a list of specified PCB components
    (identified by their reference designators, e.g., R1, U2). Unlike `query_pcb_all_footprint_info`, this function
    only returns data for the components explicitly listed in the input reference list (filtered query).
    
    Args:
        params: Typed dictionary containing a list of PCB component reference designators to query
                - reference_list: List of API_PCB_REFERENCE objects (e.g., [{"reference": "R1"}, {"reference": "U2"}])
                - Empty list = returns empty footprint info list (no components queried)
    
    Returns:
        API_PCB_FOOTPRINT_INFO_LIST | None:
            - On success: Typed dictionary containing footprint info for the queried references
              Example: {"footprint_list": [{"reference": "R1", "fpid": "Resistor_SMD:R_0805"}, 
                                           {"reference": "U2", "fpid": "IC_SOIC:SOIC-8"}]}
            - On failure: None (e.g., missing "msg" field in API response, invalid references, JSON parsing errors)
    
    Raises:
        (Handled) All exceptions are caught and logged; no explicit exceptions are raised to the caller.
        Common failure scenarios:
            - Missing mandatory "msg" field in KiCad API response (invalid response format)
            - Malformed JSON in "msg" field (corrupted footprint info data)
            - Invalid/non-existent reference designators in input params (e.g., "R999" which does not exist)
            - KiCad SDK connection errors or no active PCB design open
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    response : API_QUERY_RESULT = KICAD_CLIENT.cpp_sdk_action( api_name= "queryFootprintInfo",params={}, cmd_type="cpp_sdk_query")
    if "msg" not in response:
        logger.error("lack msg")
        return None
    library : API_PCB_FOOTPRINT_INFO_LIST = json.loads(response["msg"])
    return library




@mcp.tool()
def move_pcb_footprint( params : API_MOVE_FOOTPRINT_PARAMS):
    """
    Asynchronous tool function to move a specific PCB footprint by a RELATIVE offset via KiCad C++ SDK API.
    
    This function acts as a Python asynchronous wrapper for the KiCad C++ SDK's `moveFootprint` API endpoint,
    dedicated to incrementally repositioning a target PCB footprint (identified by reference designator)
    from its current location by a specified X/Y relative offset (delta values). Unlike absolute position setting,
    this function adjusts the footprint's position by additive values (e.g., +3mm in X = move right 3mm, -2mm in Y = move down 2mm).
    
    Args:
        params: Typed dictionary containing target footprint reference and relative movement offset
                - reference: Unique ID of the PCB footprint to move (e.g., "R1", "U2", "C5")
                - offset: API_POINT_PARAMS object with RELATIVE X/Y offset values (mm/mil)
                          Positive X = right movement; Negative X = left movement
                          Positive Y = up movement; Negative Y = down movement
                          Example: {"x": 3.5, "y": -1.2} = move 3.5mm right, 1.2mm down
    
    Returns:
        Any | None:
            - On success: Raw response data from the KiCad C++ SDK API (e.g., movement confirmation, new position)
            - On failure: None (e.g., invalid reference designator, non-numeric offset values, KiCad API timeout)
    
    Raises:
        (Implicit) Exceptions may be raised by `call_kicad_cpp_sdk_api` (e.g., network connectivity issues,
        invalid offset parameters, attempts to move non-existent footprint references)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "moveFootprint",params=params) 



@mcp.tool()
def modify_pcb_footprint_reference( params : API_MODIFY_FOOTPRINT_REFERENCE):
    """
    Asynchronous tool function to rename the reference designator of a specific PCB footprint via KiCad C++ SDK API.
    
    This function acts as a Python asynchronous wrapper for the KiCad C++ SDK's `modifyFootprintReference` API endpoint,
    dedicated to changing the unique reference designator (component label) of a target PCB footprint from its original
    value to a new specified value. The operation adheres to PCB design standards (IPC-2221) and KiCad naming rules,
    requiring the new reference to be unique (no duplicates on the PCB) and alphanumeric (no special characters).
    
    Args:
        params: Typed dictionary containing old and new reference designators for the target footprint
                - old_reference: Exact original reference of the footprint to rename (e.g., "R1", "U2")
                                 Case-sensitive in some EDA environments (verify before use)
                - new_reference: New unique reference to assign (e.g., "R10", "U8")
                                 Must follow KiCad naming conventions (e.g., R=resistor, U=IC, C=capacitor)
                                 Must not conflict with existing references on the PCB
    
    Returns:
        Any | None:
            - On success: Raw response data from the KiCad C++ SDK API (e.g., rename confirmation, updated footprint info)
            - On failure: None (e.g., invalid old reference, duplicate new reference, non-compliant new reference format)
    
    Raises:
        (Implicit) Exceptions may be raised by `call_kicad_cpp_sdk_api` (e.g., network errors,
        attempt to rename non-existent footprint, duplicate reference violation)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "modifyFootprintReference",params=params) 


@mcp.tool()
def set_pcb_footprint_position( params : API_SET_FOOTPRINT_POSITION):
    """
    Asynchronously sets the absolute position of a specific PCB footprint via the KiCad C++ SDK API.

    This function wraps the KiCad SDK's `setFootprintPosition` endpoint to reposition a target PCB footprint
    (identified by its reference designator) to a fixed, absolute location on the PCB. It sets the final position
    of the footprint's origin (reference pin/geometric center) relative to the PCB's design origin (typically
    the bottom-left corner of the board) — it does NOT support relative/incremental movement (delta values).

    Args:
        params: Typed dictionary with footprint identification and position data
            reference: Unique reference designator of the target footprint (e.g., "R1", "U2", "C5")
                       Must exactly match the footprint's reference in the KiCad PCB layout (case-sensitive)
            new_position: API_POINT_PARAMS object containing absolute X/Y coordinates (units: mm)
                          Example: {"x": 25.4, "y": 12.7} = Place footprint at 25.4mm X, 12.7mm Y from PCB origin
                          Relative/delta values (e.g., +5mm in X) are NOT supported

    Returns:
        Any | None: Raw KiCad SDK API response data if the operation succeeds (e.g., position confirmation),
                    or None if the API call fails (e.g., invalid reference, out-of-bounds coordinates)

    Notes:
        - Coordinates are relative to the PCB's design origin (bottom-left corner by default in KiCad)
        - Ensure coordinate values are within the physical bounds of the PCB to avoid placement errors
        - Unlike `move_pcb_footprint`, this function overwrites the footprint's position (not incremental)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "setFootprintPosition",params=params) 


@mcp.tool()
def rotate_pcb_footprint( params : API_ROTATE_FOOTPRINT_PARAMS):
    """
    Asynchronously rotates a specific PCB footprint via the KiCad C++ SDK API.

    This function wraps the KiCad SDK's `rotateFootprint` endpoint to rotate a target PCB footprint
    (identified by its reference designator) around its origin point (reference pin/geometric center).
    Rotation uses **degree-based angles (not radians)** and follows KiCad's default rotation conventions:
    positive values = counterclockwise (CCW) rotation, negative values = clockwise (CW) rotation.

    Args:
        params: Typed dictionary with footprint identification and rotation parameters
            reference: Unique reference designator of the target footprint (e.g., "R1", "U2", "C5")
                       Must exactly match the footprint's reference in KiCad (case-sensitive)
            degree: Rotation angle in degrees (float, e.g., 90.0, -45.5, 180.0) — NOT radians
                    Positive value: Counterclockwise rotation (e.g., 90.0 = 90° CCW)
                    Negative value: Clockwise rotation (e.g., -45.0 = 45° CW)
                    Valid range: Typically -360.0 to 360.0 (KiCad normalizes out-of-range values)

    Returns:
        Any | None: Raw KiCad SDK API response data if rotation succeeds (e.g., rotation confirmation),
                    or None if the API call fails (e.g., invalid reference, non-numeric degree value)

    Notes:
        - Rotation is performed around the footprint's origin (reference pin/geometric center), not PCB origin
        - KiCad normalizes angles outside -360° to 360° (e.g., 450.0 → 90.0, -405.0 → -45.0)
        - The log message prefix is corrected from "Set PCB Footprint position" to match rotation functionality
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "rotateFootprint",params=params) 



@mcp.tool()
def queryCurrentFrameType()->API_FRAME_PARAMS:
    """
    Asynchronous tool function to query the type of the currently active frame in KiCad EDA tool.
    
    This function calls KiCad's C++ SDK API to fetch the frame type information of the current active window,
    parses the JSON response, and returns it as a typed dictionary (API_FRAME_PARAMS).
    
    Returns:
        Optional[API_FRAME_PARAMS]: 
            - On success: Typed dictionary containing the 'frame_type' field (value from API_FRAME_TYPE_PARAMS)
            - On failure (e.g., missing 'msg' field in response, API call exception): None
    
    Exceptions Handled:
        Catches all general exceptions during API call/JSON parsing, prints error message, and returns None.
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    response : API_QUERY_RESULT = KICAD_CLIENT.cpp_sdk_action( api_name= "queryCurrentFrameType",params={}, cmd_type="cpp_sdk_query")
    if "msg" not in response:
        logger.error("lack msg")
        return None
    library : API_FRAME_PARAMS = json.loads(response["msg"])
    logger.info(f"queryCurrentFrameType result : {library}")
    return library


@mcp.tool()
def closeFrame( params : API_FRAME_PARAMS):
    """
    Asynchronous tool function to close a specific frame window in KiCad EDA tool.
    
    This function calls KiCad's C++ SDK API to close the frame window matching the provided frame type parameters.
    It logs the API response status and returns the raw response from the SDK API for further processing.
    
    Args:
        params: API_FRAME_PARAMS - Typed dictionary containing the 'frame_type' field that specifies
                which type of KiCad frame (e.g., PCB editor, schematic editor) to close.
    
    Returns:
        Optional[Any]: 
            - On API call success: Raw response data from KiCad C++ SDK API (type depends on SDK implementation)
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "closeFrame",params=params) 


@mcp.tool()
def openFrame( params : API_FRAME_PARAMS):
    """
    Asynchronous tool function to open a specific frame window in KiCad EDA tool.
    
    This function invokes KiCad's C++ SDK API to open a new frame window of the specified type (e.g., PCB editor,
    schematic editor, Gerber viewer). It logs the API response status and returns the raw response for further
    validation or processing by the caller.
    
    Args:
        params: API_FRAME_PARAMS - Typed dictionary containing the mandatory 'frame_type' field that specifies
                which type of KiCad frame to open (value from API_FRAME_TYPE_PARAMS enumeration).
    
    Returns:
        Optional[Any]:
            - On successful API call: Raw response data from KiCad C++ SDK API (type depends on SDK implementation,
              typically a dictionary with status/result info)
            - On empty API response: None
            - Note: The function does not raise exceptions (all errors are logged to console).
    
    Side Effects:
        Prints human-readable status messages to the console:
        - If response exists: Logs the API response with frame type context
        - If no response: Logs a warning about invalid/empty API response
    """
    if KICAD_CLIENT is None:
        logger.error( "Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "openFrame",params=params)

@mcp.tool()
def saveFrame():
    """
    Saves the current KiCad frame (schematic/PCB) to persistent storage via CPP SDK.
    
    This function calls the KiCad CPP SDK's `saveFrame` API through the pre-initialized
    KICAD_CLIENT instance, which persists the current state of the frame (e.g., schematic frame, 
    PCB frame) to the corresponding file/storage system.
    
    Returns:
        Optional[Dict]: Parsed JSON response from KiCad CPP SDK if the frame save succeeds,
                        containing status and detailed frame save information; 
                        None if the client is uninitialized or the save operation fails.
    
    Raises:
        None: All exceptions are caught and logged internally, no explicit raise.
    
    Notes:
        - Requires the KICAD_CLIENT instance to be properly initialized before calling.
        - The `saveFrame` API requires no additional parameters (empty params dict).
        - Returned dict structure example:
          {
              "status": "ok",
              "msg": {"saved_frame_type": "FRAME_SCH", "save_path": "/path/to/frame.kicad_sch"}
          }
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
    
    return KICAD_CLIENT.cpp_sdk_action( api_name="saveFrame", params={})

@mcp.tool()
def saveAsFrame():
    """
    Saves the current KiCad frame (schematic/PCB) to a user-specified path via CPP SDK (Save As functionality).
    
    This function invokes the KiCad CPP SDK's `saveAs` API through the pre-initialized KICAD_CLIENT instance,
    enabling "Save As" functionality for the current frame (e.g., schematic frame, PCB frame). 
    Unlike the basic `saveFrame` function (which overwrites the existing file), this function allows 
    specifying a new file path/location to save the frame, preserving the original file (if exists).
    
    Returns:
        Optional[Dict]: Parsed JSON response from KiCad CPP SDK if the "Save As" operation succeeds,
                        containing status and detailed save-as information (e.g., target path, frame type);
                        None if the KICAD_CLIENT is uninitialized or the API call fails.
    
    Raises:
        None: All exceptions are caught and logged internally by the underlying `cpp_sdk_action` method,
              no explicit exceptions are raised by this function.
    
    Notes:
        - Requires the KICAD_CLIENT instance to be properly initialized before calling (fails fast if not).
        - The `saveAs` API may require path parameters in production (current params={} is a placeholder;
          update params with target file path when implementing full functionality).
        - Key difference from `saveFrame`: 
          - `saveFrame`: Overwrites the existing file associated with the current frame.
          - `saveAsFrame`: Saves the frame to a new user-defined path (original file remains unchanged).
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
    return KICAD_CLIENT.cpp_sdk_action(api_name="saveAs", params={})


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
    
    Raises:
        None: All exceptions are caught and logged internally by the underlying `cpp_sdk_action` method;
              no explicit exceptions are raised by this function.
    
    Notes:
        - Requires the KICAD_CLIENT instance to be properly initialized before invocation (fails fast if not).
        - The current empty `params={}` is a placeholder; in production, populate it with import parameters
          such as source file path, target project path, or format-specific conversion options (e.g.:
          `params={"file_path": "/path/to/altium_sch.SchDoc", "format": "altium"}`).
        - Supported non-KiCad formats depend on KiCad CPP SDK's `importNonKicadSch` API capabilities
          (common formats: Altium, Eagle, OrCAD, PADS, LTspice).
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")

    return KICAD_CLIENT.cpp_sdk_action( api_name="importNonKicadSch", params={})

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
    
    Raises:
        None: All exceptions are caught and logged internally by the underlying `cpp_sdk_action` method;
              no explicit exceptions are raised by this function.
    
    Notes:
        - Requires the KICAD_CLIENT instance to be properly initialized before invocation (fails fast if not).
        - The empty `params={}` is a placeholder; production use requires populating import parameters:
          e.g., `params={"file_path": "/path/to/logo.svg", "target_layer": "F.SilkS", "scale": 1.0, "rotation": 0}`.
        - Supported vector formats depend on KiCad CPP SDK capabilities (primary: SVG; secondary: EPS/DXF).
        - Imported vector graphics are converted to editable KiCad schematic primitives (lines, curves, polygons).

    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "importVectorGraphic", params={})


@mcp.tool()
def exportNetlist():
    """
    Exports a netlist file from the active KiCad schematic via CPP SDK.
    
    This function serves as a programmatic wrapper for KiCad's "Export Netlist" feature,
    invoking the CPP SDK's `exportNetlist` API through the pre-initialized KICAD_CLIENT instance.
    A netlist is a critical text-based file that describes the electrical connectivity of components
    in the schematic (e.g., component references, pin connections, net names), enabling seamless
    transfer of schematic logic to PCB layout tools.
    
    The exported netlist is compatible with KiCad's PCB editor and other EDA tools, forming the
    bridge between schematic design and PCB layout implementation.
    
    Returns:
        Optional[Dict]: Parsed JSON response from the KiCad CPP SDK if export succeeds, containing
                        status, exported netlist file path, format, and schematic metadata;
                        None if the KICAD_CLIENT is uninitialized or the export operation fails.
    
    Raises:
        None: All exceptions are caught and logged internally by the underlying `cpp_sdk_action` method;
              no explicit exceptions are raised by this function.
    
    Notes:
        - Requires the KICAD_CLIENT instance to be properly initialized before invocation (fails fast if not).
        - The empty `params={}` is a placeholder; production use requires populating export parameters:
          e.g., `params={"file_path": "/path/to/exported_netlist.net", "format": "kicad_net", "include_power_nets": True}`.
        - Supported netlist formats depend on KiCad CPP SDK capabilities (primary: KiCad native .net; secondary: EAGLE, SPICE).
        - Ensure the active schematic is saved and free of connectivity errors before exporting (avoids invalid netlist).
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
    
    return KICAD_CLIENT.cpp_sdk_action( api_name="exportNetlist", params={})


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

    return KICAD_CLIENT.cpp_sdk_action( api_name="schematicSetup", params={})

@mcp.tool()
def openPageSettingDlg():
    """
    Opens the Page Setting dialog for the active KiCad schematic/editor via CPP SDK.
    
    Wraps KiCad's native Page Setting feature, providing access to page-related configurations
    (e.g., page size, orientation, margins, title block settings). Requires KICAD_CLIENT initialization.
    
    Returns:
        Optional[Dict]: Parsed SDK response (dialog status) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")

    return KICAD_CLIENT.cpp_sdk_action( api_name="pageSetting", params={})



@mcp.tool()
def openPrintDlg():
    """
    Opens the Print dialog for the active KiCad schematic/editor via CPP SDK.
    
    Wraps KiCad's native Print feature, providing access to print-related configurations
    (e.g., printer selection, page range, scaling, color mode). Requires KICAD_CLIENT initialization.
    
    Returns:
        Optional[Dict]: Parsed SDK response (dialog status) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")

    return KICAD_CLIENT.cpp_sdk_action( api_name="print", params={})


@mcp.tool()
def openPlotDlg():
    """
    Opens the Plot dialog for the active KiCad schematic/PCB editor via CPP SDK.
    
    Wraps KiCad's native Plot feature, providing access to plot-related configurations
    (e.g., output format (PDF/PNG/SVG), layer selection, plot scale, mirror plot). 
    Requires KICAD_CLIENT initialization.
    
    Returns:
        Optional[Dict]: Parsed SDK response (dialog status) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")

    return KICAD_CLIENT.cpp_sdk_action( api_name="plot", params={})


@mcp.tool()
def closeCurrentFrame():
    """
    Closes the currently open frame module in KiCad via CPP SDK.
    
    Wraps KiCad's native frame closing feature, terminating the active frame (e.g., schematic editor,
    PCB editor, or setup dialog frame) without exiting the entire KiCad application.
    Requires KICAD_CLIENT initialization.
    
    Returns:
        Optional[Dict]: Parsed SDK response (frame close status) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "closeCurrentFrame", params={})


@mcp.tool()
def openFindDialog():
    """
    Opens the Find dialog in the active KiCad editor via CPP SDK.
    
    Wraps KiCad's native Find feature, providing access to text/element search functionality
    (e.g., finding component references, net names, or text strings in schematics/PCB files).
    Requires KICAD_CLIENT initialization.
    
    Returns:
        Optional[Dict]: Parsed SDK response (dialog status) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")

    return KICAD_CLIENT.cpp_sdk_action( api_name= "find", params={})


@mcp.tool()
def openFindAndReplaceDialog():
    """
    Opens the Find and Replace dialog in the active KiCad editor via CPP SDK.
    
    Wraps KiCad's native Find and Replace feature, enabling search and batch replacement of
    text/elements (e.g., component references, net names, text strings in schematics/PCB files).
    Requires KICAD_CLIENT initialization.
    
    Returns:
        Optional[Dict]: Parsed SDK response (dialog status) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")

    return KICAD_CLIENT.cpp_sdk_action( api_name="findReplace", params={})


@mcp.tool()
def deleteTool():
    """
    Launches the interactive delete tool in the active KiCad editor via CPP SDK.
    
    Wraps KiCad's native interactive delete tool functionality, enabling manual selection
    and deletion of schematic/PCB elements (e.g., components, wires, text) through direct
    mouse interaction with the editor canvas. Requires KICAD_CLIENT initialization.
    
    Returns:
        Optional[Dict]: Parsed SDK response (tool launch status) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
    return KICAD_CLIENT.cpp_sdk_action(api_name="deleteTool", params={})

@mcp.tool()
def selectAllItems():
    """
    Selects all items in the active KiCad editor via CPP SDK.
    
    Wraps KiCad's native "Select All" functionality, highlighting all editable elements
    (e.g., components, wires, text, graphical primitives) in the current schematic/PCB file.
    Requires KICAD_CLIENT initialization.
    
    Returns:
        Optional[Dict]: Parsed SDK response (selection status) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
    return KICAD_CLIENT.cpp_sdk_action( api_name="selectAll", params={})

@mcp.tool()
def unSelectAllItems():
    """
    Deselects all currently selected items in the active KiCad editor via CPP SDK.
    
    Wraps KiCad's native "Unselect All" functionality, clearing the selection state of all
    editable elements (e.g., components, wires, text, graphical primitives) in the current
    schematic/PCB file. Requires KICAD_CLIENT initialization.
    
    Returns:
        Optional[Dict]: Parsed SDK response (unselection status) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
    return KICAD_CLIENT.cpp_sdk_action( api_name="unselectAll", params={})


@mcp.tool()
def openEditTextAndGraphicPropertyDialog():
    """
    Opens the Text and Graphic Properties edit dialog in the active KiCad editor via CPP SDK.
    
    Wraps KiCad's native property edit feature, providing access to modify attributes of
    text elements (font, size, color, alignment) and graphical primitives (line width, fill,
    layer, color) in schematics/PCB files. Requires KICAD_CLIENT initialization.
    
    Returns:
        Optional[Dict]: Parsed SDK response (dialog status) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
    return KICAD_CLIENT.cpp_sdk_action(  api_name= "editTextGraphicProperty", params={})


@mcp.tool()
def togglePropertyPanel():
    """
    Toggles the visibility of the property panel in the active KiCad editor via CPP SDK.
    
    Wraps KiCad's native property panel feature to switch its display state: shows the panel
    if it is hidden, and hides it if it is currently visible (first call = show, second call = hide, vice versa).
    The panel displays and allows modification of attributes for selected schematic/PCB elements
    (e.g., component values, text styles, graphical properties like line width or layer).
    
    Requires KICAD_CLIENT initialization before invocation.
    
    Returns:
        Optional[Dict]: Parsed SDK response (panel toggle status, including current visibility) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
    return KICAD_CLIENT.cpp_sdk_action( api_name="propertyPanel", params={})

@mcp.tool()
def toggleSearchPanel():
    """
    Toggles the visibility of the search panel in the active KiCad editor via CPP SDK.
    
    Wraps KiCad's native search panel feature to switch its display state: shows the panel
    if it is hidden, and hides it if it is currently visible (first call = show, second call = hide, vice versa).
    The panel supports real-time search of schematic/PCB elements (e.g., component references, net names, text strings).
    
    Requires KICAD_CLIENT initialization before invocation.
    
    Returns:
        Optional[Dict]: Parsed SDK response (panel toggle status, including current visibility) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
    return KICAD_CLIENT.cpp_sdk_action( api_name="searchPanel", params={})


@mcp.tool()
def toggleHierarchyPanel():
    """
    Toggles the visibility of the hierarchy panel in the active KiCad editor via CPP SDK.
    
    Wraps KiCad's native hierarchy panel feature to switch its display state: shows the panel
    if it is hidden, and hides it if it is currently visible (first call = show, second call = hide, vice versa).
    The hierarchy panel provides navigation for multi-sheet schematic hierarchies in KiCad.
    
    Requires KICAD_CLIENT initialization before invocation.
    
    Returns:
        Optional[Dict]: Parsed SDK response (panel toggle status, including current visibility) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
    return KICAD_CLIENT.cpp_sdk_action( api_name="hierarchyPanel", params = {})


@mcp.tool()
def toggleNetNavigatorPanel():
    """
    Toggles the visibility of the Net Navigator panel in the active KiCad editor via CPP SDK.
    
    Wraps KiCad's native Net Navigator panel feature to switch its display state: shows the panel
    if it is hidden, and hides it if it is currently visible (first call = show, second call = hide, vice versa).
    The Net Navigator panel provides quick navigation and management of electrical nets in schematics/PCB files.
    
    Requires KICAD_CLIENT initialization before invocation.
    
    Returns:
        Optional[Dict]: Parsed SDK response (panel toggle status, including current visibility) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
    return KICAD_CLIENT.cpp_sdk_action( api_name="netNavigatorPanel", params={})


@mcp.tool()
def toggleDesignBlockPanel():
    """
    Toggles the visibility of the Design Block panel in the active KiCad editor via CPP SDK.
    
    Wraps KiCad's native Design Block panel feature to switch its display state: shows the panel
    if it is hidden, and hides it if it is currently visible (first call = show, second call = hide, vice versa).
    The Design Block panel enables management and reuse of modular design blocks in KiCad schematics/PCB projects.
    
    Requires KICAD_CLIENT initialization before invocation.
    
    Returns:
        Optional[Dict]: Parsed SDK response (panel toggle status, including current visibility) or None on failure.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
    return KICAD_CLIENT.cpp_sdk_action( api_name="designBlockPanel", params={})


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
    return KICAD_CLIENT.cpp_sdk_action( api_name="symbolLibraryBrowser",params={})


@mcp.tool()
def zoomView(params : API_ZOOM_PARAMS):
    """
    Adjusts the view zoom of the active KiCad editor based on the specified zoom parameter.
    
    Args:
        params: API_ZOOM_PARAMS enumeration value that defines the zoom behavior:
            - zoomInCenter: Zoom in centered on the canvas middle point
            - zoomOutCenter: Zoom out centered on the canvas middle point
            - zoomFitScreen: Fit all visible content to the editor screen
            - zoomFitObjects: Fit all selected/loaded objects to the editor view
    
    Returns:
        Optional[Dict]: Parsed SDK response (zoom operation status) or None if the client is uninitialized/fails.
    
    Raises:
        None: Logs an error if KICAD_CLIENT is uninitialized but does not raise an exception.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
    return KICAD_CLIENT.cpp_sdk_action(api_name=params.value, params={})


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
    return KICAD_CLIENT.cpp_sdk_action( api_name="showBusSyntaxHelp")

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
    return KICAD_CLIENT.cpp_sdk_action( api_name= "runERC")

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
    return KICAD_CLIENT.cpp_sdk_action( api_name="showSimulator")



def wait_for_kicad_pid(timeout=30):

    import psutil
    import time

    start = time.time()

    while time.time() - start < timeout:
        for proc in psutil.process_iter(['pid', 'name']):
            name = proc.info['name']
            if name and name.lower() in ("kicad.exe", "pcbnew.exe", "eeschema.exe"):
                return proc.info['pid']
        time.sleep(0.5)

    return None

def build_socket_url(pid, editor):
    return f"ipc://kicad_sdk_pair-{pid}-{editor}"


def wait_for_connection(client_cls, socket_url, editor, retries=20):
    for _ in range(retries):
        try:
            return client_cls(socket_url, editor_type=editor)
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Failed to connect to KiCad socket")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="KiCad MCP Server")
    parser.add_argument("--socket-url", help="KiCad SDK socket URL")
    parser.add_argument("--api-key", help="OpenAI API key")
    parser.add_argument("--base-url", help="OpenAI base URL")
    parser.add_argument("--model", help="OpenAI model name")    
    parser.add_argument(
        "--editor-type",
        type=str,
        choices=VALID_EDITORS,
        help="Editor type (schematic, pcb, footprint, symbol)",
    )

    args = parser.parse_args()
    
    # Set environment variables from command-line arguments if provided
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
    if args.base_url:
        os.environ["OPENAI_BASE_URL"] = args.base_url
    if args.model:
        os.environ["OPENAI_MODEL"] = args.model

    socket_url = None
    if args.socket_url:
        socket_url = args.socket_url
    else:
        if not args.editor_type:
            raise RuntimeError("editor-type required when socket_url not provided")

        logger.info("Waiting for KiCad process...")
        pid = wait_for_kicad_pid()

        if not pid:
            raise RuntimeError("KiCad not found")

        socket_url = build_socket_url(pid, args.editor_type)

    logger.info(f"Using socket URL: {socket_url}")

    KICAD_CLIENT = wait_for_connection(
        KiCadClient,
        socket_url,
        args.editor_type
    )

    # Run MCP server
    logger.info("Starting MCP server with stdio transport")
    mcp.run(transport="stdio")
    logger.info("Quitting KiCad MCP SERVER")