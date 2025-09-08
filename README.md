# Dummy Telco Service Backend & MCP Server

This repository contains a **dummy telco backend** and a **FastMCP server** that exposes the backend as MCP tools. It is intended for **development, testing, and reference purposes**.  

> ⚠️ **Note:** These services do **not fully conform** to the official CAMARA APIs. They provide a simplified reference implementation for experimentation.

---

## Table of Contents

- [Overview](#overview)

---

## Overview

1. **Telco Backend (`telco_backend`)**  
   - Provides simulated telco services including:
     - Device Location
     - Quality-on-Demand (QoD) sessions
     - SMS messaging
     - Device reachability
     - Number verification
   
   - Connexion 3.x (ASGI / Starlette-based OpenAPI server)
     -  Swagger UI → http://127.0.0.1:5000/ui/

2. **MCP Server (`mcp_server.py`)**  
   - Wraps the dummy backend as MCP tools using `FastMCP`.
   - Tools allow retrieval of catalog, device location, QoD sessions, SMS sending, reachability checks, and number verification.
      - Streamable HTTP API: http://127.0.0.1:8000
3. **MCP Host / AI assistant (Claude Desktop)**  
   - Use **Claude Desktop** as the MCP client to call the tools exposed by `mcp_server.py`.
   - Streamlit Web UI - 
---
## Demo

![me](https://github.com/KostasChar/MCP_test_telco/blob/main/camara_demo_test.gif)

## MCP Server Testing 
[MCP Inspector](https://modelcontextprotocol.io/legacy/tools/inspector)
