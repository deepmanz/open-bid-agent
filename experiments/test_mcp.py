import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server = StdioServerParameters(command=sys.executable, args=["src/mcp_resource_server.py"])
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools offered:", [tool.name for tool in tools.tools])

            print("\nfind_people('azure migration'):")
            result = await session.call_tool("find_people", {"skill": "azure migration"})
            for item in result.content:
                print(" ", item.text)

            print("\ncheck_availability(P03, Jan–Jun 2027):")
            result = await session.call_tool(
                "check_availability",
                {"person_id": "P03", "start_date": "2027-01-01", "end_date": "2027-06-30"})
            for item in result.content:
                print(" ", item.text)


asyncio.run(main())