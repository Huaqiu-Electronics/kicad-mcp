import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from typechat import create_openai_language_model


def get_logger():
    # Check DEBUG flag
    KICAD_HQ_DEBUG_COPILOT = os.getenv("KICAD_HQ_DEBUG_COPILOT", "0") == "1"

    # Determine OS-independent writable directory
    if os.name == "nt":  # Windows
        log_dir = os.path.join(
            os.getenv("APPDATA", os.getenv("TEMP", os.getcwd())),
            "kicad-mcp",
            "kicad-mcp",
        )
    else:  # Linux/MacOS
        log_dir = os.path.join(
            os.getenv("XDG_CACHE_HOME", os.path.join(os.getenv("HOME"), ".cache")),
            "kicad-mcp",
            "kicad-mcp",
        )

    # Ensure the log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Configure logging
    log_file = os.path.join(log_dir, "kicad-mcp.log")

    # Always log to stderr to avoid corrupting MCP stdio transport
    console_handler = logging.StreamHandler(sys.stderr)

    # Add file logging only if KICAD_HQ_DEBUG_COPILOT is True
    if KICAD_HQ_DEBUG_COPILOT:
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
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

    return logging.getLogger("kicad-mcp")


def typechat_get_llm(
    model=os.getenv("OPENAI_MODEL") or "gpt-5-mini", api_key=None, base_url=None
):
    llm = create_openai_language_model(
        model=model,
        api_key=api_key or os.getenv("OPENAI_API_KEY") or "",
        endpoint=base_url or os.getenv("OPENAI_BASE_URL") or "",
    )
    llm.timeout_seconds = 60 * 3  # 3 minutes
    return llm


def wait_for_kicad_pid(timeout=30):
    import psutil
    import time

    start = time.time()

    while time.time() - start < timeout:
        for proc in psutil.process_iter(["pid", "name"]):
            name = proc.info["name"]
            if name and name.lower() in ("kicad.exe", "pcbnew.exe", "eeschema.exe"):
                return proc.info["pid"]
        time.sleep(0.5)

    return None


def build_socket_url(pid, editor):
    return f"ipc://kicad_sdk_pair-{pid}-{editor}"


def wait_for_connection(client_cls, socket_url, editor, retries=2):
    import time

    for _ in range(retries):
        try:
            return client_cls(socket_url, editor_type=editor)
        except Exception:
            time.sleep(0.2)
    raise RuntimeError("Failed to connect to KiCad socket")
