"""
Streamlit GUI for CAMARA MCP Client
A web interface for interacting with CAMARA telecom APIs through MCP and Ollama.
"""

import asyncio
import streamlit as st
import nest_asyncio
from datetime import datetime
import json
from typing import Optional, List, Dict, Any, Tuple
from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.agent.workflow import FunctionAgent, ToolCallResult, ToolCall
from llama_index.core.workflow import Context
import threading
import queue

# Apply nest_asyncio for async compatibility
nest_asyncio.apply()

# Page configuration
st.set_page_config(
    page_title="CAMARA MCP Client",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .service-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .api-call {
        background: #e6f3ff;
        padding: 0.75rem;
        border-radius: 6px;
        border-left: 4px solid #1a73e8;
        font-family: monospace;
        margin: 0.5rem 0;
        color: #1a1a1a;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .api-call pre {
        background: #f8f9fa;
        padding: 0.5rem;
        border-radius: 4px;
        border: 1px solid #e0e0e0;
        overflow-x: auto;
        color: #333;
        margin: 0.5rem 0;
    }
    .api-call strong {
        color: #1a73e8;
    }
    .error-box {
        background: #ffebee;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #d93025;
        color: #c5221f;
        margin: 0.5rem 0;
    }
    .success-box {
        background: #e6f4ea;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #137333;
        color: #137333;
        margin: 0.5rem 0;
    }
    .success-box code {
        background: #d9ead3;
        padding: 0.2rem 0.4rem;
        border-radius: 3px;
        color: #0d652d;
    }
    .tool-usage {
        background: #f8f9fa;
        padding: 0.75rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        border: 1px solid #e0e0e0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.75rem 0;
        background: #f8f9fa;
    }
    .user-message {
        background: #e8f0fe;
        border-left: 4px solid #1a73e8;
    }
    .bot-message {
        background: #fef7e0;
        border-left: 4px solid #fbbc04;
    }
</style>
""", unsafe_allow_html=True)

# System prompt for CAMARA services
SYSTEM_PROMPT = """\
You are a helpful AI assistant that can interact with CAMARA telecom APIs through available tools.

When users ask questions, interpret their intent and use the appropriate tools.
Always provide helpful, conversational responses and explain what each service does.
If there are API errors, explain them in user-friendly terms.
If the user asks for a specific parameter of the network, filter out the response.
"""
# Available CAMARA services:
# - Service Catalog: Get information about available CAMARA services
# - Device Location: Retrieve location information for devices using deviceId
# - Quality on Demand (QoD): Create, manage, and delete QoS sessions for phone numbers
# - SMS Messaging: Send SMS messages to phone numbers
# - Device Reachability: Check if devices are reachable using deviceId
# - Number Verification: Verify phone numbers

class AsyncExecutor:
    """Helper class to execute async functions in a separate thread"""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        self.result_queue = queue.Queue()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coro):
        """Run an async coroutine and return the result"""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

    def stop(self):
        """Stop the event loop"""
        self.loop.call_soon_threadsafe(self.loop.stop)


class StreamlitCAMARAClient:
    """Streamlit-integrated CAMARA MCP Client"""

    def __init__(self):
        self.llm: Optional[Ollama] = None
        self.mcp_client: Optional[BasicMCPClient] = None
        self.mcp_tools: Optional[McpToolSpec] = None
        self.agent: Optional[FunctionAgent] = None
        self.agent_context: Optional[Context] = None
        self.is_initialized = False
        self.executor = AsyncExecutor()

    def setup_llm(self, model_name: str, request_timeout: float = 120.0) -> bool:
        """Setup Ollama LLM"""
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
        """Setup MCP client and discover tools"""
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
        """Setup the CAMARA agent"""
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
        """Process user message and return response with tool calls"""
        if not self.is_initialized or not self.agent or not self.agent_context:
            return "Client not initialized", []

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


def initialize_session_state():
    """Initialize session state variables"""
    if 'client' not in st.session_state:
        st.session_state.client = StreamlitCAMARAClient()
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'is_connected' not in st.session_state:
        st.session_state.is_connected = False
    if 'available_tools' not in st.session_state:
        st.session_state.available_tools = []
    if 'connection_error' not in st.session_state:
        st.session_state.connection_error = None


def render_header():
    """Render the main header"""
    st.markdown("""
    <div class="main-header">
        <h1>📡 CAMARA MCP Client</h1>
        <p>Interact with CAMARA Telecom APIs using Natural Language</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar configuration"""
    with st.sidebar:
        st.header("🔧 Configuration")

        model_name = st.selectbox(
            "Ollama Model",
            ["llama3.2", "llama3.1", "mistral", "codellama", "phi3","deepseek-r1","deepseek-r1:1.5b"],
            help="Select your Ollama model"
        )

        server_url = st.text_input(
            "MCP Server URL",
            value="http://127.0.0.1:8000/mcp",
            help="URL of your CAMARA MCP server"
        )

        if st.button("🔌 Connect to CAMARA MCP", type="primary"):
            connect_to_mcp(model_name, server_url)

        if st.session_state.is_connected:
            st.success("🟢 Connected and Ready")
        else:
            st.error("🔴 Not Connected")
            if st.session_state.connection_error:
                st.error(f"Error: {st.session_state.connection_error}")

        if st.session_state.available_tools:
            st.header("🛠️ Available Tools")
            for i, tool in enumerate(st.session_state.available_tools):
                with st.expander(f"🔧 {tool.metadata.name}"):
                    description = getattr(tool.metadata, 'description', 'No description available')
                    st.write(description[:200] + ("..." if len(description) > 200 else ""))

        return model_name, server_url


def connect_to_mcp(model_name: str, server_url: str):
    """Handle MCP connection"""
    st.session_state.connection_error = None

    with st.spinner("Connecting to CAMARA services..."):
        try:
            if st.session_state.client.setup_llm(model_name):
                st.success("✅ Ollama LLM connected")

                tools = st.session_state.client.setup_mcp_client(server_url)
                if tools:
                    st.success("✅ MCP server connected")
                    st.session_state.available_tools = tools

                    if st.session_state.client.setup_agent():
                        st.success("✅ CAMARA agent ready")
                        st.session_state.is_connected = True
                        st.rerun()
                    else:
                        st.session_state.connection_error = "Failed to setup agent"
                else:
                    st.session_state.connection_error = "Failed to connect to MCP server"
            else:
                st.session_state.connection_error = "Failed to setup Ollama LLM"
        except Exception as e:
            st.session_state.connection_error = str(e)
            st.error(f"Connection failed: {str(e)}")


def render_chat_interface():
    """Render the main chat interface"""
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("💬 Chat with CAMARA APIs")

        st.subheader("📝 Try these examples:")

        example_buttons = [
            ("📋 Show service catalog", "What services are available?"),
            ("📍 Device location", "Find location of device ABC123"),
            ("💬 Send SMS", "Send SMS to +1234567890 saying 'Hello World'"),
            ("⚡ Create QoD session", "Create QoD session for +1234567890"),
            ("📶 Check reachability", "Check if device XYZ789 is reachable"),
            ("✅ Verify number", "Verify phone number +1234567890")
        ]

        # Store the selected example in session state
        if 'selected_example' not in st.session_state:
            st.session_state.selected_example = ""

        cols = st.columns(3)
        for i, (button_text, example_text) in enumerate(example_buttons):
            with cols[i % 3]:
                if st.button(button_text, key=f"example_{i}"):
                    if st.session_state.is_connected:
                        st.session_state.selected_example = example_text
                        st.rerun()
                    else:
                        st.warning("Please connect to CAMARA MCP first!")

        # Use the selected example as placeholder if available
        placeholder_text = st.session_state.selected_example if st.session_state.selected_example else "e.g., 'Send SMS to +1234567890 saying meeting at 3pm'"

        user_input = st.text_input(
            "Ask about CAMARA services:",
            placeholder=placeholder_text,
            disabled=not st.session_state.is_connected,
            key="chat_input"
        )

        col_send, col_clear = st.columns([1, 4])
        with col_send:
            send_clicked = st.button("📤 Send", disabled=not st.session_state.is_connected or not user_input)
        with col_clear:
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.session_state.selected_example = ""
                st.rerun()

        # Process the message only when send is clicked
        if send_clicked and user_input:
            # Clear the selected example after sending
            st.session_state.selected_example = ""
            return user_input

    with col2:
        render_status_panel()

    return None


def render_status_panel():
    """Render the status panel"""
    st.header("📊 API Activity")

    if st.session_state.is_connected:
        st.success("🟢 System Online")
        st.info("🤖 Model: Connected")
        st.info("🔗 Server: Connected")
    else:
        st.error("🔴 System Offline")

    if st.session_state.chat_history:
        tool_usage = {}
        for chat in st.session_state.chat_history:
            for tool_call in chat.get('tool_calls', []):
                if tool_call['type'] == 'call':
                    tool_name = tool_call['name']
                    tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1

        if tool_usage:
            st.subheader("🔧 Tool Usage")
            for tool, count in tool_usage.items():
                st.metric(tool, count)


def process_user_message(user_input: str):
    """Process user message and update chat history"""
    with st.spinner("Processing your request..."):
        try:
            response, tool_calls = st.session_state.client.process_message(user_input)

            chat_entry = {
                'timestamp': datetime.now(),
                'user_message': user_input,
                'bot_response': response,
                'tool_calls': tool_calls
            }
            st.session_state.chat_history.append(chat_entry)

            st.rerun()
        except Exception as e:
            st.error(f"Error processing message: {str(e)}")


def render_chat_history():
    """Render the conversation history"""
    st.header("💭 Conversation History")

    if not st.session_state.chat_history:
        st.info("No conversations yet. Start by asking a question or trying one of the examples above!")
        return

    for i, chat in enumerate(reversed(st.session_state.chat_history)):
        with st.expander(
                f"💬 {chat['user_message'][:50]}... ({chat['timestamp'].strftime('%H:%M:%S')})",
                expanded=(i == 0)
        ):
            st.markdown(f"**🗣️ You:** {chat['user_message']}")

            if chat['tool_calls']:
                st.markdown("**🔧 API Calls:**")
                for tool_call in chat['tool_calls']:
                    if tool_call['type'] == 'call':
                        kwargs_str = json.dumps(tool_call['kwargs'], indent=2) if tool_call['kwargs'] else "{}"
                        st.markdown(f"""
                        <div class="api-call">
                            📡 Calling: <strong>{tool_call['name']}</strong><br>
                            📝 Parameters: <pre>{kwargs_str}</pre>
                        </div>
                        """, unsafe_allow_html=True)
                    elif tool_call['type'] == 'result':
                        result_preview = str(tool_call['output'])[:200]
                        if len(str(tool_call['output'])) > 200:
                            result_preview += "..."

                        st.markdown(f"""
                        <div class="success-box">
                            ✅ <strong>{tool_call['name']}</strong> completed<br>
                            📄 Response: <code>{result_preview}</code>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown(f"**🤖 Assistant:** {chat['bot_response']}")

            if chat['tool_calls']:
                if st.button(f"🔍 Show Raw API Responses", key=f"raw_{i}"):
                    for tool_call in chat['tool_calls']:
                        if tool_call['type'] == 'result':
                            try:
                                if isinstance(tool_call['output'], (dict, list)):
                                    st.json(tool_call['output'])
                                else:
                                    st.code(str(tool_call['output']))
                            except Exception:
                                st.text(str(tool_call['output']))


def render_footer():
    """Render the footer"""
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>🚀 Powered by Ollama + CAMARA MCP + Streamlit</p>
        <p>💡 Ask questions in natural language to interact with telecom APIs</p>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application function"""
    initialize_session_state()
    render_header()
    model_name, server_url = render_sidebar()
    user_message = render_chat_interface()
    if user_message:
        process_user_message(user_message)
    render_chat_history()
    render_footer()


if __name__ == "__main__":
    main()