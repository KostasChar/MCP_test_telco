import json
import asyncio
import logging
import inspect
from quart import Quart, request, jsonify, Response
from quart_cors import cors
from gemini_mcp import PROMPT
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
import hashlib
import urllib.parse



logging.getLogger("mcp_use").setLevel(logging.ERROR)
logging.basicConfig(level=logging.INFO)

app = Quart(__name__)
app = cors(app, allow_origin="*")

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

# --- Concurrency Management ---
MAX_CONCURRENT_AGENTS = 5
agent_semaphore = asyncio.Semaphore(MAX_CONCURRENT_AGENTS)

# Shared cache for deduplication - MUST be checked BEFORE any work starts
query_cache = {}
cache_lock = asyncio.Lock()


# --- SSE Helper ---
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
    from mcp_use import MCPAgent, MCPClient
    # from dedup_mcp_client import DedupMCPClient as MCPClient
    # from dedup_mcp_client import create_dedup_agent as MCPAgent

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


# --- Query Key Generation ---
def query_key(query_str):
    """Generate a unique hash for a query string."""
    normalized = str(query_str).strip()
    return hashlib.md5(normalized.encode()).hexdigest()


# --- Execute Query with Proper Deduplication ---
async def cleanup_agent_sessions(agent, key_hash):
    try:
        await asyncio.wait_for(agent.client.close_all_sessions(), timeout=10.0)
        logging.info(f"🔒 Sessions closed for: {key_hash[:8]}...")
    except asyncio.TimeoutError:
        logging.warning(f"⚠️ Session close timeout for: {key_hash[:8]}...")
    except Exception as e:
        logging.warning(f"⚠️ Cleanup failed for {key_hash[:8]}: {e}")


async def execute_query(query_str):
    key = query_key(query_str)

    async with cache_lock:
        if key in query_cache:
            logging.info(f"🔄 Duplicate detected, returning cached task for: {key[:8]}...")
            return await query_cache[key]

        future = asyncio.Future()
        query_cache[key] = future
        logging.info(f"🆕 Starting new task for: {key[:8]}...")

    try:
        async with agent_semaphore:
            agent = await create_agent()
            try:
                if inspect.iscoroutinefunction(agent.run):
                    result = await agent.run(query_str)
                else:
                    result = await asyncio.to_thread(agent.run, query_str)

                while inspect.iscoroutine(result):
                    result = await result

                # --- LOG RAW OUTPUT ---
                result= str(result)
                logging.info(f"📝 Raw agent output for {key[:8]}: {result[:1000]}")  # first 1000 chars


                logging.info(f"✅ Agent completed for: {key[:8]}... ({len(result)} chars)")

                future.set_result(result)
                return result

            except Exception as e:
                future.set_exception(e)
                logging.error(f"❌ Agent error for {key[:8]}: {e}")
                raise

            finally:
                asyncio.create_task(cleanup_agent_sessions(agent, key))

    finally:
        async def remove_cache():
            await asyncio.sleep(5.0)
            async with cache_lock:
                query_cache.pop(key, None)
                logging.info(f"🧹 Cache cleared for: {key[:8]}...")
        asyncio.create_task(remove_cache())


# --- Endpoints ---
@app.route("/gemini-mcp", methods=["POST"])
async def gemini_query():
    data = await request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "No query provided"}), 400

    query = data["query"]
    logging.info(f"📨 Received POST request with query: {query[:50]}...")

    try:
        result = await execute_query(query)
        return jsonify({"response": result})
    except Exception as e:
        logging.error(f"❌ Error in gemini_query for query '{query[:50]}': {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/gemini-mcp/stream", methods=["GET", "POST", "OPTIONS"])
async def gemini_stream():
    if request.method == "OPTIONS":
        return "", 204

    # Get query
    if request.method == "POST":
        data = await request.get_json()
        query = data.get("query") if data else None
    else:
        query = request.args.get("query")

    if not query:
        return jsonify({"error": "No query provided"}), 400

    logging.info(f"📨 Received STREAM request with query: {query[:50]}...")
    chunk_size = 20000

    async def generator():
        event_id = 0
        try:
            # Get full result just like /gemini-mcp
            result = await execute_query(query)
            logging.info(f"📤 Streaming {len(result)} chars for query: {query[:50]}...")

            # Stream in chunks
            for i in range(0, len(result), chunk_size):
                chunk = result[i:i + chunk_size]
                yield sse_event({"chunk": chunk}, id=event_id)
                event_id += 1
                await asyncio.sleep(0.01)  # Yield control

            # Final done event
            yield sse_event({"done": True}, event="complete", id=event_id)
            logging.info(f"✅ Stream complete for: {query[:50]}...")

        except Exception as e:
            logging.error(f"❌ Stream error for query '{query[:50]}': {e}", exc_info=True)
            yield sse_event({"error": str(e)}, event="error", id=event_id)

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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9009, debug=True, use_reloader=False)