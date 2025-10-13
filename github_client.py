import asyncio
import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

async def setup_mcp_server():
    client = MultiServerMCPClient(
        {
            "github": {
                "transport": "streamable_http",
                "url": "http://localhost:8000/mcp/",
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

    system_message = "You are a helpful assistant with access to GitHub repositories. Use the available tools to answer questions about code and repositories."

    agent = create_react_agent(llm, tools, prompt=system_message)

    search_repo_example = await agent.ainvoke({
            "messages" : [{"role": "user", "content": "Search github repository with username `vishnumur777` and repository name `indianflagdemo`."}]
        })
    
    get_file_content_example = await agent.ainvoke({
            "messages" : [{"role": "user", "content": "Get the content of the file `index.html` from the repository `vishnumur777/indianflagdemo`."}]
        })
    get_file_content_local = await agent.ainvoke({
            "messages" : [{"role": "user", "content": "Get the content of github_mcp_server.py file from local system with given path /home/hdd/MLProjects/GenAIprojects/code_to_doc."}]
        })

    if "messages" in search_repo_example:
        print("\nSearch Repo Response:")
        for i,message in enumerate(search_repo_example["messages"]):
            print(f"{i+1}: {message.content}")

    if "messages" in get_file_content_example:
        print("\nGet File Content Response:")
        for i,message in enumerate(get_file_content_example["messages"]):
            print(f"{i+1}: {message.content}")

    if "messages" in get_file_content_local:
        print("\nGet File Content Local Response:")
        for i,message in enumerate(get_file_content_local["messages"]):
            print(f"{i+1}: {message.content}")

    
if __name__ == "__main__":
    asyncio.run(setup_mcp_server())