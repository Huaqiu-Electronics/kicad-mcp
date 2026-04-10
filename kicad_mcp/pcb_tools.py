import json
import logging
from kicad_mcp_server.sdk_api_params import (
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

def create_pcb_track(params: API_PCB_TRACK_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawPcbTrack", params=params)

def create_pcb_via(params: API_PCB_VIA_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="placePcbVia", params=params)

def create_pcb_pad(params: API_PCB_PAD_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="createPcbPad", params=params)

def move_pcb_pad(params: API_MOVE_PCB_PAD_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="movePcbPad", params=params)

def rotate_pcb_pad(params: API_ROTATE_PCB_PAD):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="rotatePcbPad", params=params)

def modify_pcb_pad_number(params: API_MODIFY_PAD_NUMBER):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="modifyPadNumber", params=params)

def modify_pcb_pad_size(params: API_MODIFY_PAD_SIZE):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="modifyPadSize", params=params)

def modify_pcb_pad_drill_size(params: API_MODIFY_PAD_DRILL_SIZE):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="modifyPadDrillSize", params=params)

def modify_pcb_pad_drill_shape(params: API_MODIFY_PAD_DRILL_SHAPE):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="modifyPadDrillShape", params=params)

def set_pcb_pad_new_position(params: API_SET_PAD_POSITION):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="setPadPosition", params=params)

def query_pcb_layer_names() -> API_PCB_LAYER_NAME_LIST:
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    response: API_QUERY_RESULT = KICAD_CLIENT.cpp_sdk_action(api_name="queryLayerNames", params={}, cmd_type="cpp_sdk_query")
    if "msg" not in response:
        logger.error("lack msg")
        return None
    library: API_PCB_LAYER_NAME_LIST = json.loads(response["msg"])
    return library

def query_pcb_all_footprint_info() -> API_PCB_FOOTPRINT_INFO_LIST:
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    response: API_QUERY_RESULT = KICAD_CLIENT.cpp_sdk_action(api_name="queryAllFootprintInfo", params={}, cmd_type="cpp_sdk_query")
    if "msg" not in response:
        logger.error("lack msg")
        return None
    library: API_PCB_FOOTPRINT_INFO_LIST = json.loads(response["msg"])
    return library

def query_pcb_footprint_info(params: API_PCB_REFERENCE_LIST) -> API_PCB_FOOTPRINT_INFO_LIST:
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    response: API_QUERY_RESULT = KICAD_CLIENT.cpp_sdk_action(api_name="queryFootprintInfo", params=params, cmd_type="cpp_sdk_query")
    if "msg" not in response:
        logger.error("lack msg")
        return None
    library: API_PCB_FOOTPRINT_INFO_LIST = json.loads(response["msg"])
    return library

def move_pcb_footprint(params: API_MOVE_FOOTPRINT_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="moveFootprint", params=params)

def modify_pcb_footprint_reference(params: API_MODIFY_FOOTPRINT_REFERENCE):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="modifyFootprintReference", params=params)

def set_pcb_footprint_position(params: API_SET_FOOTPRINT_POSITION):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="setFootprintPosition", params=params)

def rotate_pcb_footprint(params: API_ROTATE_FOOTPRINT_PARAMS):
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
