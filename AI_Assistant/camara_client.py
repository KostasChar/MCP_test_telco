"""
Core logic for the CAMARA MCP Client.
Handles interaction with Ollama, MCP, and the LlamaIndex agent.
"""

import asyncio
import streamlit as st
import nest_asyncio
import threading
import queue
from typing import Optional, List, Dict, Any, Tuple

from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.agent.workflow import FunctionAgent, ToolCallResult, ToolCall
from llama_index.core.workflow import Context

# Apply nest_asyncio to allow asyncio to run within Streamlit's environment
nest_asyncio.apply()

# System prompt for the CAMARA agent
SYSTEM_PROMPT = """\
You are a helpful AI assistant that can interact with CAMARA telecom APIs through available tools.

When users ask questions, interpret their intent and use the appropriate tools.
Always provide helpful, conversational responses and explain what each service does.
If there are API errors, explain them in user-friendly terms.
If the user asks for a specific parameter of the network, filter out the response.
"""

class AsyncExecutor:
    """Helper class to execute async functions in a separate thread."""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        """Sets up and runs the event loop in the dedicated thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coro):
        """Run an async coroutine in the event loop and return its result."""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

    def stop(self):
        """Stop the event loop."""
        self.loop.call_soon_threadsafe(self.loop.stop)


class StreamlitCAMARAClient:
    """Streamlit-integrated CAMARA MCP Client."""

    def __init__(self):
        self.llm: Optional[Ollama] = None
        self.mcp_client: Optional[BasicMCPClient] = None
        self.mcp_tools: Optional[McpToolSpec] = None
        self.agent: Optional[FunctionAgent] = None
        self.agent_context: Optional[Context] = None
        self.is_initialized = False
        self.executor = AsyncExecutor()

    def setup_llm(self, model_name: str, request_timeout: float = 120.0) -> bool:
        """Initializes the Ollama LLM."""
        try:
            self.llm = Ollama(
                model=model_name,
                request_timeout=request_timeout,
                temperature=0.1
            )
            Settings.llm = self.llm
            return True
        except Exception as e:
            st.error(f"Failed to setup Ollama: {str(e)}")
            return False

    def setup_mcp_client(self, server_url: str) -> Optional[List[Any]]:
        """Initializes the MCP client and discovers available tools."""
        try:
            async def _setup_mcp():
                self.mcp_client = BasicMCPClient(server_url)
                self.mcp_tools = McpToolSpec(client=self.mcp_client)
                return await self.mcp_tools.to_tool_list_async()

            return self.executor.run(_setup_mcp())
        except Exception as e:
            st.error(f"Failed to connect to MCP server: {str(e)}")
            return None

    def setup_agent(self) -> bool:
        """Initializes the FunctionAgent with the discovered MCP tools."""
        try:
            if not self.mcp_tools:
                raise ValueError("MCP tools not initialized")

            async def _setup_agent():
                tools = await self.mcp_tools.to_tool_list_async()
                self.agent = FunctionAgent(
                    name="CAMARAAgent",
                    description="AI agent for CAMARA telecom APIs",
                    tools=tools,
                    llm=self.llm,
                    system_prompt=SYSTEM_PROMPT,
                )
                self.agent_context = Context(self.agent)
                self.is_initialized = True
                return True

            return self.executor.run(_setup_agent())
        except Exception as e:
            st.error(f"Failed to setup agent: {str(e)}")
            return False

    def process_message(self, message: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Processes a user message through the agent and streams tool calls."""
        if not self.is_initialized or not self.agent or not self.agent_context:
            return "Client not initialized. Please connect first.", []

        try:
            async def _process_message():
                handler = self.agent.run(message, ctx=self.agent_context)
                tool_calls = []

                async for event in handler.stream_events():
                    if isinstance(event, ToolCall):
                        tool_calls.append({
                            'type': 'call',
                            'name': event.tool_name,
                            'kwargs': event.tool_kwargs
                        })
                    elif isinstance(event, ToolCallResult):
                        tool_calls.append({
                            'type': 'result',
                            'name': event.tool_name,
                            'output': event.tool_output
                        })

                response = await handler
                return str(response), tool_calls

            return self.executor.run(_process_message())
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            st.error(error_msg)
            return error_msg, []