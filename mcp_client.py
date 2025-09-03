"""
MCP Client with Ollama - Compatible with CAMARA API Server
This client connects to a CAMARA MCP server that provides telecom API services
including device location, SMS, QoD sessions, and number verification.
Users can ask natural language questions to interact with these services.
"""

import asyncio
import nest_asyncio
from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.agent.workflow import FunctionAgent, ToolCallResult, ToolCall
from llama_index.core.workflow import Context

# Apply nest_asyncio for Jupyter compatibility
nest_asyncio.apply()

# System prompt tailored for CAMARA API services
SYSTEM_PROMPT = """\
You are a helpful AI assistant that can interact with CAMARA telecom APIs through available tools.

Available CAMARA services:
- Service Catalog: Get information about available CAMARA services
- Device Location: Retrieve location information for devices using deviceId
- Quality on Demand (QoD): Create, manage, and delete QoS sessions for phone numbers
- SMS Messaging: Send SMS messages to phone numbers
- Device Reachability: Check if devices are reachable using deviceId
- Number Verification: Verify phone numbers

When users ask questions, interpret their intent and use the appropriate tools:

For service discovery:
- Use get_catalog() to show available services

For device operations:
- get_device_location() requires a deviceId
- check_reachability() requires a deviceId

For QoD sessions:
- create_qod_session() needs phoneNumber and optional qosProfile (default: "QCI_1_voice")
- get_qod_session() and delete_qod_session() need sessionId

For messaging:
- send_sms() requires 'to' (phone number) and 'content' (message text)

For verification:
- verify_number() requires phoneNumber

Always ask for required parameters if they're not provided in the user's question.
Provide helpful, conversational responses and explain what each service does.
If there are API errors, explain them in user-friendly terms.
"""


