
##  Executive Overview

This evaluation pipeline is an end-to-end framework designed to measure, benchmark, and audit the performance of a Production Retrieval-Augmented Generation (RAG) System built on top of **FastAPI**, **LangGraph**, and **LangSmith**. 

The pipeline automates the entire evaluation lifecycle:
1. **API Seeding / Data Ingestion:** Triggers real system requests to capture operational traces.
2. **Trace Extraction:** Pulls top-level execution flows and child tool logs from LangSmith.
3. **LLM-as-a-Judge Evaluation:** Uses `gpt-4o` with structured Pydantic outputs to grade performance across 4 core RAG metrics.
4. **Executive Report Generation:** Compiles findings into a PDF executive dashboard.

---

##  Pipeline Architecture & Step-by-Step Flow

Below is the complete architectural flow showing how data flows from dataset ingestion to trace scoring and report generation:

```mermaid
flowchart TD
    %% Node Definitions
    subgraph S1 ["1. SEED API CALLS"]
        A["rag_evaluation_questions.json"] -->|HTTPX Client| B["FastAPI /query Endpoint"]
    end

    subgraph S2 ["2. LANGSMITH TRACE CAPTURE"]
        C["LangGraph Execution Engine"] -->|Logs Traces & Tool Outputs| D["LangSmith Platform"]
    end

    subgraph S3 ["3. TRACE EXTRACTION"]
        E["LangSmith Client API"]
        F1["Extract Input Query"]
        F2["Extract Retrieved Context Chunks"]
        F3["Extract Final Agent Output"]
        
        E --> F1
        E --> F2
        E --> F3
    end

    subgraph S4 ["4. LLM-AS-A-JUDGE EVALUATION"]
        G["ChatOpenAI: gpt-4o + Pydantic Structured Output"]
        H1["Context Precision"]
        H2["Context Recall"]
        H3["Faithfulness"]
        H4["Answer Relevance"]
        H5["Overall Score & Justification"]

        G --> H1
        G --> H2
        G --> H3
        G --> H4
        G --> H5
    end

    subgraph S5 ["5. PDF EXECUTIVE REPORT"]
        I["ReportLab Engine"] --> J["PDF Output Report"]
    end

    %% Flow Connections between steps
    B -->|Generates Execution Traces| C
    D -->|Fetch Root Traces & Child Tool Chunks| E
    F1 & F2 & F3 -->|Pass Query + Context + Output| G
    H1 & H2 & H3 & H4 & H5 -->|Structured Evaluation Scores| I

    %% Styling
    classDef stepStyle fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#fff
    classDef nodeStyle fill:#0f172a,stroke:#94a3b8,color:#f8fafc
    
    class S1,S2,S3,S4,S5 stepStyle
    class A,B,C,D,E,F1,F2,F3,G,H1,H2,H3,H4,H5,I,J nodeStyle
```

---

##  Detailed Step-by-Step Execution Breakdown

### Step 1: Seeding API with Evaluation Questions (`hit_api_with_questions`)
- Reads test queries from `rag_evaluation_questions.json`.
- Sends POST requests to `http://127.0.0.1:8000/query` using an asynchronous/streamed `httpx.Client`.
- Generates live production-like execution traces inside the active LangGraph execution graph.
- Implements a waiting period (e.g., 10 seconds) post-seeding to ensure all asynchronous background traces fully sync with LangSmith.

### Step 2: Fetching LangGraph Root Traces (`fetch_latest_traces`)
- Connects to LangSmith via `Client()` and queries the project run store for top-level root executions (`execution_order=1`).
- Filters execution nodes specifically for `name == "LangGraph"`.
- Recursively inspects child tool runs (`run_type in ["retriever", "tool"]`) to capture the exact context chunks retrieved by vector search nodes.

### Step 3: LLM-as-a-Judge Evaluation (`evaluate_trace`)
- Builds an evaluation prompt combining the **User Query**, **Retrieved Context Chunks**, and **Generated Agent Output**.
- Uses `ChatOpenAI(model="gpt-4o", temperature=0)` configured with `with_structured_output(AdvancedRAGEvaluation)`.
- Returns strictly typed metrics:
  - **Context Precision:** Signal-to-noise ratio in retrieved context.
  - **Context Recall:** Coverage of necessary information retrieved.
  - **Faithfulness:** Groundedness of the answer against retrieved context (hallucination check).
  - **Answer Relevance:** Direct alignment between user query and generated answer.
  - **Overall Score:** Weighted aggregated health score.

### Step 4: Executive PDF Generation (`generate_executive_pdf`)
- Compiles evaluated trace data into a high-level executive PDF dashboard using `ReportLab`.
- Includes high-level KPI cards (Overall Health, Precision, Recall, Faithfulness, Relevance).
- Renders detailed trace performance breakdown tables with visual color-coded score indicator bars.

---

##  Evaluation Matrix & Benchmark Results

The table below demonstrates the evaluation breakdown across test traces processed through the `gpt-4o` evaluation judge:

| Trace ID | User Question | Precision | Recall | Faithfulness | Relevance | Overall Score | Visual Bar | Justification / Key Findings |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **#019fd290** | What are the five levels of complexity for building multi-agent applications in Pydantic AI? | 0.90 | 0.90 | 0.95 | 1.00 | **0.94** | 🟢 `[█████████░]` | Highly faithful and relevant. Minor extraneous context slightly impacted precision. |
| **#019fd28f** | What database is used in the RAG example, and how is it run locally? | 0.90 | 0.80 | 0.95 | 0.90 | **0.89** | 🟢 `[████████░░]` | Accurately cited PostgreSQL + pgvector Docker command. Minor recall gap regarding SDK role. |
| **#019fd28e** | How does Pydantic AI's dependency injection system provide data to system prompts, tools, and output validators? | 0.90 | 0.85 | 0.95 | 0.90 | **0.90** | 🟢 `[█████████░]` | Strong alignment. Clear explanation of `RunContext` and `deps_type`. |
| **#019fd28d** | What are the two decorators used to register function tools with an agent, and how do they differ? | 0.80 | 0.70 | 0.90 | 0.90 | **0.85** | 🟢 `[████████.░]` | Captured `@agent.tool` well; missed explicit mention of `@agent.tool_plain` in retrieved chunk. |

---

> **Note:** You can easily scale this pipeline to evaluate across a larger set of questions by increasing the `LIMIT_QUESTIONS` parameter or targeting additional test categories.