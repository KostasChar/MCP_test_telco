"""
Streamlit GUI for CAMARA MCP Client
A web interface for interacting with CAMARA telecom APIs through MCP and Ollama.
"""

import streamlit as st
from datetime import datetime
import json

# Import the core logic from the separate client file
from camara_client import StreamlitCAMARAClient

# --- Page Configuration and Styling ---

st.set_page_config(
    page_title="CAMARA MCP Client",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a polished look
st.markdown("""
<style>
    /* ... (all your CSS styles remain here) ... */
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .service-card {
        background: #f0f2f6; padding: 1rem; border-radius: 8px;
        border-left: 4px solid #1f77b4; margin: 0.5rem 0;
    }
    .api-call {
        background: #e6f3ff; padding: 0.75rem; border-radius: 6px;
        border-left: 4px solid #1a73e8; font-family: monospace;
        margin: 0.5rem 0; color: #1a1a1a; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .api-call pre {
        background: #f8f9fa; padding: 0.5rem; border-radius: 4px;
        border: 1px solid #e0e0e0; overflow-x: auto; color: #333; margin: 0.5rem 0;
    }
    .api-call strong { color: #1a73e8; }
    .error-box {
        background: #ffebee; padding: 1rem; border-radius: 5px;
        border-left: 4px solid #d93025; color: #c5221f; margin: 0.5rem 0;
    }
    .success-box {
        background: #e6f4ea; padding: 1rem; border-radius: 5px;
        border-left: 4px solid #137333; color: #137333; margin: 0.5rem 0;
    }
    .success-box code {
        background: #d9ead3; padding: 0.2rem 0.4rem; border-radius: 3px; color: #0d652d;
    }
    .chat-message {
        padding: 1rem; border-radius: 8px; margin: 0.75rem 0; background: #f8f9fa;
    }
    .user-message { background: #e8f0fe; border-left: 4px solid #1a73e8; }
    .bot-message { background: #fef7e0; border-left: 4px solid #fbbc04; }
</style>
""", unsafe_allow_html=True)


# --- State Management and UI Handlers ---

def initialize_session_state():
    """Initializes session state variables on first run."""
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
    if 'selected_example' not in st.session_state:
        st.session_state.selected_example = ""


def connect_to_mcp(model_name: str, server_url: str):
    """Handles the connection logic when the 'Connect' button is clicked."""
    st.session_state.connection_error = None
    with st.spinner("Connecting to CAMARA services..."):
        try:
            client = st.session_state.client
            if client.setup_llm(model_name):
                tools = client.setup_mcp_client(server_url)
                if tools:
                    st.session_state.available_tools = tools
                    if client.setup_agent():
                        st.session_state.is_connected = True
                        st.rerun()  # Rerun to update UI state
                    else:
                        st.session_state.connection_error = "Failed to setup agent."
                else:
                    st.session_state.connection_error = "Failed to connect to MCP server."
            else:
                st.session_state.connection_error = "Failed to setup Ollama LLM."
        except Exception as e:
            st.session_state.connection_error = str(e)


def process_user_message(user_input: str):
    """Processes a user's message and updates the chat history."""
    with st.spinner("Processing your request..."):
        response, tool_calls = st.session_state.client.process_message(user_input)
        st.session_state.chat_history.append({
            'timestamp': datetime.now(),
            'user_message': user_input,
            'bot_response': response,
            'tool_calls': tool_calls
        })
        st.session_state.selected_example = ""  # Clear example after use
        st.rerun()


# --- UI Rendering Functions ---

def render_header():
    """Renders the main page header."""
    st.markdown("""
    <div class="main-header">
        <h1>📡 CAMARA MCP Client</h1>
        <p>Interact with CAMARA Telecom APIs using Natural Language</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Renders the sidebar for configuration and connection."""
    with st.sidebar:
        st.header("🔧 Configuration")
        model_name = st.selectbox(
            "Ollama Model",
            ["llama3.2", "llama3.1", "mistral", "codellama", "phi3", "deepseek-r1", "deepseek-r1:1.5b"],
            help="Select your local Ollama model"
        )
        server_url = st.text_input(
            "MCP Server URL",
            value="http://127.0.0.1:8000/mcp",
            help="URL of your CAMARA MCP server"
        )
        if st.button("🔌 Connect to CAMARA MCP", type="primary"):
            connect_to_mcp(model_name, server_url)

        # Display connection status
        if st.session_state.is_connected:
            st.success("🟢 Connected and Ready")
        else:
            st.error("🔴 Not Connected")
            if st.session_state.connection_error:
                st.warning(f"Error: {st.session_state.connection_error}")

        # Display available tools
        if st.session_state.available_tools:
            st.header("🛠️ Available Tools")
            for tool in st.session_state.available_tools:
                with st.expander(f"🔧 {tool.metadata.name}"):
                    st.write(getattr(tool.metadata, 'description', 'No description.'))


def render_chat_interface():
    """Renders the main chat input, example buttons, and status panel."""
    col1, col2 = st.columns([2, 1])
    user_input = None

    with col1:
        st.header("💬 Chat with CAMARA APIs")
        st.subheader("📝 Try these examples:")
        example_buttons = [
            ("📋 Show catalog", "What services are available?"),
            ("📍 Device location", "Find location of device ABC123"),
            ("💬 Send SMS", "Send SMS to +1234567890 saying 'Hello World'"),
            ("⚡ Create QoD", "Create QoD session for +1234567890"),
            ("📶 Check reachability", "Is device XYZ789 reachable?"),
            ("✅ Verify number", "Verify phone number +1234567890")
        ]

        cols = st.columns(3)
        for i, (label, text) in enumerate(example_buttons):
            if cols[i % 3].button(label, key=f"ex_{i}"):
                if st.session_state.is_connected:
                    st.session_state.selected_example = text
                    st.rerun()
                else:
                    st.warning("Please connect to CAMARA MCP first!")

        prompt = st.text_input(
            "Your request:",
            placeholder="e.g., Send an SMS...",
            value=st.session_state.selected_example,
            disabled=not st.session_state.is_connected,
            key="chat_input"
        )

        send_clicked = st.button("📤 Send", disabled=not st.session_state.is_connected or not prompt)
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.selected_example = ""
            st.rerun()

        if send_clicked and prompt:
            user_input = prompt

    with col2:
        render_status_panel()

    return user_input


def render_status_panel():
    """Renders the API activity and tool usage panel."""
    st.header("📊 API Activity")
    if st.session_state.is_connected:
        st.success("🟢 System Online")
    else:
        st.error("🔴 System Offline")

    tool_usage = {}
    for chat in st.session_state.chat_history:
        for call in chat.get('tool_calls', []):
            if call['type'] == 'call':
                tool_name = call['name']
                tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1

    if tool_usage:
        st.subheader("🔧 Tool Usage")
        for tool, count in tool_usage.items():
            st.metric(tool, count)


def render_chat_history():
    """Renders the expandable conversation history."""
    st.header("💭 Conversation History")
    if not st.session_state.chat_history:
        st.info("No conversations yet. Ask a question to begin!")
        return

    for i, chat in enumerate(reversed(st.session_state.chat_history)):
        with st.expander(f"💬 {chat['user_message'][:50]}... ({chat['timestamp']:%H:%M:%S})", expanded=(i == 0)):
            st.markdown(f"**🗣️ You:** {chat['user_message']}")

            if chat['tool_calls']:
                st.markdown("**🔧 API Calls:**")
                for call in chat['tool_calls']:
                    if call['type'] == 'call':
                        kwargs = json.dumps(call['kwargs'], indent=2) if call['kwargs'] else "{}"
                        st.markdown(f'<div class="api-call">📡 Calling: <strong>{call["name"]}</strong>'
                                    f'<br>📝 Parameters: <pre>{kwargs}</pre></div>', unsafe_allow_html=True)
                    elif call['type'] == 'result':
                        preview = str(call['output'])[:200] + ('...' if len(str(call['output'])) > 200 else '')
                        st.markdown(f'<div class="success-box">✅ <strong>{call["name"]}</strong> completed'
                                    f'<br>📄 Response: <code>{preview}</code></div>', unsafe_allow_html=True)

            st.markdown(f"**🤖 Assistant:** {chat['bot_response']}")


def render_footer():
    """Renders the page footer."""
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: gray;'>🚀 Powered by Ollama + CAMARA MCP + Streamlit</div>",
                unsafe_allow_html=True)


# --- Main Application Execution ---

def main():
    """Main function to run the Streamlit app."""
    initialize_session_state()
    render_header()
    render_sidebar()
    user_input = render_chat_interface()

    if user_input:
        process_user_message(user_input)

    render_chat_history()
    render_footer()


if __name__ == "__main__":
    main()