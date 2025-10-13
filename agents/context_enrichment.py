import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import json, subprocess, ast

load_dotenv()

async def context_preparation(user_ip: str):

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

    system_message = """
    You are a context preparation agent. Your task is to prepare and structure the given context for
    repository given by user. You have to extract README files, CHANGELOG files, CONTRIBUTING files,
    git commit history and docstrings from the code files. Structure the context in JSON format with keys as readme, changelog, contributing, commit_history, docstrings and values as the respective contents.
    If any of these files are not present, set the value to "Null". Only return the JSON response without any additional text or markdown formatting. 
    Ensure the JSON is properly formatted and can be parsed
    by the user."""

    agent = create_react_agent(llm, tools, prompt=system_message)

    response = await agent.ainvoke({
            "messages" : [{"role": "user", "content": user_ip}]
        })
    cleaned_response = "".join(response["messages"][8].content)
    
    if cleaned_response.startswith("```json"):
        cleaned_response = cleaned_response[7:]
    if cleaned_response.endswith("```"):
        cleaned_response = cleaned_response[:-3]
    cleaned_response = cleaned_response.strip()
    
    return cleaned_response

# if __name__ == "__main__":
#     user_ip = "Prepare context for repository with username `vishnumur777` and repository name `mybatop`."
#     response = asyncio.run(context_preparation(user_ip))
#     print("\nContext Preparation Response:")
#     json_load = json.loads(response)
#     print(json.dumps(json_load, indent=2))
