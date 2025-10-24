
#  MCP Dummy CAMARA Proxy

##  Overview

This project implements an MCP server that exposes **CAMARA-compliant APIs** through the [`fastmcp`](https://pypi.org/project/fastmcp/) framework allowing integration with AI agents and enabled agentic workflows.

It serves as a proxy and validation layer between **CAMARA APIs** and **MCP tools**, allowing interoperability and experimentation with CAMARA API models, or custom Pydantic models when no CAMARA equivalent exists.

---

## 📁 Project Structure

```
MCP_dummy_Camara/
├── app.py
├── .env
├── requirements.txt
├── json_templates/       # CAMARA API request/response templates (interpolated by user input)
├── models/               # Pydantic models for CAMARA API compliance or custom types
├── tools/                # MCP tools registered as callable endpoints
│   ├── qod.py            # Quality of Delivery (QoD) related tools
│   └── edge_application.py  # Edge application discovery tools
```

---

## ⚙️ Installation

### Option 1

```
git clone https://github.com/your-username/MCP_dummy_Camara.git
cd MCP_dummy_Camara
python3 -m venv venv
source venv/bin/activate  # (on Linux/macOS) venv\Scripts\activate     # (on Windows)
pip install -r requirements.txt

Create a `.env` file in the project root (if not already present) and set your API configuration:
MCP_HOST=127.0.0.1
MCP_PORT=8000

DUMMY_BACKEND_URL=http://127.0.0.1:8081
ISI_URL=http://isiath.duckdns.org:8081/oeg/1.0.0
```

These define where the MCP server will listen for requests.

---

## 🚀 Running the Server

Run the application with:

```
python3 app.py
```

By default, it  on `127.0.0.1:8000`.

---

## 🧰 Registered Tools

All MCP tools are explicitly registered in `app.py` for safety and traceability:

| Tool                  | File                        | Description                              |
| --------------------- | --------------------------- | ---------------------------------------- |
| `create_qod_session`  | `tools/qod.py`              | Creates a CAMARA QoD session             |
| `get_qod_session`     | `tools/qod.py`              | Retrieves QoD session details            |
| `delete_qod_session`  | `tools/qod.py`              | Deletes an existing QoD session          |
| `get_app_definitions` | `tools/edge_application.py` | Retrieves available edge app definitions |

---

## 🧠 JSON Templates and Models

* **`json_templates/`**: Contains CAMARA-compatible JSON structures that act as request/response templates.
  These are dynamically **interpolated** using user input before being sent to the MCP or CAMARA endpoint.

* **`models/`**: Contains **Pydantic models** that mirror CAMARA API specifications from
  [CAMARA API to MCP Mapping](https://lf-camaraproject.atlassian.net/wiki/spaces/CAM/pages/222691579/CAMARA+API+to+MCP+Tool+Mapping).
  If a CAMARA mapping doesn’t exist, **custom models** are defined to maintain schema integrity.

---

## 🧩 Extending the Project

To add a new tool:
1. Define Pydantic models for request, response data schema validation.
2. Define the tool in `tools/your_tool.py`.
3. Decorate it with the `@app.tool()` decorator in `app.py`:

   ```python
   from MCP_dummy_Camara.tools.your_tool import new_function
   app.tool()(new_function)
   ```
4. Add corresponding models and JSON templates if needed.

---




