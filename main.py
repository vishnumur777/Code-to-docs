import chainlit as cl
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Literal
import operator
import json
import asyncio
from pathlib import Path
import sys
import os

# Add agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

# Import agent functions with correct names
from mcp_connection import mcp_connection_from_server
from code_parser import code_parser_work
from context_enrichment import context_preparation
from document_conversion import doc_conversion
from doc_conv_func_doc import doc_conversion as func_doc_conversion
from verification import validate_and_process
from file_bundler import bundle_documentation

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    user_input: str
    repository_info: str
    doc_type: str  # "readme" or "function_api"
    mcp_response: dict
    code_analysis: dict
    context_data: str
    documentation: dict
    validation_result: dict
    bundle_result: dict
    error: str

# Agent 1: MCP Connection
async def mcp_agent(state: AgentState):
    await cl.Message(
        content="🔌 **MCP Connection Agent**: Connecting to MCP server...",
        author="MCP Agent"
    ).send()
    
    try:
        # Call mcp_connection_from_server() - returns response dict
        mcp_response = await mcp_connection_from_server()
        
        await cl.Message(
            content="✅ **MCP Connection Successful**: Data fetched from server",
            author="MCP Agent"
        ).send()
        
        return {
            "mcp_response": mcp_response,
            "error": ""
        }
    except Exception as e:
        error_msg = f"❌ MCP Connection failed: {str(e)}"
        await cl.Message(content=error_msg, author="MCP Agent").send()
        return {"error": str(e), "mcp_response": {}}

# Agent 2: Code Parser
async def parser_agent(state: AgentState):
    await cl.Message(
        content="🔍 **Code Parser Agent**: Analyzing code structure...",
        author="Parser Agent"
    ).send()
    
    try:
        # Call code_parser_work() - returns dict with code analysis or error
        code_analysis = code_parser_work()
        
        if "error" in code_analysis:
            error_msg = f"⚠️ **Parsing Warning**: {code_analysis['error']}"
            await cl.Message(content=error_msg, author="Parser Agent").send()
        else:
            num_items = len(code_analysis) if isinstance(code_analysis, list) else 0
            await cl.Message(
                content=f"✅ **Code Analysis Complete**: Found {num_items} code elements",
                author="Parser Agent"
            ).send()
        
        return {"code_analysis": code_analysis, "error": ""}
    except Exception as e:
        error_msg = f"❌ Code parsing failed: {str(e)}"
        await cl.Message(content=error_msg, author="Parser Agent").send()
        return {"error": str(e), "code_analysis": {}}

# Agent 3: Context Enrichment
async def context_agent(state: AgentState):
    await cl.Message(
        content="📚 **Context Enrichment Agent**: Gathering repository context...",
        author="Context Agent"
    ).send()
    
    try:
        # Call context_preparation(user_ip: str) - returns JSON string
        context_data = await context_preparation(state["repository_info"])
        
        # Parse the JSON string to verify it's valid
        if isinstance(context_data, str):
            context_json = json.loads(context_data)
            keys = list(context_json.keys())
            await cl.Message(
                content=f"✅ **Context Enrichment Complete**: Gathered {len(keys)} context elements",
                author="Context Agent"
            ).send()
        
        return {"context_data": context_data, "error": ""}
    except Exception as e:
        error_msg = f"❌ Context enrichment failed: {str(e)}"
        await cl.Message(content=error_msg, author="Context Agent").send()
        return {"error": str(e), "context_data": ""}

# Router function to determine documentation type
def route_documentation_type(state: AgentState) -> Literal["readme_doc", "function_doc"]:
    """Route based on user's documentation preference"""
    doc_type = state.get("doc_type", "readme").lower()
    
    if "function" in doc_type or "api" in doc_type or "func" in doc_type:
        return "function_doc"
    else:
        return "readme_doc"

# Agent 4a: README Documentation Generator
async def readme_doc_agent(state: AgentState):
    await cl.Message(
        content="📝 **README Documentation Agent**: Generating comprehensive documentation...",
        author="README Doc Agent"
    ).send()
    
    try:
        # Call doc_conversion(repository_info: str) from document_conversion.py
        # Returns dict with status, documentation, code_analysis, context_data
        documentation = await doc_conversion(state["repository_info"])
        
        if documentation.get("status") == "success":
            await cl.Message(
                content="✅ **README Documentation Generated**: Comprehensive docs created",
                author="README Doc Agent"
            ).send()
        else:
            await cl.Message(
                content=f"⚠️ **Documentation Warning**: {documentation.get('error', 'Unknown error')}",
                author="README Doc Agent"
            ).send()
        
        return {"documentation": documentation, "error": ""}
    except Exception as e:
        error_msg = f"❌ README documentation generation failed: {str(e)}"
        await cl.Message(content=error_msg, author="README Doc Agent").send()
        return {"error": str(e), "documentation": {}}

