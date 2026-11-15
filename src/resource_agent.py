import asyncio
import json
import sys
import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = "qwen2.5:7b"   # 1st llama3.1:8b, then try "qwen2.5:7b" and compare
MAX_STEPS = 15          # guardrail: stop runaway loops
MAX_NUDGES = 2          # how many times the guard can send the agent back

SYSTEM_PROMPT = """You are the resource planner for an IT services bid team.
Goal: propose a delivery team for the RFP below and flag any gaps.
How to work:
- First, list the roles this RFP needs. Then use the tools to search for each role.
- Check availability for every person you propose, using their id (e.g. P03).
Rules:
- Never invent people or availability. Only state what the tools returned.
- A person counts as available only if percent_available is 50 or more for the project dates.
- If no one has a skill, call list_skills to look for an adjacent skill before declaring a gap.
- If there is still no one, recommend a subcontractor or new hire for that role.
Priorities: internal staff before subcontractors; availability before a perfect skill match.
When done, reply with a table (role | person | availability | risk), then a list of gaps."""

TASK = """RFP: Gwinnett County - Design and Implementation of a Migration to Azure Cloud.
Scope: migrate up to 150 servers to Azure; cloud disaster recovery for 135 servers;
ExpressRoute and vWAN networking with Palo Alto firewalls; Azure Virtual Desktop;
a PMI-certified project manager is required.
Project dates: 2027-01-01 to 2027-06-30."""


def to_ollama_tools(mcp_tools):
    """Translate the MCP server's tool list into the format the LLM understands."""
    return [{"type": "function",
             "function": {"name": t.name, "description": t.description or "",
                          "parameters": t.inputSchema}}
            for t in mcp_tools]


def parse_result(result):
    """Turn a tool result into Python objects so the guard can inspect it."""
    items = []
    for content in result.content:
        if not hasattr(content, "text"):
            continue
        try:
            data = json.loads(content.text)
        except json.JSONDecodeError:
            continue
        items.extend(data if isinstance(data, list) else [data])
    return items


def check_final_answer(text, people_found, checked_ids):
    """Deterministic guard: every person named in the answer must have had availability checked."""
    problems = []
    if not checked_ids:
        problems.append("You have not checked anyone's availability yet.")
    unchecked = [name for name, pid in people_found.items() if name in text and pid not in checked_ids]
    if unchecked:
        problems.append("You have not checked availability for: " + ", ".join(unchecked) + ".")
    return problems


async def run_agent():
    server = StdioServerParameters(command=sys.executable, args=["src/mcp_resource_server.py"])
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = to_ollama_tools((await session.list_tools()).tools)

            messages = [{"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": TASK}]
            people_found, checked_ids, nudges = {}, set(), 0

            for step in range(1, MAX_STEPS + 1):
                response = ollama.chat(model=MODEL, messages=messages, tools=tools,
                                       options={"temperature": 0, "num_ctx": 8192})
                message = response.message
                messages.append(message)

                if not message.tool_calls:
                    answer = message.content or ""
                    problems = check_final_answer(answer, people_found, checked_ids)
                    if problems and nudges < MAX_NUDGES:
                        nudges += 1
                        note = " ".join(problems) + " Use the tools before giving your final answer."
                        print(f"[guard] answer rejected: {note}")
                        messages.append({"role": "user", "content": note})
                        continue
                    print("\n=== Agent's final answer ===\n")
                    print(answer)
                    if problems:
                        print("\n[guard] WARNING: answer still contains unverified claims:", problems)
                    return

                for call in message.tool_calls:
                    name, args = call.function.name, call.function.arguments
                    print(f"[step {step}] agent calls {name}({args})")
                    result = await session.call_tool(name, args)
                    parsed = parse_result(result)

                    if name == "find_people":
                        for person in parsed:
                            if isinstance(person, dict) and "id" in person:
                                people_found[person["name"]] = person["id"]
                    if name == "check_availability" and not any(
                            isinstance(p, dict) and "error" in p for p in parsed):
                        checked_ids.add(args.get("person_id"))

                    text = "\n".join(c.text for c in result.content if hasattr(c, "text"))
                    print(f"           -> {' '.join(text.split())[:160]}")
                    messages.append({"role": "tool", "content": text, "tool_name": name})

            print("\nStopped: reached the step limit without a final answer.")


asyncio.run(run_agent())