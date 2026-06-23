import mlflow
from langgraph.graph import StateGraph

# Import your State and Nodes
from src.agent.state import ComplianceAgentState
from src.agent.nodes.input_guardrail import input_guardrail_node
from src.agent.nodes.supervisor import supervisor_node
from src.agent.nodes.auditor_worker import auditor_node
from src.agent.nodes.output_guardrail import output_guardrail_node
from langgraph.graph import END
from langgraph.prebuilt import ToolNode, tools_condition
from src.agent.tools import compliance_tools

# ---------------------------------------------------------
# 1. Enable MLflow Tracing for LangChain
# ---------------------------------------------------------
# This single line tells Databricks to automatically monitor and 
# log every LLM call and tool execution your agent makes.
mlflow.langchain.autolog()

# ---------------------------------------------------------
# 2. Build the Graph
# ---------------------------------------------------------
workflow = StateGraph(ComplianceAgentState)

# Add the nodes
workflow.add_node("input_guardrail", input_guardrail_node)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("auditor_worker", auditor_node)
workflow.add_node("output_guardrail", output_guardrail_node)
workflow.add_node("tools", ToolNode(compliance_tools))

# Define the routing logic (The Edges)
# Start at the Guardrail
workflow.set_entry_point("input_guardrail")

# The Guardrail decides whether to halt or pass to the Supervisor
workflow.add_conditional_edges(
    "input_guardrail",
    lambda state: "END" if state.get("is_security_breach") else "supervisor",
    {
        "END": END, 
        "FINISH": END, # Failsafe mapping to catch rogue state flags
        "supervisor": "supervisor"
    }
)

# The Supervisor decides if the worker needs to run, or if we are done
workflow.add_conditional_edges(
    "supervisor",
    lambda state: state.get("next_node", "FINISH"),
    {
        "auditor_worker": "auditor_worker", 
        "FINISH": "output_guardrail",
        "END": "output_guardrail" # Failsafe mapping
    }
)

# If the worker asks for a tool, go to 'tools'. Otherwise, return to the 'supervisor'.
workflow.add_conditional_edges(
    "auditor_worker",
    tools_condition,
    {
        "tools": "tools",
        "__end__": "supervisor" # langgraph's internal flag for "no tools requested"
    }
)

# After the tools finish executing the Python code, ALWAYS send the data back to the worker
workflow.add_edge("tools", "auditor_worker")

workflow.add_edge("output_guardrail", END)

# Compile the final application
compliance_app = workflow.compile()

# ---------------------------------------------------------
# 3. Execute with MLflow Logging
# ---------------------------------------------------------
if __name__ == "__main__":
    from langchain_core.messages import HumanMessage
    
    # Define the test payload
    initial_state = {
        "messages": [HumanMessage(content="Audit account C12345 for money laundering risks.")],
        "next_node": "",
        "is_security_breach": False
    }
    
    print("🚀 Initiating Agentic Workflow...")
    
    # Start an MLflow run to bundle the logs
    with mlflow.start_run(run_name="AML_Agent_Audit_Run"):
        
        # Execute the graph
        final_state = compliance_app.invoke(initial_state)
        
        # Print the final output from the AI
        print("\n✅ FINAL REPORT:")
        print(final_state["messages"][-1].content)