# kicad-mcp

Kicad MCP Sever integrated with KiCad IPC API

## Usage

### Debug locally

1. Clone this repository say `C:/code/kicad-mcp`

2. Configure the mcp settings in your preferred MCP client (e.g. vscode)

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
