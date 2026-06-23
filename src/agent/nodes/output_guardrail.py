import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.agent.state import ComplianceAgentState
from databricks.sdk.runtime import dbutils

def output_guardrail_node(state: ComplianceAgentState):
    """
    The Egress Filter (DLP).
    Scans the drafted response to ensure no PII or schema info is leaked.
    """
    messages = state.get("messages", [])
    
    # If there are no messages, just pass
    if not messages:
        return {"next_node": "END"}
        
    drafted_response = messages[-1].content
    
    if not drafted_response:
        return {"next_node": "END"}

    # 1. Environment Setup (With local testing fallback)      
    os.environ["GROQ_API_KEY"] = dbutils.secrets.get(scope="portfolio_secret", key="groq_api_key")    
    # Initialize the fast 8B model
    llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0)
    
    # --- UPDATED PROMPT ---
    system_prompt = SystemMessage(content=(
        "You are an enterprise Data Loss Prevention (DLP) egress filter. Your ONLY job is to rewrite the user's text to remove sensitive technical data while preserving the core business insights.\n\n"
        
        "STRICT REDACTION RULES:\n"
        "1. MASKING: You must mask all Account IDs to show only the first character and last two characters (e.g., C99887 -> C***87).\n"
        "2. SANITIZATION: You MUST completely remove or replace any mention of:\n"
        "   - Database infrastructure ('Unity Catalog', 'Databricks')\n"
        "   - Table or schema names (e.g., 'paysim_gold', 'silver_transactions')\n"
        "   - Code execution or tool names (e.g., 'PySpark', 'SQL query', 'get_customer_risk_profile', 'tool')\n"
        "3. REWRITE: Rewrite the sentence to sound like a professional compliance summary written by a human. "
        "For example, instead of 'I ran a SQL query on the paysim_gold table and Account C12345 has a discrepancy', "
        "you MUST write 'A review of the account records indicates that Account C***45 has a discrepancy.'\n\n"
        
        "Output ONLY the final sanitized text. Do not add conversational filler or metadata."
    ))
    
    filter_messages = [system_prompt, HumanMessage(content=drafted_response)]
    print("🛡️ OUTPUT GUARDRAIL: Scanning drafted response for DLP violations...")
    
    try:
        scrubbed_response = llm.invoke(filter_messages)
        final_message = AIMessage(content=scrubbed_response.content, name="Egress_Filter")
        
        return {
            "messages": [final_message],
            "next_node": "END"
        }
        
    except Exception as e:
        print(f"🚨 OUTPUT GUARDRAIL ERROR: Filter failed. Error: {e}")
        return {
            "messages": [AIMessage(content="System Error: Response blocked by Data Loss Prevention rules.")],
            "next_node": "END"
        }