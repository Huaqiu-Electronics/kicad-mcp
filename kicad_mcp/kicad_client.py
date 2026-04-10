from typing import Any
import logging
import time
import base64
import xml.etree.ElementTree as ET
import pynng
import json

from kicad_mcp.schema import API_PLACE_NETLABEL_PARAMS, KiCadCommand
from kicad_mcp.valid_editors import VALID_EDITORS


logger = logging.getLogger(__name__)


class KiCadClient:
    def __init__(self, socket_url: str, editor_type: str):
        if editor_type not in VALID_EDITORS:
            raise ValueError(f"Invalid editor type. Must be one of {VALID_EDITORS}")

        self.editor_type = editor_type
        self.socket_url = socket_url

        logger.info(f"Initializing KiCadClient with socket URL: {socket_url}")

        self.req_socket = pynng.Req0(recv_timeout=30000, send_timeout=30000)

        self._connect_with_retry()

    def _connect_with_retry(self, retries=2, delay=0.2):
        for i in range(retries):
            try:
                # force blocking connect
                self.req_socket.dial(self.socket_url, block=True)
                logger.info(f"Connected to KiCad SDK at: {self.socket_url}")
                return
            except pynng.exceptions.ConnectionRefused:
                logger.debug(f"Connection attempt {i + 1} failed, retrying...")
                time.sleep(delay)

        raise RuntimeError(f"Failed to connect to KiCad SDK: {self.socket_url}")

    def get_netlist(self) -> str | None:
        """Get the complete XML representation of the current KiCad project"""
        try:
            logger.info("Sending netlist request to KiCad SDK")
            # Send netlist request
            request = {"cmd": KiCadCommand.NET_LIST.value}

            # Send JSON request
            self.req_socket.send(json.dumps(request).encode())
            logger.debug(f"Sent netlist request: {request}")

            # Receive response
            response_data = self.req_socket.recv()
            response = json.loads(response_data.decode())
            logger.debug(f"Received netlist response: {response}")

            netlist = response.get("net_list")
            if not netlist:
                logger.warning("No net_list found in response")
                return None

            xml_content = base64.b64decode(netlist).decode("utf-8")

            try:
                root = ET.fromstring(xml_content)
                nets_section = root.find("nets")
                if nets_section is not None:
                    root.remove(nets_section)

                # Serialize the cleaned XML back to string
                cleaned_xml = ET.tostring(
                    root, encoding="utf-8", xml_declaration=True
                ).decode("utf-8")
                return cleaned_xml

            except ET.ParseError as e:
                logger.error(f"XML parsing failed: {e}")
                return xml_content

        except pynng.exceptions.Timeout:
            logger.error("Timeout while calling netlist command")
            return None
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None

    def place_net_label(self, net_params: API_PLACE_NETLABEL_PARAMS):
        """Send a single net label placement request to the KiCad SDK server"""
        try:
            net_name = net_params["net_name"]
            logger.info(f"Placing net label for: {net_name}")
            # Create request payload
            request = {
                "cmd": KiCadCommand.PLACE_NET_LABELS.value,
                "params": {"action": "place_netlabels", "context": net_params},
            }

            # Send JSON request
            self.req_socket.send(json.dumps(request).encode())
            logger.debug(f"Sent place net label request for {net_name}: {request}")

            # Receive response
            response_data = self.req_socket.recv()
            response = json.loads(response_data.decode())

            logger.info(f"Place net labels response: {response}")
        except pynng.exceptions.Timeout:
            logger.error(f"Timeout while placing net '{net_params['net_name']}'")
        except Exception as e:
            logger.error(f"Failed to place net '{net_params['net_name']}': {e}")

    def __del__(self):
        """Clean up the NNG socket"""
        try:
            self.req_socket.close()
            logger.info("Closed KiCad SDK NNG socket")
        except Exception as e:
            logger.error(str(e))

    def cpp_sdk_action(
        self, api_name: str, params: Any = {}, cmd_type: str = "cpp_sdk_action"
    ) -> Any:
        """
        Common asynchronous function to call KiCad CPP SDK API via HTTP POST request
        ----------
        Parameters:
        api_name : str
            Name of the KiCad CPP SDK interface to call (e.g., "drawTable", "drawCircle")
        params : dict[str, Any]
            Strongly typed parameters corresponding to the target API (e.g., API_TABLE_PARAMS)
        timeout : float, optional
            Request timeout in seconds, default 30.0
        ----------
        Returns:
        dict | None
            Response JSON data from KiCad API if success, None if failure
        ----------
        Exceptions:
        Prints detailed error logs for all exception scenarios (connection failure, timeout, HTTP error, etc.)
        """
        try:
            logger.info(f"cpp_sdk_action for: {api_name}")
            request = {
                "cmd": cmd_type,
                "params": {
                    "action": "cpp_sdk_api",
                    "context": {"api": api_name, "parameter": params},
                },
            }
            logger.info(f"request for: {request}")
            # Send JSON request
            self.req_socket.send(json.dumps(request).encode())
            # logger.info(f"cpp_sdk_action {api_name}: {request}")

            # Receive response
            response_data = self.req_socket.recv()
            logger.info(f"response : {response_data}")
            response = json.loads(response_data.decode())

            logger.info(f"cpp_sdk response: {response}")
            return response
        except pynng.exceptions.Timeout:
            logger.error(f"Timeout while cpp_sdk '{api_name}'")
            return None
        except Exception as e:
            logger.error(f"Failed to cpp_sdk '{api_name}': {e}")
            return None
