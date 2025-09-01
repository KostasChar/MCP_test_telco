# Dummy Telco Service Backend & MCP Server

This repository contains a **dummy telco backend** and a **FastMCP server** that exposes the backend as MCP tools. It is intended for **development, testing, and reference purposes**.  

> ⚠️ **Note:** These services do **not fully conform** to the official CAMARA APIs. They provide a simplified reference implementation for experimentation.

---

## Table of Contents

- [Overview](#overview)

---

## Overview

1. **Dummy Telco Backend (`dummy_telco_backend.py`)**  
   - Provides simulated telco services including:
     - Device Location
     - Quality-on-Demand (QoD) sessions
     - SMS messaging
     - Device reachability
     - Number verification
   - Implemented in Flask, returns static or simulated data.

2. **MCP Server (`mcp_server.py`)**  
   - Wraps the dummy backend as MCP tools using `FastMCP`.
   - Tools allow retrieval of catalog, device location, QoD sessions, SMS sending, reachability checks, and number verification.
   
3. **MCP Client (Claude Desktop)**  
   - Use **Claude Desktop** as the MCP client to call the tools exposed by `mcp_server.py`.
---
## Demo

![me](https://github.com/KostasChar/MCP_test_telco/blob/main/camara_demo_test.gif)

## MCP Server Testing 
[MCP Inspector](https://modelcontextprotocol.io/legacy/tools/inspector)
