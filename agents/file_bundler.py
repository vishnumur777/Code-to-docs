from verification import validate_and_process
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
import asyncio
import os
import shutil
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

class DocumentationBundler:
    def __init__(self, output_dir: str = "docs_output"):
        """
        Initialize the DocumentationBundler.
        
        Args:
            output_dir (str): Base directory for documentation output
        """
        self.output_dir = output_dir
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0
        )
        
    def _create_output_directories(self) -> tuple:
        """Create necessary output directories for documentation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = Path(self.output_dir) / timestamp
        
        # Create directories for functions and classes
        functions_dir = base_dir / "functions"
        classes_dir = base_dir / "classes"
        
        for dir_path in [functions_dir, classes_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        return base_dir, functions_dir, classes_dir
    
    async def separate_documentation(self, documentation: Dict) -> Dict:
        """
        Separate documentation into functions and classes.
        
        Args:
            documentation (Dict): Validated documentation
            
        Returns:
            Dict: Separated documentation with functions and classes
        """
        system_prompt = """
        You are a documentation organizer. Your task is to separate the provided documentation
        into individual functions and classes. For each item:
        
        1. For functions:
           - Extract complete function documentation
           - Include description, parameters, return type, and examples
           
        2. For classes:
           - Group class documentation with all its methods
           - Include class description, attributes, and method details
           
        Return a JSON with two main sections:
        - "functions": List of individual function documentation
        - "classes": List of class documentation with their methods
        
        Each item should have:
        - "name": Name of function/class
        - "content": Complete markdown documentation
        - "file_name": Suggested markdown file name (snake_case)
        """
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=json.dumps(documentation, indent=2))
            ]
            
            response = self.llm.invoke(messages)
            return json.loads(response.content)
            
        except Exception as e:
            return {
                "error": f"Failed to separate documentation: {str(e)}",
                "functions": [],
                "classes": []
            }
    
    def generate_markdown_files(self, separated_docs: Dict, 
                              functions_dir: Path, classes_dir: Path) -> List[str]:
        """
        Generate individual markdown files for functions and classes.
        
        Args:
            separated_docs (Dict): Separated documentation
            functions_dir (Path): Directory for function documentation
            classes_dir (Path): Directory for class documentation
            
        Returns:
            List[str]: List of generated file paths
        """
        generated_files = []
        
        try:
            # Generate function files
            for func in separated_docs.get("functions", []):
                file_path = functions_dir / f"{func['file_name']}.md"
                with open(file_path, 'w') as f:
                    f.write(func["content"])
                generated_files.append(str(file_path))
            
            # Generate class files
            for class_doc in separated_docs.get("classes", []):
                file_path = classes_dir / f"{class_doc['file_name']}.md"
                with open(file_path, 'w') as f:
                    f.write(class_doc["content"])
                generated_files.append(str(file_path))
                
            return generated_files
            
        except Exception as e:
            raise Exception(f"Failed to generate markdown files: {str(e)}")
    
    def create_zip_bundle(self, base_dir: Path, generated_files: List[str]) -> str:
        """
        Create a zip file containing all documentation files.
        
        Args:
            base_dir (Path): Base directory containing the documentation
            generated_files (List[str]): List of generated file paths
            
        Returns:
            str: Path to the created zip file
        """
        try:
            zip_path = str(base_dir) + ".zip"
            shutil.make_archive(str(base_dir), 'zip', str(base_dir))
            return zip_path
        except Exception as e:
            raise Exception(f"Failed to create zip bundle: {str(e)}")

async def bundle_documentation(
    documentation_result: Dict,
    output_dir: str = "docs_output",
    user_confirmation: bool = True
) -> Dict:
    """
    Main function to bundle documentation into separate files and create a zip archive.
    
    Args:
        documentation_result (Dict): Validated documentation result
        output_dir (str): Output directory for documentation files
        user_confirmation (bool): Whether to wait for user confirmation before zipping
        
    Returns:
        Dict: Result of bundling process with file paths and status
    """
    try:
        bundler = DocumentationBundler(output_dir)
        
        # Create output directories
        base_dir, functions_dir, classes_dir = bundler._create_output_directories()
        
        # Separate documentation into functions and classes
        separated_docs = await bundler.separate_documentation(documentation_result)
        
        # Generate markdown files
        generated_files = bundler.generate_markdown_files(
            separated_docs, functions_dir, classes_dir
        )
        
        result = {
            "status": "generated",
            "base_directory": str(base_dir),
            "generated_files": generated_files,
            "message": f"Generated {len(generated_files)} documentation files"
        }
        
        # If user confirmation is not required, create zip immediately
        if not user_confirmation:
            zip_path = bundler.create_zip_bundle(base_dir, generated_files)
            result.update({
                "status": "bundled",
                "zip_file": zip_path,
                "message": f"Documentation bundled in {zip_path}"
            })
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "details": "Failed to bundle documentation"
        }

# Example usage
# if __name__ == "__main__":
#     async def main():
#         # Assuming we have validated documentation
#         doc_result = {
#             "documentation": "... validated documentation content ...",
#             "code_analysis": "... code analysis ..."
#         }
#         
#         # Generate files without zip (waiting for user confirmation)
#         result = await bundle_documentation(doc_result, user_confirmation=True)
#         print(json.dumps(result, indent=2))
#         
#         # After user confirms, create zip
#         if input("Create zip bundle? (y/n): ").lower() == 'y':
#             bundler = DocumentationBundler()
#             zip_path = bundler.create_zip_bundle(
#                 Path(result["base_directory"]),
#                 result["generated_files"]
#             )
#             print(f"Created zip bundle: {zip_path}")
#     
#     asyncio.run(main())
