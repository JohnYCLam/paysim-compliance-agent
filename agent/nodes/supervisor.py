from typing import Literal
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI  # Note: Swap with ChatDatabricks if using Databricks Foundation Models
from pydantic import BaseModel, Field

from src.agent.state import ComplianceAgentState

# ---------------------------------------------------------
# 1. Deterministic Routing Schema (The Safety Net)
# ---------------------------------------------------------
class RouteDecision(BaseModel):
    """
    By forcing the LLM to output this exact Pydantic model, we eliminate 
    routing hallucinations. The LLM can only ever pick one of these literal strings.
    """
    next_node: Literal["auditor_worker", "FINISH"] = Field(
        description="The exact name of the next node to route to. Use 'FINISH' if the user's request is completely resolved."
    )

# ---------------------------------------------------------
# 2. Supervisor Node Definition
# ---------------------------------------------------------
def supervisor_node(state: ComplianceAgentState):
    """
    Acts as the manager of the workflow. Reviews the conversation history 
    and determines the next step in the compliance investigation.
    """
    
    # Define the core model (Temperature=0 ensures deterministic, logical routing)
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Bind the strict Pydantic schema to the LLM
    router_llm = llm.with_structured_output(RouteDecision)
    
    # The System Prompt is the Supervisor's "Job Description"
    system_prompt = SystemMessage(content=(
        "You are a senior AML Compliance Supervisor orchestrating a ledger investigation. "
        "You manage a specialized worker: 'auditor_worker'.\n\n"
        
        "Your available worker capabilities:\n"
        "- auditor_worker: Can fetch aggregated customer risk profiles and pull specific recent transactions.\n\n"
        
        "Rules:\n"
        "1. If the user asks to investigate an account, ALWAYS route to the 'auditor_worker' first.\n"
        "2. If the 'auditor_worker' has returned the necessary data and provided an analysis, and no further action is required, route to 'FINISH'.\n"
        "3. Do not attempt to answer data questions yourself. You are strictly a router."
    ))
    
    # Combine the system prompt with the ongoing conversation history
    messages = [system_prompt] + list(state["messages"])
    
    # Execute the routing decision
    try:
        decision = router_llm.invoke(messages)
        print(f"👔 SUPERVISOR DECISION: Routing to -> {decision.next_node}")
        
        # Return the update to the state clipboard
        return {"next_node": decision.next_node}
        
    except Exception as e:
        print(f"🚨 SUPERVISOR ERROR: Routing failed. Halting workflow. Error: {e}")
        # Failsafe routing to prevent infinite loops on error
        return {"next_node": "FINISH"}