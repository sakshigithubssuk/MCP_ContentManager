import anyio

from agent.agent import Agent


async def run_query(user_query: str):
    """Run agent in anyio context so MCP stdio_client (anyio-based) works."""
    agent = Agent()
    return await agent.handle_query(user_query)


def main():
    print("===== CM AI SERVER STARTED =====")

    agent = Agent()

    while True:
        user_query = input("\nEnter your query (type 'exit' to stop): ")

        if user_query.lower() == "exit":
            print("Server stopped.")
            break

        print("\n--- Sending query to Agent ---")

        # MCP stdio_client requires anyio event loop (spawns process, task groups)
        response = anyio.run(run_query, user_query, backend="asyncio")

        print("\n--- Final Response Stored in Variable 'response' ---")
        print(response)


if __name__ == "__main__":
    main()
