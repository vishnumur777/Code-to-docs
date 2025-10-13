from mcp_connection import mcp_connection_from_server
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import json

def code_parser_work() -> dict:
    mcp_response = asyncio.run(mcp_connection_from_server())
    prompt = """
    You are a programming assistant. You will be given a piece of code, and you need to
    identify what programming language it was written in, then extract classes and functions from it. 
    Return only a valid JSON array without any additional text or markdown formatting. The JSON array should contain objects with these fields:
    - programming_language: The programming language of the code
    - name: The name of the class or function
    - type: "class" or "function"
    - description: A brief description of what the class or function does
    - parameters: A list of parameter names (for functions only)
    - return_type: The return type (for functions only)
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0
    )

    try:
        code_content = mcp_response["messages"][2].content
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=str(code_content))
        ]

        llm_response = llm.invoke(messages)
        
        cleaned_response = llm_response.content.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        json_dict = json.loads(cleaned_response)
        return json_dict
    
    except KeyError as e:
        return {"error": f"Failed to access mcp_response content: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse JSON response: {str(e)}", "raw_response": llm_response.content}
    except TypeError:
        return {"error": "The response is not a valid JSON array.", "raw_response": llm_response.content}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

# if __name__ == "__main__":
#     response = code_parser()
#     print(json.dumps(response, indent=2))