# Agent 4b: Function API Documentation Generator
async def function_doc_agent(state: AgentState):
    await cl.Message(
        content="📋 **Function API Documentation Agent**: Generating API docs...",
        author="Function Doc Agent"
    ).send()
    
    try:
        # Call doc_conversion(repository_info: str) from doc_conv_func_doc.py
        # Returns dict with status, documentation, code_analysis, context_data
        documentation = await func_doc_conversion(state["repository_info"])
        
        if documentation.get("status") == "success":
            await cl.Message(
                content="✅ **Function API Documentation Generated**: API reference created",
                author="Function Doc Agent"
            ).send()
        else:
            await cl.Message(
                content=f"⚠️ **Documentation Warning**: {documentation.get('error', 'Unknown error')}",
                author="Function Doc Agent"
            ).send()
        
        return {"documentation": documentation, "error": ""}
    except Exception as e:
        error_msg = f"❌ Function API documentation generation failed: {str(e)}"
        await cl.Message(content=error_msg, author="Function Doc Agent").send()
        return {"error": str(e), "documentation": {}}

# Agent 5: Verification
async def verification_agent(state: AgentState):
    await cl.Message(
        content="✔️ **Verification Agent**: Validating documentation...",
        author="Verification Agent"
    ).send()
    
    try:
        # Call validate_and_process(repository_info, documentation_result, user_prompt, user_feedback)
        # Returns dict with status, documentation, validation_result, ready_for_bundling
        validation_result = await validate_and_process(
            repository_info=state["repository_info"],
            documentation_result=state["documentation"],
            user_prompt=state.get("user_input"),
            user_feedback=None
        )
        
        # Extract validation score
        val_result = validation_result.get("validation_result", {})
        score = val_result.get("validation_score", 0)
        is_valid = val_result.get("is_valid", False)
        
        status_emoji = "✅" if is_valid else "⚠️"
        await cl.Message(
            content=f"{status_emoji} **Validation Complete**: Score: {score:.2f}/1.0",
            author="Verification Agent"
        ).send()
        
        return {"validation_result": validation_result, "error": ""}
    except Exception as e:
        error_msg = f"❌ Verification failed: {str(e)}"
        await cl.Message(content=error_msg, author="Verification Agent").send()
        return {"error": str(e), "validation_result": {}}

# Agent 6: File Bundler
async def bundler_agent(state: AgentState):
    await cl.Message(
        content="📦 **File Bundler Agent**: Creating documentation bundle...",
        author="Bundler Agent"
    ).send()
    
    try:
        # Get the validated documentation
        # validation_result contains 'documentation' key with the final docs
        doc_to_bundle = state["validation_result"].get(
            "documentation", 
            state["documentation"].get("documentation", {})
        )
        
        # Call bundle_documentation(documentation_result, output_dir, user_confirmation)
        # Returns dict with status, base_directory, generated_files, zip_file, message
        bundle_result = await bundle_documentation(
            documentation_result={"documentation": doc_to_bundle},
            output_dir="docs_output",
            user_confirmation=False  # Auto-create zip
        )
        
        num_files = len(bundle_result.get("generated_files", []))
        zip_file = bundle_result.get("zip_file", "")
        
        if bundle_result.get("status") == "bundled":
            await cl.Message(
                content=f"✅ **Bundling Complete**: {num_files} files created\n📁 Zip: `{zip_file}`",
                author="Bundler Agent"
            ).send()
        else:
            await cl.Message(
                content=f"⚠️ **Bundling Status**: {bundle_result.get('message', 'Partial success')}",
                author="Bundler Agent"
            ).send()
        
        return {"bundle_result": bundle_result, "error": ""}
    except Exception as e:
        error_msg = f"❌ Bundling failed: {str(e)}"
        await cl.Message(content=error_msg, author="Bundler Agent").send()
        return {"error": str(e), "bundle_result": {}}

# Final report agent
async def report_agent(state: AgentState):
    await cl.Message(
        content="📊 **Final Report Agent**: Generating summary...",
        author="Report Agent"
    ).send()
    
    # Check for errors in any stage
    if state.get("error"):
        await cl.Message(
            content=f"❌ **Process Failed**: {state['error']}",
            author="Report Agent"
        ).send()
        return state
    
    # Generate summary
    doc_type = state.get("doc_type", "README").upper()
    validation = state.get("validation_result", {}).get("validation_result", {})
    bundle = state.get("bundle_result", {})
    
    # Get validation details
    is_valid = validation.get("is_valid", False)
    score = validation.get("validation_score", 0)
    issues = validation.get("issues", [])
    
    summary = f"""
## 📋 Documentation Generation Complete!

**Repository**: `{state.get('repository_info', 'N/A')}`
**Documentation Type**: **{doc_type}**

### ✅ Validation Results
- **Status**: {'✓ Valid' if is_valid else '⚠ Needs Review'}
- **Quality Score**: {score:.2f}/1.0
- **Issues Found**: {len(issues)}

### 📦 Bundle Information
- **Files Generated**: {len(bundle.get('generated_files', []))}
- **Output Directory**: `{bundle.get('base_directory', 'N/A')}`
- **Zip File**: `{bundle.get('zip_file', 'N/A')}`

### 📝 Next Steps
1. Download the zip file from the output directory
2. Review the generated documentation files
3. Address any validation issues if present
4. Integrate the docs into your repository

**Overall Status**: ✅ **COMPLETE**
"""
    
    await cl.Message(
        content=summary,
        author="Report Agent"
    ).send()
    
    return state

