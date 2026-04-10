from enum import Enum
from typing_extensions import TypedDict, List


class KiCadCommand(str, Enum):
    """KiCad SDK commands"""

    NET_LIST = "netlist"
    PLACE_NET_LABELS = "placeNetLabels"


class API_PLACE_NETLABEL_PIN(TypedDict):
    """Pin information for net label placement"""

    designator: str
    pin_num: int


class API_PLACE_NETLABEL_PARAMS(TypedDict):
    """Parameters for placing net labels"""

    net_name: str
    pins: List[API_PLACE_NETLABEL_PIN]


class API_PLACE_NETLABELS(TypedDict):
    """Container for multiple net label placements"""

    nets: List[API_PLACE_NETLABEL_PARAMS]
