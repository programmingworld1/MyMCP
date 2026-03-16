import asyncio
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# This is our connection to Claude (the AI).
# It uses our API key to authenticate.
anthropic_client = Anthropic()  # reads ANTHROPIC_API_KEY from environment

async def main():
    # Tell the client how to start the server:
    # run "python server.py" as a subprocess.
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    # Start the server and open a communication channel with it.
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            # Do the handshake — client and server introduce themselves.
            await session.initialize()

            # Ask the server: "what tools do you have?"
            # Then reformat them into the shape Claude expects.
            mcp_tools = await session.list_tools()
            tools = [
                {
                    "name": t.name,                  # e.g. "read_doc"
                    "description": t.description,    # e.g. "Return the contents of a document..."
                    "input_schema": t.inputSchema,   # e.g. what parameters it takes
                }
                for t in mcp_tools.tools
            ]

            print("Connected. Tools:", [t["name"] for t in tools])
            print("Type your message or 'quit' to exit.\n")

            # This list stores the full conversation history.
            # Every message you send and every reply Claude gives gets added here.
            # Claude needs this so it remembers what was said earlier.
            messages = []

            # Outer loop: keeps the chat going until you type "quit".
            while True:
                user_input = input("You: ").strip()
                if user_input.lower() == "quit":
                    break
                if not user_input:
                    continue

                # Add your message to the conversation history.
                messages.append({"role": "user", "content": user_input})

                # Inner loop: keeps going as long as Claude wants to call tools.
                # Example: Claude might call read_doc, get the result,
                # then call edit_doc, get that result, then finally write a response.
                while True:

                    # Send the full conversation + available tools to Claude.
                    # Claude reads the tools and decides if it needs to call any.
                    response = anthropic_client.messages.create(
                        model="claude-opus-4-6",
                        max_tokens=1024,
                        tools=tools,       # the tools Claude can choose from
                        messages=messages,
                    )

                    if response.stop_reason == "tool_use":
                        # Claude wants to call a tool before answering.
                        # Add Claude's decision to the conversation history.
                        messages.append({"role": "assistant", "content": response.content})

                        # Claude may want to call multiple tools at once.
                        # Loop through all of them and call each one on the server.
                        tool_results = []
                        for block in response.content:
                            if block.type == "tool_use":
                                print(f"  [calling {block.name}({block.input})]")

                                # Actually call the tool on the MCP server.
                                result = await session.call_tool(block.name, block.input)

                                # Collect the result so we can send it back to Claude.
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,        # links result to the right tool call
                                    "content": result.content[0].text,
                                })

                        # Send the tool results back to Claude so it can continue.
                        messages.append({"role": "user", "content": tool_results})

                    else:
                        # Claude is done calling tools and has a final answer.
                        # Extract the text and print it.
                        final_text = next(
                            (b.text for b in response.content if hasattr(b, "text")), ""
                        )
                        print(f"\nClaude: {final_text}\n")

                        # Add Claude's final answer to the conversation history.
                        messages.append({"role": "assistant", "content": response.content})
                        break  # exit inner loop, go back to waiting for your next message

asyncio.run(main())
