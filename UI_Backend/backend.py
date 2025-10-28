import os
import json
import asyncio
import logging
from quart import Quart, request, Response, jsonify
from quart_cors import cors
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient

logging.basicConfig(level=logging.INFO)
logging.getLogger("mcp_use").setLevel(logging.ERROR)

load_dotenv()

app = Quart(__name__)
app = cors(app, allow_origin="*")
app.url_map.strict_slashes = False  # allows /gemini-mcp/stream and /gemini-mcp/stream/


# --- SSE Helper ---
def sse_event(data, event="message", id=None, retry=None):
    lines = []
    if id is not None:
        lines.append(f"id: {id}")
    if event:
        lines.append(f"event: {event}")
    if retry is not None:
        lines.append(f"retry: {retry}")
    json_data = json.dumps(data) if not isinstance(data, str) else data
    for line in str(json_data).splitlines():
        lines.append(f"data: {line}")
    return "\n".join(lines) + "\n\n"


# --- Agent Creation ---
async def create_agent():
    MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
    client = MCPClient({"mcpServers": {"http": {"url": MCP_SERVER_URL}}})
    await client.create_session("http")

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
    agent = MCPAgent(client=client, max_steps=10, system_prompt=PROMPT, llm=llm, max_retries_per_step=3, verbose=True)
    return agent


# --- POST endpoint (optional, for non-streaming) ---
@app.route("/gemini-mcp", methods=["POST"])
async def gemini_query():
    data = await request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "No query provided"}), 400
    query = data["query"]

    try:
        agent = await create_agent()
        result = await agent.run(query)
        return jsonify({"response": result})
    except Exception as e:
        logging.error(f"Error in gemini_query: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# --- SSE Stream endpoint ---
@app.route("/gemini-mcp/stream", methods=["GET", "OPTIONS"])
async def gemini_stream():
    if request.method == "OPTIONS":
        return "", 204

    query = request.args.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    async def generator():
        event_id = 0
        try:
            agent = await create_agent()
            result = await agent.run(query)
            chunk_size = 50

            for i in range(0, len(result), chunk_size):
                chunk = result[i:i + chunk_size]
                yield sse_event({"chunk": chunk}, id=event_id)
                event_id += 1
                # Yield heartbeat every 2 seconds
                if event_id % 40 == 0:
                    yield sse_event({}, event="ping")
                await asyncio.sleep(0.05)

            yield sse_event({"done": True}, event="complete", id=event_id)

        except Exception as e:
            logging.error(f"Stream error for query '{query[:50]}': {e}", exc_info=True)
            yield sse_event({"error": str(e)}, event="error", id=event_id)

    return Response(
        generator(),
        content_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9009, debug=True, use_reloader=False)


# Right now, the backend is running agent.run(query) all at once, and then splits the full result into chunks.
# That’s why the frontend sees the “streamed” data almost instantly: the LLM finishes generating before you even start sending chunks.
# If you cannot stream directly from the LLM a workaround is the use of asyncio.sleep between chunks to simulate streaming.
# This is not real streaming; the full response is still generated in memory.