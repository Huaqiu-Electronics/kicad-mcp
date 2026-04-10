import json
import logging
from kicad_mcp_server.sdk_api_params import (
    API_MULTI_LINES_PARAMS, API_HIER_SHEET_PARAMS, API_CLASS_LABEL_PARAMS, API_TEXTBOX_PARAMS, API_TABLE_PARAMS,
    API_LABEL_PARAMS, API_QUERY_SYMBOL, API_QUERY_RESULT,
    API_SYMBOL_LIBARARY_LIST, API_PLACE_SYMBOL, API_MOVE_SYMBOL, API_ROTATE_SYMBOL,
    API_MODIFY_SYMBOL_VALUE, API_MODIFY_SYMBOL_REFERENCE, API_CREATE_SYMBOL_LIBARARY,
    API_CREATE_LIB_SYMBOL_PIN
)
from kicad_mcp_server.schema import API_PLACE_NETLABELS
from typechat import TypeChatJsonTranslator, TypeChatValidator, Failure
from kicad_mcp_server.utils import typechat_get_llm

logger = logging.getLogger(__name__)
KICAD_CLIENT = None

def init_context(client, log):
    global KICAD_CLIENT, logger
    KICAD_CLIENT = client
    logger = log

async def generate_net_labels(net_list: str) -> "API_PLACE_NETLABELS | None":
    """
    Given the full XML representation of a KiCad project, and build its connections using net labels.
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

def place_all_net_labels(nets: API_PLACE_NETLABELS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return
    for net_params in nets["nets"]:
        KICAD_CLIENT.place_net_label(net_params)

def get_current_kicad_project() -> str | None:
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.get_netlist()

def draw_multi_wires(lines: API_MULTI_LINES_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawMultiWire", params=lines)

def draw_multi_buses(lines: API_MULTI_LINES_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawBus", params=lines)


def create_hier_sheet(sheet: API_HIER_SHEET_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawHierSheet", params=sheet)

def create_class_label(label: API_CLASS_LABEL_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="placeClassLabel", params=label)

def create_textbox(textbox: API_TEXTBOX_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawTextbox", params=textbox)

def create_common_text(text: API_LABEL_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawSchematicText", params=text)

def create_table(table: API_TABLE_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="drawTable", params=table)

def create_local_label(label: API_LABEL_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="placeLocalLabel", params=label)

def create_global_label(label: API_LABEL_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="placeGlobalLabel", params=label)

def create_hier_label(label: API_LABEL_PARAMS):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="placeHierLabel", params=label)

def query_symbol_pin(query: API_QUERY_SYMBOL):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    response = KICAD_CLIENT.cpp_sdk_action(api_name="querySymbolPin", params=query, cmd_type="cpp_sdk_query")
    return response

def query_symbol_library() -> API_SYMBOL_LIBARARY_LIST:
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    response: API_QUERY_RESULT = KICAD_CLIENT.cpp_sdk_action(api_name="getSymbolLibrary", params={}, cmd_type="cpp_sdk_query")
    if "msg" not in response:
        logger.error("lack msg")
        return None
    library: API_SYMBOL_LIBARARY_LIST = json.loads(response["msg"])
    return library

def place_symbol(params: API_PLACE_SYMBOL):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="placeSymbol", params=params)

def move_symbol(params: API_MOVE_SYMBOL):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="moveSymbol", params=params)

def rotate_symbol(params: API_ROTATE_SYMBOL):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="rotateSymbol", params=params)

def modify_symbol_value(params: API_MODIFY_SYMBOL_VALUE):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="modifySymbolValue", params=params)

def modify_symbol_reference(params: API_MODIFY_SYMBOL_REFERENCE):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="modifySymbolReference", params=params)

def create_symbol_library(params: API_CREATE_SYMBOL_LIBARARY):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="addSymbolLibrary", params=params)

def create_symbol_pin(params: API_CREATE_LIB_SYMBOL_PIN):
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="addLibSymbolPin", params=params)

def importNonKicadSchematic():
    if KICAD_CLIENT is None:
        logger.error("Client not initialized")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="importNonKicadSch", params={})

def importVectorGraphicsFile():
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="importVectorGraphic", params={})

def exportNetlist():
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="exportNetlist", params={})

def openSchematicSetupDlg():
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="schematicSetup", params={})

def openSymbolLibraryBrowser():
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="symbolLibraryBrowser", params={})

def showBusSyntaxHelp():
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="showBusSyntaxHelp")

def runERCCheck():
    if KICAD_CLIENT is None:
        logger.error("Client not initialize")
        return None
    return KICAD_CLIENT.cpp_sdk_action(api_name="runERC")

def showSpiceSimulator():
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
