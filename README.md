# 🛡️ Agentic AI for AML Compliance Assurance

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
* **Guardrail Node:** The security perimeter. Intercepts prompt injections and jailbreak attempts before they reach the reasoning engine.
* **Supervisor Agent:** Analyzes the user request and routes it to the appropriate sub-agent.
* **Data Auditor Worker:** A specialized agent equipped with parameterized Unity Catalog tools to fetch risk profiles and investigate anomalous line items.

## 🚀 Key Technical Achievements
* **Zero-Hallucination Mathematics:** Eliminated LLM arithmetic errors by shifting complex ledger reconciliation to the PySpark Silver layer.
* **Defeated SQL Injection:** Secured all AI-to-Database interactions using PySpark parameterized queries (`args` dictionaries) rather than vulnerable f-strings.
* **Mitigated Agent DoS:** Enforced deterministic Python bounds (`min()`, `int()`) on the agent's data retrieval tools, preventing context window flooding and API cost overruns.
* **Data Minimization:** Explicit column selection ensures the AI only receives the analytical fields required for fraud detection, naturally protecting simulated PII.

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
│   │   ├── tools.py                 # Unity Catalog secure tool definitions
│   │   ├── state.py                 # LangGraph TypedDict memory state
│   │   ├── nodes/
│   │   │   ├── guardrail.py         # Prompt injection interceptor
│   │   │   ├── supervisor.py        
│   │   │   └── auditor_worker.py    
│   │   │
│   │   └── graph.py                 # Graph compilation and routing logic
│   │
├── requirements.txt                 
└── README.md
```