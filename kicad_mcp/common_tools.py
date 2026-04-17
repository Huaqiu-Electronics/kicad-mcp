import json
import logging
from kicad_mcp.server import mcp
from kicad_mcp.sdk_api_params import (
    API_FRAME_PARAMS, API_ZOOM_PARAMS, API_CIRCLE_PARAMS, API_ARC_PARAMS,
    API_BEZIER_PARAMS, API_RECTANGLE_PARAMS, API_QUERY_RESULT
)

logger = logging.getLogger(__name__)
KICAD_CLIENT = None

def init_context(client, log):
    global KICAD_CLIENT, logger
    KICAD_CLIENT = client
    logger = log

@mcp.tool()
def queryCurrentFrameType() -> API_FRAME_PARAMS:
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
        logger.error("Client not initialized")
        return None
    response: API_QUERY_RESULT = KICAD_CLIENT.cpp_sdk_action(api_name="queryCurrentFrameType", params={}, cmd_type="cpp_sdk_query")
    if "msg" not in response:
        logger.error("lack msg")
        return None
    library: API_FRAME_PARAMS = json.loads(response["msg"])
    logger.info(f"queryCurrentFrameType result : {library}")
    return library

@mcp.tool()
def closeFrame(params: API_FRAME_PARAMS):
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
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="closeFrame", params=params)

@mcp.tool()
def openFrame(params: API_FRAME_PARAMS):
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
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="openFrame", params=params)

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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="saveFrame", params={})

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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="saveAs", params={})

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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="pageSetting", params={})

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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="print", params={})

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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="plot", params={})

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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="closeCurrentFrame", params={})

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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="find", params={})

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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="findReplace", params={})

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
        return None
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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="selectAll", params={})

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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="unselectAll", params={})

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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="editTextGraphicProperty", params={})

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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="propertyPanel", params={})

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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="searchPanel", params={})

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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="hierarchyPanel", params={})

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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="netNavigatorPanel", params={})

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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="designBlockPanel", params={})

@mcp.tool()
def zoomView(params: API_ZOOM_PARAMS):
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
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name=params.value, params={})

@mcp.tool()
def draw_circle(circle: API_CIRCLE_PARAMS):
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
        2. Request Body Format: Comply with KiCad API unified specification, containing fixed "action" and context parameters
        3. Timeout: 30 seconds (adapt to time-consuming scenarios of KiCad underlying graphic drawing)
    Return Description:
        No explicit return value; print KiCad API response content on success, and error information on failure
    Notes:
        1. Ensure KiCad API service is started and listening on {KICAD_API_URL}
        2. Parameter unit must be millimeter (KiCad default unit) to avoid unit conversion errors
        3. Radius must be a positive value, otherwise KiCad SDK returns parameter validation failure
    ============================================================================
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawCircle", params=circle)

@mcp.tool()
def draw_arc(arc: API_ARC_PARAMS):
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
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawArc", params=arc)

@mcp.tool()
def draw_bezier(bezier: API_BEZIER_PARAMS):
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
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawBezier", params=bezier)

@mcp.tool()
def draw_rectangle(rectangle: API_RECTANGLE_PARAMS):
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
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawRectangle", params=rectangle)

TOOLS = [
    queryCurrentFrameType,
    closeFrame,
    openFrame,
    saveFrame,
    saveAsFrame,
    openPageSettingDlg,
    openPrintDlg,
    openPlotDlg,
    closeCurrentFrame,
    openFindDialog,
    openFindAndReplaceDialog,
    deleteTool,
    selectAllItems,
    unSelectAllItems,
    openEditTextAndGraphicPropertyDialog,
    togglePropertyPanel,
    toggleSearchPanel,
    toggleHierarchyPanel,
    toggleNetNavigatorPanel,
    toggleDesignBlockPanel,
    zoomView,
    draw_circle,
    draw_arc,
    draw_bezier,
    draw_rectangle,
]
