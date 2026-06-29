An enterprise-grade, multi-agent AI system built to automate Anti-Money Laundering (AML) ledger investigations. This project combines a PySpark Medallion data pipeline (Databricks Unity Catalog) with a secure, stateful LangGraph agent architecture.

## 🎯 Project Motivation
Having previously managed Compliance Assurance at an international banking level, I have experienced the operational bottlenecks of manual ledger investigations. Currently completing my Master of Artificial Intelligence in Melbourne, I engineered this architecture to solve a critical industry challenge: safely deploying Generative AI in highly regulated environments without compromising data governance or mathematical accuracy.

## 🏗️ Architecture Overview

This project is divided into two strict operational phases:

### Phase 1: The Deterministic Data Foundation (Medallion Architecture)
LLMs are prone to mathematical hallucinations. To mitigate this, all aggregations and ledger logic are pre-computed deterministically using PySpark before the AI ever touches the data.
* **Bronze Layer:** Raw ingestion of the synthetic PaySim mobile money dataset into Unity Catalog Volumes with strict `StructType` enforcement.
* **Silver Layer:** Data cleansing, integrity filtering (dropping impossible financial states), and feature engineering (e.g., calculating ledger discrepancies and high-risk transaction flags).
* **Gold Layer:** Pre-aggregated Customer Risk Profiles optimized for low-latency AI lookup.

### Phase 2: The Multi-Agent Orchestrator (LangGraph)
A stateful workflow designed around the Principle of Least Privilege. The LLM does not write SQL; it uses strictly parameterized Python tools to interact with the Gold and Silver tables.
* **The "Guardrail Sandwich" (Ingress & Egress):**
    * **Input Guardrail:** The security perimeter. Powered by a specialized safety model to intercept prompt injections, persona hijacking, and raw SQL exploitation attempts before they reach the reasoning engine.
    * **Output Guardrail (DLP):** An independent Data Loss Prevention filter that redacts Personally Identifiable Information (PII) and scrubs internal database infrastructure jargon (e.g., table names, cluster details) from the final report.
* **Supervisor Agent:** Analyzes the user request and routes it to the appropriate sub-agent or determines when the investigation is complete.
* **Data Auditor Worker & Tool Node:** A specialized agent equipped with secure Unity Catalog tools to fetch risk profiles and investigate anomalous line items, backed by a dedicated LangGraph `ToolNode` for isolated Python execution.

## 🚀 Key Technical Achievements
* **Zero-Hallucination Mathematics:** Eliminated LLM arithmetic errors by shifting complex ledger reconciliation to the PySpark Silver layer.
* **Defeated SQL Injection:** Secured all AI-to-Database interactions using PySpark parameterized queries (`args` dictionaries) rather than vulnerable string interpolation.
* **Circuit Breakers & Rate Limiting:** Engineered an enterprise Python decorator (`@secure_db_tool`) to trip the circuit if the database crashes, stopping the AI from entering infinite loops. It also hard-caps query limits to prevent context window flooding and API cost overruns.
* **Structured Empty States:** Ensured database tools return consistent JSON schemas (e.g., `NOT_FOUND`) even when data is missing, preventing the orchestrator from panicking and hallucinating errors.
* **Full-Stack Observability:** Integrated Databricks MLflow autologging to trace LangGraph execution, monitor step-by-step tool latency, and visualize agent routing logic.

##  Demo
![](docs/images/demo.png)

## 📂 Repository Structure
```text
paysim_compliance_agent/
│
├── src/
│   ├── data_pipeline/
│   │   ├── 01_ingest_bronze.py      
│   │   ├── 02_transform_silver.py   
│   │   └── 03_aggregate_gold.py     
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── tools.py                 # Unity Catalog secure tool & decorators
│   │   ├── state.py                 # LangGraph TypedDict memory state
│   │   ├── nodes/
│   │   │   ├── guardrail.py         # Ingress prompt injection interceptor
│   │   │   ├── supervisor.py        # Routing logic
│   │   │   ├── auditor_worker.py    # Investigation logic
│   │   │   └── output_guardrail.py  # Egress DLP and PII masking filter
│   │   │
│   │   └── graph.py                 # Graph compilation and execution
│   │
│   └── utils/
│       └── llm_factory.py           # Centralized LLM client initialization
│
├── tests/
│   ├── test_guardrails.ipynb        # Ingress and Egress isolated tests
│   └── test_e2e_pipeline.ipynb      # End-to-end graph and MLflow trace tests
│
├── requirements.txt                 
└── README.md
```