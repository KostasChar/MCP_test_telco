# Dummy Telco Service Backend & MCP Server

This repository contains a **dummy telco backend** and a **FastMCP server** that exposes the backend as MCP tools. It is intended for **development, testing, and reference purposes**.  

> ⚠️ **Note:** These services do **not fully conform** to the official CAMARA APIs. They provide a simplified reference implementation for experimentation.

---

## Table of Contents

- [Overview](#overview)

---

## Overview

1. **Telco Backend (`Telco_backend`)**  
   - Provides simulated telco services including:
     - Device Location
     - Quality-on-Demand (QoD) sessions
     - SMS messaging
     - Device reachability
     - Number verification
   
   - Connexion 3.x (ASGI / Starlette-based OpenAPI server)
     -  Swagger UI → http://127.0.0.1:5000/ui/

2. **MCP Server (`MCP_server`)**  
   - Wraps the dummy backend as MCP tools using `FastMCP`.
   - Tools allow retrieval of catalog, device location, QoD sessions, SMS sending, reachability checks, and number verification.
      - Streamable HTTP API: http://127.0.0.1:8000
     
3. **MCP Host / AI assistant (Claude Desktop)**  
   - Use **Claude Desktop** as the MCP client to call the tools exposed by `MCP_server`.
   - Streamlit Web UI & MCP Client & Ollama - (`AI_Assistant`)
     - Install Ollama locally 

4. **HTTP Backend (to be integrated with custom front-ends)**
   - Custom MCP agent that has tool access based on mcp-use library (leverages http-streamable for mcp communication).
   - Streaming - ongoing conversations/streams → needs async loop (Quart).
     - Supports also SSE endpoints 
---
## How to Run
   - Telco_backend and MCP_server: python app.py and python mcp_server.py
   - MCP Host / AI Assistant
     - Custom AI_assistant: streamlit run app.py
     - [Claude Desktop](https://claude.ai/download): edit_claude_desktop_config.json
       - Use stdio connectivity with MCP server, in case of Streamable HTTP API errors 
     -  [Open WebUI](https://openwebui.com/): Open WebUI is an extensible, feature-rich, and user-friendly self-hosted AI platform designed to operate entirely offline.
        - [mcpo](https://github.com/open-webui/mcpo): Expose any MCP tool as an OpenAPI-compatible HTTP server—instantly.
          - e.g. `mcpo --port 8001 --api-key "top-secret" --server-type "streamable-http" -- http://127.0.0.1:8000/mcp`
     -  [Cherry Studio](https://www.cherry-ai.com/)
     - UI-Backend: python backend.py 



## Demo

![me](https://github.com/KostasChar/MCP_test_telco/blob/main/camara_demo_test.gif)

## MCP Server Testing 
[MCP Inspector](https://modelcontextprotocol.io/legacy/tools/inspector)
