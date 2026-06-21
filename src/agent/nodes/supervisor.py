import os
from typing import Literal
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from databricks.sdk.runtime import dbutils
from src.agent.state import ComplianceAgentState

# 1. Deterministic Routing Schema
class RouteDecision(BaseModel):
    next_node: Literal["auditor_worker", "FINISH"] = Field(
        description="The exact name of the next node to route to. Use 'FINISH' if the user's request is completely resolved."
    )

# 2. Supervisor Node Definition
def supervisor_node(state: ComplianceAgentState):
    """
    Acts as the manager of the workflow using Groq's high-speed LPU inference engine.
    """
    
    # Securely load the Groq API key into the environment
    os.environ["GROQ_API_KEY"] = dbutils.secrets.get(scope="portfolio_secret", key="groq_api_key")
    
    # Initialize Groq using Llama 3.3 70B (Temperature=0 for deterministic routing)
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    
    # Bind the strict Pydantic schema to the LLM
    router_llm = llm.with_structured_output(RouteDecision)
    
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
    
    try:
        decision = router_llm.invoke(messages)
        print(f"👔 SUPERVISOR DECISION: Routing to -> {decision.next_node}")
        return {"next_node": decision.next_node}
        
    except Exception as e:
        print(f"🚨 SUPERVISOR ERROR: Routing failed. Halting workflow. Error: {e}")
        return {"next_node": "FINISH"}