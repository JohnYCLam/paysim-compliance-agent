import streamlit as st
import sys
import os
from langchain_core.messages import HumanMessage

# Ensure the app can find the src directory
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import your compiled agent
from src.agent.graph import compliance_app

# ---------------------------------------------------------
# UI Configuration
# ---------------------------------------------------------
st.set_page_config(page_title="AML Agent", page_icon="🛡️", layout="centered")

st.title("🛡️ AML Compliance Agent")
st.markdown("Automated ledger investigations securely powered by Databricks Unity Catalog.")

# Initialize the chat memory in the browser session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render the historical chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------------------------------------------------------
# Chat Execution Logic
# ---------------------------------------------------------
# Wait for the user to type a prompt
if prompt := st.chat_input("Enter account ID for a compliance audit (e.g., C109355026)..."):
    
    # 1. Display the user's message immediately
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Show a loading spinner while the agent does the heavy lifting
    with st.chat_message("assistant"):
        with st.spinner("Analyzing ledger and executing Unity Catalog tools..."):
            try:
                # Format the state for LangGraph
                initial_state = {
                    "messages": [HumanMessage(content=prompt)],
                    "next_node": "",
                    "is_security_breach": False
                }
                
                # Execute the graph (This triggers your Guardrails, Supervisor, and Tools)
                final_state = compliance_app.invoke(initial_state)
                
                # Extract the final scrubbed output from the Output Guardrail
                agent_response = final_state["messages"][-1].content
                
                # Display the response and save it to memory
                st.markdown(agent_response)
                st.session_state.messages.append({"role": "assistant", "content": agent_response})
                
            except Exception as e:
                st.error(f"System Error: {str(e)}")