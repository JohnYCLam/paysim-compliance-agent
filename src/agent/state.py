from typing import Annotated, TypedDict, Sequence
import operator
from langchain_core.messages import BaseMessage

class ComplianceAgentState(TypedDict):
    """
    The shared memory structure for the AML Compliance Agent network.
    Every node in the graph will read from and return updates to this state.
    """
    
    # 1. The Conversation History
    # 'operator.add' is a Reducer. It tells LangGraph to append new messages 
    # to the list rather than overwriting the entire history.
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # 2. The Security Perimeter Flag
    # Set by the Guardrail node. If True, the graph halts immediately.
    is_security_breach: bool
    
    # 3. The Orchestration Router
    # The Supervisor updates this string to dictate which worker acts next.
    # (e.g., "auditor", "human_in_loop", or "FINISH")
    next_node: str
    
    # 4. Enterprise Audit Trail (Optional but highly recommended)
    # Extracts and stores the specific account being audited. 
    # This is crucial for logging compliance actions in Databricks later.
    active_account_id: str