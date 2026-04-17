import json
import logging
from kicad_mcp.server import mcp
from kicad_mcp.sdk_api_params import (
    API_PCB_TRACK_PARAMS, API_PCB_VIA_PARAMS, API_PCB_PAD_PARAMS,
    API_MOVE_PCB_PAD_PARAMS, API_ROTATE_PCB_PAD, API_MODIFY_PAD_NUMBER,
    API_MODIFY_PAD_SIZE, API_MODIFY_PAD_DRILL_SIZE, API_MODIFY_PAD_DRILL_SHAPE,
    API_SET_PAD_POSITION, API_QUERY_RESULT, API_PCB_LAYER_NAME_LIST,
    API_PCB_FOOTPRINT_INFO_LIST, API_PCB_REFERENCE_LIST, API_MOVE_FOOTPRINT_PARAMS,
    API_MODIFY_FOOTPRINT_REFERENCE, API_SET_FOOTPRINT_POSITION, API_ROTATE_FOOTPRINT_PARAMS
)

logger = logging.getLogger(__name__)
KICAD_CLIENT = None

def init_context(client, log):
    global KICAD_CLIENT, logger
    KICAD_CLIENT = client
    logger = log

@mcp.tool()
def create_pcb_track(params: API_PCB_TRACK_PARAMS):
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
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawPcbTrack", params=params)

@mcp.tool()
def create_pcb_via(params: API_PCB_VIA_PARAMS):
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
          - MICROVIAs only connect adjacent copper layers (e.g., F_Cu \u2194 In1_Cu);
          - BLIND_BURIED vias connect outer \u2194 inner or inner \u2194 inner layers (no outer layer exposure for buried).
        - An empty response indicates invalid parameters (e.g., invalid layer combination) or KiCad SDK communication failures.
        - This function is registered as an MCP tool and can be invoked by AI agents in KiCad's MCP workflow.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="placePcbVia", params=params)

@mcp.tool()
def create_pcb_pad(params: API_PCB_PAD_PARAMS):
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
        - An empty response indicates invalid parameters (e.g., empty_pad_number) or KiCad SDK communication failures.
        - This function is registered as an MCP tool and can be invoked by AI agents in KiCad's MCP workflow.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="createPcbPad", params=params)

@mcp.tool()
def move_pcb_pad(params: API_MOVE_PCB_PAD_PARAMS):
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
        - An empty response indicates invalid parameters (e.g., empty_pad_number) or KiCad SDK communication failures.
        - This function is registered as an MCP tool and can be invoked by AI agents in KiCad's MCP workflow.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="movePcbPad", params=params)

@mcp.tool()
def rotate_pcb_pad(params: API_ROTATE_PCB_PAD):
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
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="rotatePcbPad", params=params)

@mcp.tool()
def modify_pcb_pad_number(params: API_MODIFY_PAD_NUMBER):
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
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="modifyPadNumber", params=params)

@mcp.tool()
def modify_pcb_pad_size(params: API_MODIFY_PAD_SIZE):
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
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="modifyPadSize", params=params)

@mcp.tool()
def modify_pcb_pad_drill_size(params: API_MODIFY_PAD_DRILL_SIZE):
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
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="modifyPadDrillSize", params=params)

@mcp.tool()
def modify_pcb_pad_drill_shape(params: API_MODIFY_PAD_DRILL_SHAPE):
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
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="modifyPadDrillShape", params=params)

@mcp.tool()
def set_pcb_pad_new_position(params: API_SET_PAD_POSITION):
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
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="setPadPosition", params=params)

@mcp.tool()
def query_pcb_layer_names() -> API_PCB_LAYER_NAME_LIST:
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
        logger.error("Client not initialized")
        return None
    response: API_QUERY_RESULT = KICAD_CLIENT.cpp_sdk_action(api_name="queryLayerNames", params={}, cmd_type="cpp_sdk_query")
    if "msg" not in response:
        logger.error("lack msg")
        return None
    library: API_PCB_LAYER_NAME_LIST = json.loads(response["msg"])
    return library

@mcp.tool()
def query_pcb_all_footprint_info() -> API_PCB_FOOTPRINT_INFO_LIST:
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
        logger.error("Client not initialized")
        return None
    response: API_QUERY_RESULT = KICAD_CLIENT.cpp_sdk_action(api_name="queryAllFootprintInfo", params={}, cmd_type="cpp_sdk_query")
    if "msg" not in response:
        logger.error("lack msg")
        return None
    library: API_PCB_FOOTPRINT_INFO_LIST = json.loads(response["msg"])
    return library

@mcp.tool()
def query_pcb_footprint_info(params: API_PCB_REFERENCE_LIST) -> API_PCB_FOOTPRINT_INFO_LIST:
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
        logger.error("Client not initialized")
        return None
    response: API_QUERY_RESULT = KICAD_CLIENT.cpp_sdk_action(api_name="queryFootprintInfo", params=params, cmd_type="cpp_sdk_query")
    if "msg" not in response:
        logger.error("lack msg")
        return None
    library: API_PCB_FOOTPRINT_INFO_LIST = json.loads(response["msg"])
    return library

@mcp.tool()
def move_pcb_footprint(params: API_MOVE_FOOTPRINT_PARAMS):
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
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="moveFootprint", params=params)

@mcp.tool()
def modify_pcb_footprint_reference(params: API_MODIFY_FOOTPRINT_REFERENCE):
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
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="modifyFootprintReference", params=params)

@mcp.tool()
def set_pcb_footprint_position(params: API_SET_FOOTPRINT_POSITION):
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
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="setFootprintPosition", params=params)

@mcp.tool()
def rotate_pcb_footprint(params: API_ROTATE_FOOTPRINT_PARAMS):
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
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="rotateFootprint", params=params)

TOOLS = [
    create_pcb_track,
    create_pcb_via,
    create_pcb_pad,
    move_pcb_pad,
    rotate_pcb_pad,
    modify_pcb_pad_number,
    modify_pcb_pad_size,
    modify_pcb_pad_drill_size,
    modify_pcb_pad_drill_shape,
    set_pcb_pad_new_position,
    query_pcb_layer_names,
    query_pcb_all_footprint_info,
    query_pcb_footprint_info,
    move_pcb_footprint,
    modify_pcb_footprint_reference,
    set_pcb_footprint_position,
    rotate_pcb_footprint,
]
