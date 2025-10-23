from document_conversion import doc_conversion
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
import asyncio
from typing import Dict, Union, Optional
from dotenv import load_dotenv

load_dotenv()

class DocumentationValidator:
    def __init__(self):
        """Initialize the DocumentationValidator with Gemini model"""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0
        )
        
    async def validate_documentation(self, 
                                  documentation: Dict,
                                  code_analysis: Dict,
                                  user_prompt: Optional[str] = None) -> Dict:
        """
        Validate the generated documentation against code analysis and user requirements.
        
        Args:
            documentation (Dict): The generated documentation
            code_analysis (Dict): Code analysis from the parser
            user_prompt (Optional[str]): Original user requirements/prompt
            
        Returns:
            Dict: Validation results with status and any improvement suggestions
        """
        system_prompt = """
        You are a documentation validation expert. Your task is to:
        1. Verify that the documentation covers all code elements (classes, functions, etc.)
        2. Check if the documentation meets user requirements
        3. Validate technical accuracy
        4. Ensure documentation clarity and completeness

        If any issues are found, provide specific improvement suggestions.
        Return a JSON with:
        - "is_valid": boolean
        - "validation_score": float (0-1)
        - "issues": list of specific issues found
        - "suggestions": list of improvement suggestions
        - "missing_elements": list of code elements not covered
        """
        
        validation_input = {
            "documentation": documentation,
            "code_analysis": code_analysis,
            "user_requirements": user_prompt
        }
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=json.dumps(validation_input, indent=2))
        ]
        
        try:
            response = self.llm.invoke(messages)
            validation_result = json.loads(response.content)
            return validation_result
        except Exception as e:
            return {
                "is_valid": False,
                "error": str(e),
                "validation_score": 0,
                "issues": ["Failed to perform validation"]
            }
    
    async def process_user_feedback(self, 
                                 repository_info: str,
                                 original_doc: Dict,
                                 feedback: str) -> Dict:
        """
        Process user feedback and regenerate documentation if needed.
        
        Args:
            repository_info (str): Repository information
            original_doc (Dict): Original documentation
            feedback (str): User feedback/suggestions
            
        Returns:
            Dict: Updated documentation or error message
        """
        system_prompt = """
        You are a documentation improvement expert. Using the original documentation and user feedback:
        1. Analyze the feedback
        2. Identify specific areas for improvement
        3. Maintain existing accurate content
        4. Incorporate user suggestions
        
        Return improved documentation that addresses all feedback while maintaining technical accuracy.
        """
        
        improvement_input = {
            "original_documentation": original_doc,
            "user_feedback": feedback
        }
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=json.dumps(improvement_input, indent=2))
        ]
        
        try:
            # Get improvement suggestions
            response = self.llm.invoke(messages)
            improvements = json.loads(response.content)
            
            # Regenerate documentation with improvements
            new_doc = await doc_conversion(repository_info)
            
            # Validate new documentation
            validation_result = await self.validate_documentation(
                new_doc["documentation"],
                new_doc["code_analysis"]
            )
            
            return {
                "status": "success",
                "updated_documentation": new_doc["documentation"],
                "validation_result": validation_result,
                "improvements_applied": improvements
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "details": "Failed to process feedback and update documentation"
            }

async def validate_and_process(
    repository_info: str,
    documentation_result: Dict,
    user_prompt: Optional[str] = None,
    user_feedback: Optional[str] = None
) -> Dict:
    """
    Main function to validate documentation and process any feedback.
    
    Args:
        repository_info (str): Repository information
        documentation_result (Dict): Generated documentation result
        user_prompt (Optional[str]): Original user requirements
        user_feedback (Optional[str]): User feedback if any
        
    Returns:
        Dict: Processed and validated documentation
    """
    validator = DocumentationValidator()
    
    try:
        # First validation
        validation_result = await validator.validate_documentation(
            documentation_result["documentation"],
            documentation_result["code_analysis"],
            user_prompt
        )
        
        # If validation fails or user feedback exists, process improvements
        if not validation_result["is_valid"] or user_feedback:
            improved_doc = await validator.process_user_feedback(
                repository_info,
                documentation_result,
                user_feedback or json.dumps(validation_result["suggestions"])
            )
            return {
                "status": "updated",
                "documentation": improved_doc["updated_documentation"],
                "validation_result": improved_doc["validation_result"],
                "improvements": improved_doc["improvements_applied"]
            }
            
        # If validation passes and no feedback, proceed to bundling
        return {
            "status": "validated",
            "documentation": documentation_result["documentation"],
            "validation_result": validation_result,
            "ready_for_bundling": True
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "details": "Validation process failed"
        }

# Example usage
# if __name__ == "__main__":
#     async def main():
#         repo_info = "username: vishnumur777, repository: mybatop"
#         doc_result = await doc_conversion(repo_info)
#         
#         # Validate without user feedback
#         result = await validate_and_process(repo_info, doc_result)
#         print(json.dumps(result, indent=2))
#         
#         # Validate with user feedback
#         feedback = "Please add more code examples and improve the installation section"
#         result_with_feedback = await validate_and_process(
#             repo_info, 
#             doc_result, 
#             user_feedback=feedback
#         )
#         print(json.dumps(result_with_feedback, indent=2))
#     
#     asyncio.run(main())
