import chainlit as cl
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    research_data: str
    analysis: str

# Define individual agents
async def research_agent(state: AgentState):
    await cl.Message(
        content="🔍 **Research Agent**: Searching for information...",
        author="Research Agent"
    ).send()
    
    # Do research work
    result = "Found relevant data..."
    
    await cl.Message(
        content=f"✅ **Research Complete**: {result}",
        author="Research Agent"
    ).send()
    
    return {"research_data": result}

async def analysis_agent(state: AgentState):
    await cl.Message(
        content="📊 **Analysis Agent**: Analyzing research data...",
        author="Analysis Agent"
    ).send()
    
    # Do analysis
    analysis = f"Analysis of: {state['research_data']}"
    
    await cl.Message(
        content=f"✅ **Analysis Complete**: {analysis}",
        author="Analysis Agent"
    ).send()
    
    return {"analysis": analysis}

async def writer_agent(state: AgentState):
    await cl.Message(
        content="✍️ **Writer Agent**: Generating final response...",
        author="Writer Agent"
    ).send()
    
    # Write final output
    final = f"Report based on {state['analysis']}"
    
    await cl.Message(
        content=f"📝 **Final Report**: {final}",
        author="Writer Agent"
    ).send()
    
    return {"messages": [final]}

# Build the graph
def create_multi_agent_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("research", research_agent)
    workflow.add_node("analysis", analysis_agent)
    workflow.add_node("writer", writer_agent)
    
    workflow.set_entry_point("research")
    workflow.add_edge("research", "analysis")
    workflow.add_edge("analysis", "writer")
    workflow.add_edge("writer", END)
    
    return workflow.compile()

@cl.on_chat_start
async def start():
    agent = create_multi_agent_graph()
    cl.user_session.set("agent", agent)
    await cl.Message(content="🤖 Multi-Agent System Ready!").send()

@cl.on_message
async def main(message: cl.Message):
    agent = cl.user_session.get("agent")
    
    async with cl.Step(name="Multi-Agent Processing") as parent_step:
        
        async for event in agent.astream({"messages": [message.content]}):
            for node_name, node_output in event.items():
                async with cl.Step(
                    name=f"Agent: {node_name}",
                    parent_id=parent_step.id
                ) as step:
                    step.output = str(node_output)