class CAMARAMCPClient:
    """MCP Client using Ollama for CAMARA Telecom API Operations"""

    def __init__(self,
                 model_name: str = "llama3.2",
                 mcp_server_url: str = "http://127.0.0.1:8000/sse",
                 request_timeout: float = 120.0):
        """
        Initialize the MCP client with Ollama for CAMARA services

        Args:
            model_name: Ollama model to use (default: llama3.2)
            mcp_server_url: URL of the CAMARA MCP server SSE endpoint
            request_timeout: Request timeout in seconds
        """
        self.model_name = model_name
        self.mcp_server_url = mcp_server_url
        self.request_timeout = request_timeout

        # Initialize components
        self.llm = None
        self.mcp_client = None
        self.mcp_tools = None
        self.agent = None
        self.agent_context = None

    def setup_llm(self):
        """Setup Ollama LLM"""
        print(f"🤖 Setting up Ollama with model: {self.model_name}")
        self.llm = Ollama(
            model=self.model_name,
            request_timeout=self.request_timeout,
            temperature=0.1  # Lower temperature for more consistent API interactions
        )
        Settings.llm = self.llm
        print("✅ Ollama LLM ready")

    async def setup_mcp_client(self):
        """Setup MCP client and discover CAMARA tools"""
        print(f"🔌 Connecting to CAMARA MCP server...")
        print(f"   URL: {self.mcp_server_url}")

        try:
            self.mcp_client = BasicMCPClient(self.mcp_server_url)
            self.mcp_tools = McpToolSpec(client=self.mcp_client)

            # Discover and display available tools
            tools = await self.mcp_tools.to_tool_list_async()
            print("✅ Connected to CAMARA MCP server successfully")
            print(f"\n📡 Available CAMARA API tools ({len(tools)} services):")

            # Group tools by category for better display
            tool_categories = {
                'catalog': '📋 Service Management',
                'location': '📍 Device Location',
                'qod': '⚡ Quality on Demand',
                'sms': '💬 SMS Messaging',
                'reachability': '📶 Device Status',
                'verify': '✅ Verification'
            }

            for i, tool in enumerate(tools, 1):
                # Determine category
                tool_name = tool.metadata.name
                category = '🔧 Other'
                for key, cat in tool_categories.items():
                    if key in tool_name.lower():
                        category = cat
                        break

                print(f"   {i}. {tool_name}")
                print(f"      📂 {category}")

                # Show first line of description
                desc_lines = tool.metadata.description.split('\n')
                if desc_lines and desc_lines[0].strip():
                    print(f"      💡 {desc_lines[0].strip()}")
                print()

        except Exception as e:
            print(f"❌ Failed to connect to CAMARA MCP server: {e}")
            print("\n🔧 Troubleshooting tips:")
            print("   • Ensure your CAMARA MCP server is running")
            print("   • Check that the FastMCP server is using the correct transport")
            print("   • Verify the server URL is accessible")
            raise

    async def setup_agent(self):
        """Setup the function agent for CAMARA operations"""
        print("🧠 Setting up CAMARA API agent...")
        tools = await self.mcp_tools.to_tool_list_async()

        self.agent = FunctionAgent(
            name="CAMARAAgent",
            description="An AI agent that can interact with CAMARA telecom APIs for device management, messaging, and network services.",
            tools=tools,
            llm=self.llm,
            system_prompt=SYSTEM_PROMPT,
        )

        self.agent_context = Context(self.agent)
        print("✅ CAMARA API agent initialized and ready")

    async def handle_user_message(self, message_content: str, verbose: bool = True):
        """
        Handle user message and return agent response

        Args:
            message_content: User's question or request
            verbose: Whether to print tool calls and results

        Returns:
            Agent's response as string
        """
        handler = self.agent.run(message_content, ctx=self.agent_context)

        async for event in handler.stream_events():
            if verbose and isinstance(event, ToolCall):
                print(f"\n🔧 Calling CAMARA API: {event.tool_name}")
                if event.tool_kwargs:
                    print(f"   📝 Parameters: {event.tool_kwargs}")
            elif verbose and isinstance(event, ToolCallResult):
                print(f"✅ API call completed: {event.tool_name}")
                if event.tool_output:
                    # Pretty print API responses
                    output = str(event.tool_output)
                    if len(output) > 200:
                        print(f"   📄 Response: {output[:200]}...")
                    else:
                        print(f"   📄 Response: {output}")

        response = await handler
        return str(response)

    async def initialize(self):
        """Initialize all components"""
        print("🚀 Initializing CAMARA MCP Client with Ollama")
        print("=" * 60)

        self.setup_llm()
        await self.setup_mcp_client()
        await self.setup_agent()

        print("=" * 60)
        print("✅ CAMARA MCP Client ready!")
        print("\n💬 You can now ask questions about CAMARA telecom services:")
        print("\n🔍 Discovery & Information:")
        print("   • 'What services are available?'")
        print("   • 'Show me the service catalog'")

        print("\n📍 Device Location & Status:")
        print("   • 'Find the location of device ABC123'")
        print("   • 'Check if device XYZ789 is reachable'")

        print("\n💬 SMS Messaging:")
        print("   • 'Send SMS to +1234567890 saying Hello'")
        print("   • 'Text +4471234567 with meeting reminder'")

        print("\n⚡ Quality on Demand:")
        print("   • 'Create QoD session for +1234567890'")
        print("   • 'Check QoD session status for session123'")
        print("   • 'Delete QoD session session456'")

        print("\n✅ Verification:")
        print("   • 'Verify phone number +1234567890'")

        print("\n⌨️  Type 'exit' to quit")
        print("-" * 60)

    async def chat_loop(self):
        """Main interactive chat loop"""
        while True:
            try:
                user_input = input("\n🗣️  You: ").strip()

                if user_input.lower() in ['exit', 'quit', 'q', 'bye']:
                    print("\n👋 Thanks for using CAMARA MCP Client. Goodbye!")
                    break

                if not user_input:
                    continue

                if user_input.lower() in ['help', 'h']:
                    await self.show_help()
                    continue

                print("\n" + "─" * 50)
                response = await self.handle_user_message(user_input, verbose=True)
                print("─" * 50)
                print(f"🤖 Assistant: {response}")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("💡 Try rephrasing your question or type 'help' for examples")
                continue

    async def show_help(self):
        """Show help information"""
        print("\n📚 CAMARA MCP Client Help")
        print("=" * 40)
        print("Available CAMARA services you can ask about:")
        print("\n📋 Service Catalog:")
        print("   - 'What services are available?'")
        print("   - 'Show me the catalog'")
        print("\n📍 Device Location:")
        print("   - 'Where is device [deviceId]?'")
        print("   - 'Get location for device ABC123'")
        print("\n📶 Device Reachability:")
        print("   - 'Is device [deviceId] reachable?'")
        print("   - 'Check if device XYZ789 is online'")
        print("\n💬 SMS Messaging:")
        print("   - 'Send SMS to [phone] saying [message]'")
        print("   - 'Text +1234567890 with Hello World'")
        print("\n⚡ Quality on Demand (QoD):")
        print("   - 'Create QoD session for [phone]'")
        print("   - 'Check QoD session [sessionId]'")
        print("   - 'Delete QoD session [sessionId]'")
        print("\n✅ Number Verification:")
        print("   - 'Verify phone number [phone]'")
        print("   - 'Check if +1234567890 is valid'")


async def main():
    """Main function to run the CAMARA MCP client"""

    # Configuration - Update these for your setup
    MODEL_NAME = "llama3.2"  # Change to your preferred Ollama model
    MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"  # CAMARA MCP server SSE endpoint

    # Create and initialize the CAMARA client
    client = CAMARAMCPClient(
        model_name=MODEL_NAME,
        mcp_server_url=MCP_SERVER_URL,
        request_timeout=120.0
    )

    try:
        await client.initialize()
        await client.chat_loop()
    except Exception as e:
        print(f"\n💥 Failed to start CAMARA MCP client: {e}")
        print("\n🔧 Troubleshooting checklist:")
        print("   1. ✅ Ollama is running with the specified model")
        print("   2. ✅ CAMARA MCP server is running (check your FastMCP server)")
        print("   3. ✅ Backend API server is running on localhost:5000")
        print("   4. ✅ All required packages are installed:")
        print("      pip install llama-index-llms-ollama llama-index-tools-mcp nest-asyncio")
        print("   5. ✅ Server is using the correct transport (SSE for web clients)")


if __name__ == "__main__":
    asyncio.run(main())

# For Jupyter notebook usage:
# await main()