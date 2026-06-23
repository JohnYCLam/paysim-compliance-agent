import os
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from databricks.sdk.runtime import dbutils
# Import the shared state and our enterprise toolbelt
from src.agent.state import ComplianceAgentState
from src.agent.tools import compliance_tools

def auditor_node(state: ComplianceAgentState):
    """
    The specialist worker that executes Databricks tools and analyzes the results.
    """
    # 1. Environment Setup (With local testing fallback)      
    os.environ["GROQ_API_KEY"] = dbutils.secrets.get(scope="portfolio_secret", key="groq_api_key")
        
    # 2. Initialize the Groq LLM 
    # (We use a slightly higher temperature here so the agent can write natural summaries)
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
    
    # 3. Bind the tools to the LLM
    # This is the magic line that gives the LLM access to your database functions
    # Force the LLM to only output one tool call per turn
    auditor_agent = llm.bind_tools(compliance_tools, parallel_tool_calls=False)
    
    # 4. Define the Worker's Behavior
    system_prompt = SystemMessage(content=(
        "You are a meticulous Data Auditor specializing in Anti-Money Laundering (AML).\n"
        "Your job is to execute database tools to answer the user's investigation request.\n\n"
        
        "Rules:\n"
        "1. ALWAYS fetch the customer risk profile first before pulling recent transactions.\n"
        "2. Ensure your final analysis is highly interpretable. Explain the exact rationale behind your assessment so a non-technical compliance officer can understand it.\n"
        "3. If you find a 'total_discrepancy_amount' > 0, highlight it as a SEVERE ledger violation."
    ))
    
    # 5. Execute the Agent
    messages = [system_prompt] + list(state["messages"])
    print("🔍 AUDITOR WORKER: Analyzing data and executing tools...")
    
    response = auditor_agent.invoke(messages)
    
    # Return the AI's response to be appended to the state's message history
    return {"messages": [response]}