from langchain_core.tools import tool
import json

# ---------------------------------------------------------
# TOOL 1: The Risk Profile Fetcher
# ---------------------------------------------------------
@tool
def get_customer_risk_profile(account_id: str) -> str:
    """
    Retrieves the pre-calculated compliance risk profile for a specific customer.
    Always use this tool FIRST when asked to audit an account to understand their baseline risk.
    """
    try:
        # SECURE: Using a named parameter placeholder (:acc_id)
        query = """
            SELECT * FROM portfolio_catalog.compliance_project.customer_risk_profiles
            WHERE account_id = :acc_id
        """
        
        # Pass the variable securely to Spark's execution engine
        df = spark.sql(query, args={"acc_id": account_id}).toPandas()
        
        if df.empty:
            return json.dumps({"error": f"No risk profile found for account {account_id}."})
            
        return df.to_json(orient="records")
        
    except Exception as e:
        return json.dumps({"error": f"Database error: {str(e)}"})

# ---------------------------------------------------------
# TOOL 2: The Secure Transaction Investigator
# ---------------------------------------------------------    
@tool
def get_recent_transactions(account_id: str, limit: int = 10) -> str:
    """
    Retrieves the most recent individual transactions for an account.
    Use this tool to investigate specific anomalies, trace money movement, 
    or find the exact transaction causing a ledger discrepancy.
    """
    try:
        # MITIGATION 1: Defeat Agent DoS (Context Flooding)
        # Force the LLM's requested limit into an integer and hard-cap it at 50.
        # This prevents the LLM from requesting 1,000,000 rows and crashing the application.
        safe_limit = min(abs(int(limit)), 50)
        
        # MITIGATION 2: Defeat SQL Injection
        # We use a parameterized placeholder (:acc_id) for the untrusted string input.
        query = f"""
            SELECT step, tx_type, amount, beneficiary_id, is_high_risk_tx_type, orig_balance_discrepancy
            FROM portfolio_catalog.compliance_project.paysim_silver
            WHERE originator_id = :acc_id
            ORDER BY step DESC
            LIMIT {safe_limit}
        """
        
        # Pass the account_id securely into Spark's execution engine
        df = spark.sql(query, args={"acc_id": account_id}).toPandas()
        
        if df.empty:
            return json.dumps({"error": f"No recent transactions found for account {account_id}."})
            
        return df.to_json(orient="records")
        
    except ValueError:
        # Catch cases where the LLM passes a non-numeric string as the limit
        return json.dumps({"error": "Invalid limit parameter provided. Must be an integer."})
    except Exception as e:
        return json.dumps({"error": f"Database error: {str(e)}"})
    
# ---------------------------------------------------------
# TOOL EXPORT
# ---------------------------------------------------------
# We bundle them here so other files can import the entire "toolbelt" at once.
compliance_tools = [get_customer_risk_profile, get_recent_transactions]
