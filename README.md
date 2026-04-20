# kicad-mcp

KiCad MCP integrated with the KiCad IPC API.

[![PyPI version](https://badge.fury.io/py/kicad-mcp.svg)](https://pypi.org/project/kicad-mcp/)
[![License](https://img.shields.io/pypi/l/kicad-mcp.svg)](https://github.com/Huaqiu-Electronics/kicad-mcp/blob/main/LICENSE)
---

## Usage

### Run the latest release

You can run the MCP server directly without installing it using `uvx`:

```bash
uvx kicad-mcp --editor-type schematic
```

This will download and execute the latest version from PyPI in an isolated environment.

---

### MCP client configuration 

1. Claude Code

```json
{
	"mcpServers": {
		"Kicad-Schematic-MCP": {
			"type": "stdio",
			"command": "uvx",
			"args": [
				"kicad-mcp",
				"--editor-type",
				"schematic"
			]
		},
		"Kicad-PCB-MCP": {
			"type": "stdio",
			"command": "uvx",
			"args": [
				"kicad-mcp",
				"--editor-type",
				"pcb"
			]
		}
	},
	"inputs": []
}
```

2. VSCode

Add the following configuration to your MCP client:

```json
{
	"servers": {
		"Kicad-Schematic-MCP": {
			"type": "stdio",
			"command": "uvx",
			"args": [
				"kicad-mcp",
				"--editor-type",
				"schematic"
			]
		},
		"Kicad-PCB-MCP": {
			"type": "stdio",
			"command": "uvx",
			"args": [
				"kicad-mcp",
				"--editor-type",
				"pcb"
			]
		}
	},
	"inputs": []
}
```

---

3. Cherry Studio

![Cherry Studio Setup](https://raw.githubusercontent.com/Huaqiu-Electronics/kicad-mcp/main/docs/setup-in-cherry-studio.png)
---

### Options

`--editor-type` supports:

- `schematic`
- `pcb`
- `symbol`
- `footprint`

---

## Development

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd kicad-mcp
```

---

### 2. Configure MCP client (local development)

Example configuration in VSCode:

```json
{
  "servers": {
    "kicad-pcb-mcp": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "C:/code/kicad-mcp",
        "run",
        "kicad-mcp",
        "--editor-type",
        "pcb"
      ]
    },
    "kicad-schematic-mcp": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "C:/code/kicad-mcp",
        "run",
        "kicad-mcp",
        "--editor-type",
        "schematic"
      ]
    }
  }
}
```

---

### 3. Run locally

Install dependencies and run:

```bash
uv sync
uv run kicad-mcp --editor-type schematic
```

---

### 4. Iterate

Modify the code and restart your MCP client to see changes.

---

## Notes

- Requires `uv`: https://github.com/astral-sh/uv  
- Python 3.11+
- Ensure KiCad is running with IPC enabled

---
