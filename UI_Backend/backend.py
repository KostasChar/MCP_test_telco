import json
import asyncio
import logging
from quart import Quart, request, jsonify, Response
from quart_cors import cors
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient
import objgraph

logging.getLogger("mcp_use").setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO)

app = Quart(__name__)
app = cors(app, allow_origin="*")

load_dotenv()


#--- SSE Helper ---
def sse_event(data, event="message", id=None, retry=None):
    lines = []
    if id is not None:
        lines.append(f"id: {id}")
    if event is not None:
        lines.append(f"event: {event}")
    if retry is not None:
        lines.append(f"retry: {retry}")

    if isinstance(data, str):
        for line in data.splitlines():
            lines.append(f"data: {line}")
    else:
        json_data = json.dumps(data)
        for line in json_data.splitlines():
            lines.append(f"data: {line}")

    return "\n".join(lines) + "\n\n"


# --- Agent Creation ---
async def create_agent():
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

    fresh_client = MCPClient({
        "mcpServers": {
            "http": {"url": MCP_SERVER_URL}
        }
    })

    # Automatically create a session for the server "http"
    await fresh_client.create_session("http")

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    MODEL_NAME = os.getenv("GEMINI_MODEL_NAME")
    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0, google_api_key=GOOGLE_API_KEY)

    PROMPT = """
    You are an intelligent assistant that uses available tools to respond to user requests.

    Instructions:
    1. Identify the appropriate tool for the task.
    2. Respond with the tool's result in natural language summarizing.
    3. Provide any helpful context or next steps based on the result.

    """
    agent = MCPAgent(
        client=fresh_client,
        max_steps=10,
        system_prompt=PROMPT,
        llm=llm,
        max_retries_per_step=3,
        verbose=True
    )
    return agent

# --- Endpoints ---
@app.route("/gemini-mcp", methods=["POST"])
async def gemini_query():
    data = await request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "No query provided"}), 400

    query = data["query"]
    logging.info(f"📨 Received POST request with query: {query[:50]}...")

    agent = await create_agent()
    try:
        result = await agent.run(query)
        return jsonify({"response": result})
    except Exception as e:
        logging.error(f"❌ Error in gemini_query for query '{query[:50]}': {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        await agent.close()
        logging.info("🧹 Agent closed after request")



@app.route("/gemini-mcp/stream", methods=["GET", "POST", "OPTIONS"])
async def gemini_stream():
    if request.method == "OPTIONS":
        return "", 204

    query = None
    if request.method == "POST":
        data = await request.get_json()
        query = data.get("query") if data else None
    else:
        query = request.args.get("query")

    if not query:
        return jsonify({"error": "No query provided"}), 400

    logging.info(f"📨 Received STREAM request with query: {query[:50]}...")
    chunk_size = 50

    async def generator():
        event_id = 0
        agent = await create_agent()
        try:
            result = await agent.run(query)
            logging.info(f"📤 Streaming {len(result)} chars for query: {query[:50]}...")

            for i in range(0, len(result), chunk_size):
                chunk = result[i:i + chunk_size]
                yield sse_event({"chunk": chunk}, id=event_id)
                event_id += 1
                await asyncio.sleep(0.01)  # Yield control

            yield sse_event({"done": True}, event="complete", id=event_id)
            logging.info(f"✅ Stream complete for: {query[:50]}...")

        except Exception as e:
            logging.error(f"❌ Stream error for query '{query[:50]}': {e}", exc_info=True)
            yield sse_event({"error": str(e)}, event="error", id=event_id)

        finally:
            await agent.close()
            logging.info("🧹 Agent closed after streaming")

    return Response(
        generator(),
        content_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )



@app.route("/health", methods=["GET"])
async def health_check():
    return jsonify({"status": "healthy", "service": "gemini-mcp"})

@app.route("/debug/objgraph", methods=["GET"])
async def debug_objgraph():
    import io
    import sys
    import objgraph

    buf = io.StringIO()
    sys.stdout = buf
    objgraph.show_growth(limit=10)
    sys.stdout = sys.__stdout__

    return Response(buf.getvalue(), mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9009, debug=False, use_reloader=False)

