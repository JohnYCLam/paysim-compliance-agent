from pyspark.sql import SparkSession
from langchain_core.tools import tool
import json
from functools import wraps
import time

# =====================================================================
# SECURITY LAYER: State Tracking for Circuit Breaker & Rate Limiter
# =====================================================================
# Note: If deployed on AWS Serverless, this state would typically be 
# moved to Redis or DynamoDB. For Databricks clusters, memory is fine.
SECURITY_STATE = {
    "consecutive_errors": 0,
    "circuit_open_until": 0,
    "rate_limits": {}
}

def secure_db_tool(max_calls=3, time_window=30, max_errors=2, timeout_seconds=60):
    """
    Enterprise decorator that wraps database tools with rate limiting 
    and a circuit breaker to prevent infinite AI loops.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            
            # 1. CIRCUIT BREAKER CHECK
            if SECURITY_STATE["consecutive_errors"] >= max_errors:
                if current_time < SECURITY_STATE["circuit_open_until"]:
                    # Failsafe: Tell the AI the database is dead and to stop asking
                    return json.dumps([{"status": "CIRCUIT_OPEN", "message": "CRITICAL: Database offline. Halt investigation and report failure."}])
                else:
                    # Half-open: The timeout passed, let's try one more time
                    SECURITY_STATE["consecutive_errors"] = max_errors - 1

            # 2. RATE LIMITER CHECK
            # Extract the account_id from the arguments to track spam
            account_id = kwargs.get('account_id') or (args[0] if args else "unknown")
            
            if account_id not in SECURITY_STATE["rate_limits"]:
                SECURITY_STATE["rate_limits"][account_id] = []
                
            # Clean up old requests outside the time window
            SECURITY_STATE["rate_limits"][account_id] = [
                t for t in SECURITY_STATE["rate_limits"][account_id] 
                if current_time - t < time_window
            ]
            
            # If the AI asked for this exact account too many times, block it
            if len(SECURITY_STATE["rate_limits"][account_id]) >= max_calls:
                return json.dumps([{"status": "RATE_LIMITED", "message": f"Action blocked: You have queried {account_id} too many times. Move on."}])
            
            # Log the request
            SECURITY_STATE["rate_limits"][account_id].append(current_time)

            # 3. EXECUTE THE SPARK QUERY
            try:
                result = func(*args, **kwargs)
                # If successful, reset the circuit breaker
                SECURITY_STATE["consecutive_errors"] = 0
                return result
                
            except Exception as e:
                # If the database crashes, trip the circuit breaker
                SECURITY_STATE["consecutive_errors"] += 1
                if SECURITY_STATE["consecutive_errors"] >= max_errors:
                    SECURITY_STATE["circuit_open_until"] = current_time + timeout_seconds
                    
                return json.dumps([{"status": "DATABASE_ERROR", "message": f"Execution failed: {str(e)}"}])
                
        return wrapper
    return decorator

# ---------------------------------------------------------
# TOOL 1: The Risk Profile Fetcher
# ---------------------------------------------------------
@tool
@secure_db_tool(max_calls=3, time_window=30)
def get_customer_risk_profile(account_id: str) -> str:
    """
    Retrieves the pre-calculated compliance risk profile for a specific customer.
    Always use this tool FIRST when asked to audit an account to understand their baseline risk.
    """
    try:
        # 1. Fetch the active Databricks Spark session
        spark = SparkSession.builder.getOrCreate()
        
        # SECURE: Using a named parameter placeholder (:acc_id)
        query = """
            SELECT * FROM portfolio_catalog.compliance_project.customer_risk_profiles
            WHERE account_id = :acc_id
        """
        
        # Pass the variable securely to Spark's execution engine
        df = spark.sql(query, args={"acc_id": account_id}).toPandas()
        
        # STRUCTURED EMPTY STATE: Tells the LLM exactly what happened without breaking schema
        if df.empty:
            return json.dumps([{"status": "NOT_FOUND", "message": f"No risk profile found for account {account_id}."}])
            
        return df.to_json(orient="records")
        
    except Exception as e:
        # Standardized error state
        return json.dumps([{"status": "DATABASE_ERROR", "message": f"Execution failed: {str(e)}"}])

# ---------------------------------------------------------
# TOOL 2: The Secure Transaction Investigator
# ---------------------------------------------------------    
@tool
@secure_db_tool(max_calls=3, time_window=30)
def get_recent_transactions(account_id: str, limit: int = 10) -> str:
    """
    Retrieves the most recent individual transactions for an account.
    Use this tool to investigate specific anomalies, trace money movement, 
    or find the exact transaction causing a ledger discrepancy.
    """
    try:
        # 1. Fetch the active Databricks Spark session
        spark = SparkSession.builder.getOrCreate()

        # MITIGATION 1: Defeat Agent DoS (Context Flooding)
        # Force the LLM's requested limit into an integer and hard-cap it at 50.
        safe_limit = min(abs(int(limit)), 50)
        
        # MITIGATION 2: Defeat SQL Injection
        # We use a parameterized placeholder (:acc_id) for the untrusted string input.
        # (Note: safe_limit is safe to use in an f-string because we strictly cast it to an int above)
        query = f"""
            SELECT step, tx_type, amount, beneficiary_id, is_high_risk_tx_type, orig_balance_discrepancy
            FROM portfolio_catalog.compliance_project.paysim_silver
            WHERE originator_id = :acc_id
            ORDER BY step DESC
            LIMIT {safe_limit}
        """
        
        # Pass the account_id securely into Spark's execution engine
        df = spark.sql(query, args={"acc_id": account_id}).toPandas()
        
        # STRUCTURED EMPTY STATE
        if df.empty:
            return json.dumps([{"status": "NOT_FOUND", "message": f"No recent transactions found for account {account_id}."}])
            
        return df.to_json(orient="records")
        
    except ValueError:
        # Catch cases where the LLM passes a non-numeric string as the limit
        return json.dumps([{"status": "INVALID_INPUT", "message": "Invalid limit parameter provided. Must be an integer."}])
    except Exception as e:
        return json.dumps([{"status": "DATABASE_ERROR", "message": f"Execution failed: {str(e)}"}])    
# ---------------------------------------------------------
# TOOL EXPORT
# ---------------------------------------------------------
# We bundle them here so other files can import the entire "toolbelt" at once.
compliance_tools = [get_customer_risk_profile, get_recent_transactions]
