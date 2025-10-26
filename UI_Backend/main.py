from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
from gemini_mcp import create_agent


app = FastAPI(
    title="Asynchronous Agent Executor",
    description="Backend for running Gemini and Ollama agents with streaming support.",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic model for request body validation
class QueryRequest(BaseModel):
    query: str


# --- Helper Functions ---

def format_sse(data: str, event: str = None) -> str:
    """Helper function to create SSE formatted messages."""
    msg = f"data: {data}\n"
    if event:
        msg = f"event: {event}\n{msg}"
    return f"{msg}\n"


async def stream_agent_response(agent, query, request: Request = None):
    """Async generator for streaming responses using Server-Sent Events (SSE)."""
    if agent is None:
        yield format_sse(json.dumps({"error": "Agent is not initialized or available"}), event="error")
        return

    try:
        # Check if client disconnected
        if request and await request.is_disconnected():
            print("Client disconnected before streaming started")
            return

        # Check if the agent supports the astream coroutine
        if hasattr(agent, 'astream'):
            async for chunk in agent.astream(query):
                # Check for client disconnect during streaming
                if request and await request.is_disconnected():
                    print("Client disconnected during streaming")
                    break

                # Process the chunk content
                content = None
                if hasattr(chunk, 'content'):
                    content = chunk.content
                elif isinstance(chunk, dict):
                    content = chunk.get("output", str(chunk))
                elif hasattr(chunk, 'get'):
                    content = chunk.get("content", str(chunk))

                if content:
                    yield format_sse(json.dumps({"chunk": content}))

                # Yield control to the event loop
                await asyncio.sleep(0.01)

        elif hasattr(agent, 'run'):
            # Fallback for non-streaming agents with async run
            print("Agent does not support streaming (astream), falling back to run...")
            result = await agent.run(query)

            # Stream the result chunk by chunk as a fallback
            result_str = str(result)
            chunk_size = 50
            for i in range(0, len(result_str), chunk_size):
                # Check for client disconnect
                if request and await request.is_disconnected():
                    print("Client disconnected during fallback streaming")
                    break

                chunk = result_str[i:i + chunk_size]
                yield format_sse(json.dumps({"chunk": chunk}))
                await asyncio.sleep(0.05)
        else:
            raise Exception("Agent does not support streaming or async execution")

        # Only send completion if client is still connected
        if not request or not await request.is_disconnected():
            yield format_sse(json.dumps({"done": True}), event="complete")

    except asyncio.CancelledError:
        print("Stream cancelled by client disconnect")
        raise
    except Exception as e:
        # Stream the error message
        print(f"Streaming error occurred: {e}")
        yield format_sse(json.dumps({"error": str(e)}), event="error")
    finally:
        # Clean up agent resources if it has a cleanup method
        if hasattr(agent, 'cleanup'):
            try:
                await agent.cleanup()
            except Exception as cleanup_error:
                print(f"Cleanup error: {cleanup_error}")


# --- Endpoints ---

# Non-streaming endpoint for Gemini
@app.post("/gemini-mcp", response_model=dict)
async def query_gemini(request_data: QueryRequest):
    query = request_data.query
    agent = None

    try:
        # Create and properly initialize agent
        agent = create_agent()

        # If agent creation is async, await it
        if asyncio.iscoroutine(agent):
            agent = await agent

        # Ensure agent is ready before running
        if hasattr(agent, 'initialize'):
            await agent.initialize()

        result = await agent.run(query)
        return {"response": result}
    except Exception as e:
        print(f"Error in query_gemini: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up agent resources
        if agent and hasattr(agent, 'cleanup'):
            try:
                await agent.cleanup()
            except Exception as cleanup_error:
                print(f"Cleanup error: {cleanup_error}")


# Streaming endpoint for Gemini
@app.post("/gemini-mcp/stream")
async def gemini_stream_endpoint(request_data: QueryRequest, request: Request):
    query = request_data.query

    async def generate():
        agent = None
        try:
            # Send initial connection keepalive
            yield format_sse(json.dumps({"status": "connected"}), event="connection")

            # Create and properly initialize agent
            agent = create_agent()

            # If agent creation is async, await it
            if asyncio.iscoroutine(agent):
                agent = await agent

            # Ensure agent is ready before streaming
            if hasattr(agent, 'initialize'):
                await agent.initialize()

            yield format_sse(json.dumps({"status": "streaming"}), event="status")

            # Stream the response
            async for message in stream_agent_response(agent, query, request):
                yield message

        except asyncio.CancelledError:
            print("Stream generation cancelled")
            # Don't yield error on cancellation, just clean up
        except Exception as e:
            print(f"Error in gemini_stream_endpoint: {e}")
            yield format_sse(json.dumps({"error": str(e)}), event="error")
        finally:
            # Clean up agent resources
            if agent and hasattr(agent, 'cleanup'):
                try:
                    await agent.cleanup()
                except Exception as cleanup_error:
                    print(f"Cleanup error: {cleanup_error}")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream; charset=utf-8",
            "Transfer-Encoding": "chunked",
        }
    )


# Standard way to run FastAPI with uvicorn
if __name__ == "__main__":
    import uvicorn

    print("--- Starting FastAPI server on http://127.0.0.1:9009 ---")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=9009,
        workers=1,
        timeout_keep_alive=60,  # Increased for SSE connections
        timeout_graceful_shutdown=15,
        reload=False,
        log_level="info",
    )