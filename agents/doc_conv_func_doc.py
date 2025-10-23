from code_parser import code_parser_work
from context_enrichment import context_preparation
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def doc_conversion(repository_info: str) -> dict:
    """
    Generate comprehensive documentation based on code analysis and repository context.
    
    Args:
        repository_info (str): String containing repository username and name
        
    Returns:
        dict: Generated documentation with structured sections
    """
    try:
        # Get code analysis from code_parser
        code_analysis = code_parser_work()
        
        # Get repository context from context_enrichment
        context_data = await context_preparation(repository_info)
        if isinstance(context_data, str):
            context_data = json.loads(context_data)
        
        # Initialize Gemini model
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3  # Slightly higher temperature for more creative documentation
        )
        
        # Prepare comprehensive prompt for documentation generation
        system_prompt = """
        You are a technical documentation expert. Using the provided code analysis and repository context,
        generate comprehensive documentation in markdown format that includes:

        1. Function/Class Descriptions

        which contains function names, parameters, return types, and brief descriptions.

        2. Usage Examples

        Provide clear examples of how to use the main functions/classes.


        Format the documentation in clear markdown with proper headings, code blocks, and sections.
        Focus on clarity, completeness, and technical accuracy.
        """

        # Combine code analysis and context for the model
        combined_input = {
            "code_analysis": code_analysis,
            "repository_context": context_data
        }
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=json.dumps(combined_input, indent=2))
        ]

        # Generate documentation
        response = llm.invoke(messages)
        
        return {
            "status": "success",
            "documentation": response.content,
            "code_analysis": code_analysis,
            "context_data": context_data
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "details": "Failed to generate documentation"
        }

# Example usage
# if __name__ == "__main__":
#     repo_info = "username: vishnumur777, repository: mybatop"
#     response = asyncio.run(doc_conversion(repo_info))
#     print(json.dumps(response, indent=2))
    