# Build the LangGraph workflow
def create_documentation_graph():
    workflow = StateGraph(AgentState)
    
    # Add all agent nodes
    workflow.add_node("mcp_connection", mcp_agent)
    workflow.add_node("code_parser", parser_agent)
    workflow.add_node("context_enrichment", context_agent)
    workflow.add_node("readme_documentation", readme_doc_agent)
    workflow.add_node("function_documentation", function_doc_agent)
    workflow.add_node("verification", verification_agent)
    workflow.add_node("file_bundler", bundler_agent)
    workflow.add_node("final_report", report_agent)
    
    # Set entry point
    workflow.set_entry_point("mcp_connection")
    
    # Linear flow through first three agents
    workflow.add_edge("mcp_connection", "code_parser")
    workflow.add_edge("code_parser", "context_enrichment")
    
    # Conditional edge based on documentation type
    workflow.add_conditional_edges(
        "context_enrichment",
        route_documentation_type,
        {
            "readme_doc": "readme_documentation",
            "function_doc": "function_documentation"
        }
    )
    
    # Both documentation types flow to verification
    workflow.add_edge("readme_documentation", "verification")
    workflow.add_edge("function_documentation", "verification")
    
    # Continue to bundler and final report
    workflow.add_edge("verification", "file_bundler")
    workflow.add_edge("file_bundler", "final_report")
    workflow.add_edge("final_report", END)
    
    return workflow.compile()

@cl.on_chat_start
async def start():
    """Initialize the multi-agent documentation system"""
    agent = create_documentation_graph()
    cl.user_session.set("agent", agent)
    
    welcome_message = """
# 🤖 Multi-Agent Documentation Generator

Welcome! I can generate comprehensive documentation for your GitHub repository.

## 📝 Documentation Types:
- **README Documentation**: Complete project docs with overview, setup, usage, and API details
- **Function API Documentation**: Focused documentation on functions and classes only

## 🚀 How to Use:
Send a message with repository info and doc type preference.

**Examples**:
```
Generate README documentation for repository vishnumur777/mybatop
```
```
Create function API documentation for vishnumur777/mybatop
```

## 🔧 Agent Pipeline:
1. MCP Connection → 2. Code Parser → 3. Context Enrichment → 
4. Documentation Generation → 5. Verification → 6. File Bundler

Ready to generate documentation! 🎉
"""
    
    await cl.Message(content=welcome_message).send()

@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages and process through the agent workflow"""
    agent = cl.user_session.get("agent")
    
    # Parse user input
    user_input = message.content.lower()
    
    # Determine documentation type
    doc_type = "readme"
    if any(word in user_input for word in ["function", "api", "func"]):
        doc_type = "function_api"
    
    # Extract repository info
    import re
    repo_pattern = r'(?:repository|repo)?\s*([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)'
    repo_match = re.search(repo_pattern, user_input)
    
    if not repo_match:
        await cl.Message(
            content="❌ Please provide repository in format: `username/repository`\n\n**Example**: `vishnumur777/mybatop`"
        ).send()
        return
    
    repo_parts = repo_match.group(1).split('/')
    repository_info = f"Prepare context for repository with username `{repo_parts[0]}` and repository name `{repo_parts[1]}`."
    
    await cl.Message(
        content=f"🎯 **Starting Documentation Generation**\n- Repository: `{repo_match.group(1)}`\n- Type: `{doc_type.upper()}`"
    ).send()
    
    # Create parent step for entire workflow
    async with cl.Step(name="📋 Documentation Pipeline") as parent_step:
        
        # Initialize state
        initial_state = {
            "messages": [message.content],
            "user_input": message.content,
            "repository_info": repository_info,
            "doc_type": doc_type,
            "mcp_response": {},
            "code_analysis": {},
            "context_data": "",
            "documentation": {},
            "validation_result": {},
            "bundle_result": {},
            "error": ""
        }
        
        # Stream through agent graph
        try:
            async for event in agent.astream(initial_state):
                for node_name, node_output in event.items():
                    async with cl.Step(
                        name=f"🔧 {node_name.replace('_', ' ').title()}",
                        parent_id=parent_step.id
                    ) as step:
                        # Format output (excluding large content)
                        if isinstance(node_output, dict):
                            display_output = {
                                k: v for k, v in node_output.items() 
                                if k not in ['messages', 'mcp_response', 'documentation', 'context_data']
                            }
                            output_str = json.dumps(display_output, indent=2, default=str)
                        else:
                            output_str = str(node_output)
                        
                        step.output = output_str
        
        except Exception as e:
            await cl.Message(
                content=f"❌ **Workflow Error**: {str(e)}"
            ).send()
            parent_step.output = f"Failed: {str(e)}"