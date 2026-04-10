import json
import logging
from kicad_mcp.sdk_api_params import (
    API_ARC_PARAMS,
    API_BEZIER_PARAMS,
    API_CIRCLE_PARAMS,
    API_FRAME_PARAMS,
    API_RECTANGLE_PARAMS,
    API_ZOOM_PARAMS,
    API_QUERY_RESULT,
)

logger = logging.getLogger(__name__)
KICAD_CLIENT = None


def init_context(client, log):
    global KICAD_CLIENT, logger
    KICAD_CLIENT = client
    logger = log


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

    try:
        response: API_QUERY_RESULT = KICAD_CLIENT.cpp_sdk_action(
            api_name="queryCurrentFrameType", params={}, cmd_type="cpp_sdk_query"
        )
        if "msg" not in response:
            logger.error("lack msg")
            return None
        library: API_FRAME_PARAMS = json.loads(response["msg"])
        logger.info(f"queryCurrentFrameType result : {library}")
        return library
    except Exception as e:
        logger.error(f"Error in queryCurrentFrameType: {e}")
        return None


def closeFrame(params: API_FRAME_PARAMS):
    """
    Asynchronous tool function to close a specific frame window in KiCad EDA tool.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="closeFrame", params=params)


def openFrame(params: API_FRAME_PARAMS):
    """
    Asynchronous tool function to open a specific frame window in KiCad EDA tool.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="openFrame", params=params)


def saveFrame():
    """
    Saves the current KiCad frame (schematic/PCB) to persistent storage via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="saveFrame", params={})


def saveAsFrame():
    """
    Saves the current KiCad frame (schematic/PCB) to a user-specified path via CPP SDK (Save As functionality).
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="saveAs", params={})


def openPageSettingDlg():
    """
    Opens the Page Setting dialog for the active KiCad schematic/editor via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="pageSetting", params={})


def openPrintDlg():
    """
    Opens the Print dialog for the active KiCad schematic/editor via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="print", params={})


def openPlotDlg():
    """
    Opens the Plot dialog for the active KiCad schematic/PCB editor via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="plot", params={})


def closeCurrentFrame():
    """
    Closes the currently open frame module in KiCad via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="closeCurrentFrame", params={})


def openFindDialog():
    """
    Opens the Find dialog in the active KiCad editor via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="find", params={})


def openFindAndReplaceDialog():
    """
    Opens the Find and Replace dialog in the active KiCad editor via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="findReplace", params={})


def deleteTool():
    """
    Launches the interactive delete tool in the active KiCad editor via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="deleteTool", params={})


def selectAllItems():
    """
    Selects all items in the active KiCad editor via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="selectAll", params={})


def unSelectAllItems():
    """
    Deselects all currently selected items in the active KiCad editor via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="unselectAll", params={})


def openEditTextAndGraphicPropertyDialog():
    """
    Opens the Text and Graphic Properties edit dialog in the active KiCad editor via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="editTextGraphicProperty", params={})


def togglePropertyPanel():
    """
    Toggles the visibility of the property panel in the active KiCad editor via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="propertyPanel", params={})


def toggleSearchPanel():
    """
    Toggles the visibility of the search panel in the active KiCad editor via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="searchPanel", params={})


def toggleHierarchyPanel():
    """
    Toggles the visibility of the hierarchy panel in the active KiCad editor via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="hierarchyPanel", params={})


def toggleNetNavigatorPanel():
    """
    Toggles the visibility of the Net Navigator panel in the active KiCad editor via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="netNavigatorPanel", params={})


def toggleDesignBlockPanel():
    """
    Toggles the visibility of the Design Block panel in the active KiCad editor via CPP SDK.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="designBlockPanel", params={})


def zoomView(params: API_ZOOM_PARAMS):
    """
    Adjusts the view zoom of the active KiCad editor based on the specified zoom parameter.
    """
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name=params.value, params={})


def draw_circle(circle: API_CIRCLE_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawCircle", params=circle)


def draw_arc(arc: API_ARC_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawArc", params=arc)


def draw_bezier(bezier: API_BEZIER_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawBezier", params=bezier)


def draw_rectangle(rectangle: API_RECTANGLE_PARAMS):
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
