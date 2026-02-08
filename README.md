# KiCad MCP

We are integrating MCP into KiCad, issues and pull requests are welcome.

## Features

**Full MCP support Out of the box**
**Built-in KiCad MCP Server**

## Give it a try

1. Download the [KiCad Huaqiu Distribution 9.0.7-rc3 ](https://github.com/Huaqiu-Electronics/kicad-win-builder/releases/download/9.0.7-rc3/kicad-huaqiu-9.0.7-rc3-x86_64.exe), you can also find a portable version on the [github release page](https://github.com/Huaqiu-Electronics/kicad-win-builder/releases/tag/9.0.7-rc3)

The production ready one shall be shipped with the release of KiCad 10.

**Install for user while using the installer or use the portable version and extract to writable directory**

Or the KiCad MCP Server will fail to initialize due to missing write permission while installing the python package.

2. Open either the PCB or Schematic editor, click the "Robot" button to toggle the Copilot panel
3. Click the Settings (Gear) button, paste your OpenAI API key. There shall be an existing built-int KiCad MCP Server available.

## Architecture

![KiCad MCP Core Components](docs/kicad-mcp.svg)

### KiCad MCP Client

The KiCad Client now has the full MCP capabilities by embedding the [mcp-agent](https://github.com/lastmile-ai/mcp-agent).

KiCad editors( PCB/ Schematic) will atomically start a [KiCad MCP Client](https://github.com/Huaqiu-Electronics/kicad-mcp-client) instance on launch and pass both the dual-communicating IPC channel and the KiCad IPC API url to it.


### KiCad IPC API

The KiCad IPC API forms the backbone of KiCad MCP, and is what makes it standout from the other MCP clients, we are planing to adding more scenarios driven APIs to it.

Checkout the source code of [KiCad](https://gitlab.com/kicad/code/kicad/) or [KiCad Huaqiu-Electronics Distribution](https://gitlab.com/kicad-hq/kicad/-/tree/release/9.0) if you are interested in developing the KiCad IPC API. Our fork has always been keeping up to date with the latest KiCad release branch, all the upstream changes are merged into it.

### KiCad MCP Server

[KiCad MCP Server](https://github.com/Huaqiu-Electronics/kicad-mcp-server) exposes the KiCad IPC API as MCP tools based on the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk).

Currently there are [72 tools](https://github.com/Huaqiu-Electronics/kicad-mcp-server/blob/main/main.py) available, more will be added in the future.

### The Frontend

We host [NextChat](https://github.com/ChatGPTNextWeb/NextChat) on [our server](https://chat.eda.cn) as the frontend, it interacts with the KiCad through the webview IPC API while KiCad forwards the messages between the UI and the mcp-agent.

## Development

### KiCad IPC API

Follow the [official KiCad Development Guide](https://dev-docs.kicad.org/en/getting-started/index.html)

### KiCad MCP Server

1. Locate the local KiCad MCP Server installation directory

2. Clone the repo and replace the entire directory

```bash
cd /path/to/kicad-installation-directory # %LOCALAPPDATA%\Programs\KiCad\9.0\bin if installed for user
rm -rf ./kicad-mcp-server
git clone https://github.com/Huaqiu-Electronics/kicad-mcp-server.git
```

Don't forget to commit your changes and open a pull request.


## Troubleshooting

### Empty KiCad MCP TOOLs

If you found that the KiCad MCP Tools are empty, follow the steps below to fix it.

1. Ensure the installation directory is writable
2. If you have config mirror for the python pip command, ensure the mirror has not banned your IP. The MCP SDKs pulls a lot of python packages on first launch.

### Enabling new MCP Servers added

While new MCP Servers are disabled by default, you can check and enable them by clicking the button besides the attachment icon in the input box.