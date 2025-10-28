import asyncio
import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

async def mcp_connection_from_server():
    client = MultiServerMCPClient(
        {
            "github": {
                "transport": "streamable_http",
                "url": "http://localhost:8002/mcp/",
                "headers": {
                    "Content-Type": "application/json"
                }
            }
        }
    )

    tools = await client.get_tools()
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0
    )

    system_message = "You are a helpful assistant with access to GitHub repositories and Local files. Use the available tools to answer questions about code and repositories."

    agent = create_react_agent(llm, tools, prompt=system_message)

    user_ip = input("User: ")

    response = await agent.ainvoke({
        "messages" : [{"role": "user", "content": user_ip}]
    })

    return response