# import os
# import json
# import httpx
# import time
# from datetime import datetime
# from typing import List, Dict, Any, Optional

# from dotenv import load_dotenv
# from pydantic import BaseModel, Field
# from langchain_openai import ChatOpenAI
# from langsmith import Client

# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import (
#     SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
# )
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib import colors
# from reportlab.graphics.shapes import Drawing, Rect






# from datetime import datetime
# import re
# from typing import Any, Dict, List

# from reportlab.graphics.shapes import Drawing, Rect
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import A4
# from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
# from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# # ==========================================
# # 1. CONFIGURATION & SETUP
# # ==========================================
# load_dotenv()

# PROJECT_NAME = os.getenv("LANGCHAIN_PROJECT", "pydocs-ai")
# PDF_OUTPUT_PATH = "rag_evaluation_executive_report.pdf"
# DATASET_PATH = os.path.join(os.path.dirname(__file__), "rag_evaluation_questions.json")
# API_URL = "http://127.0.0.1:8000/query"
# EVAL_MODEL_NAME = "gpt-4o"
# LIMIT_QUESTIONS = 5

# client = Client()
# judge_llm = ChatOpenAI(model=EVAL_MODEL_NAME, temperature=0)


# # ==========================================
# # 2. HELPER FUNCTIONS FOR CLEAN PARSING
# # ==========================================
# def extract_dataset_question(q: Any) -> str:
#     """Safely extracts clean question string from raw dataset JSON."""
#     if isinstance(q, dict):
#         return str(q.get("question", "")).strip()
#     return str(q).strip()


# def extract_trace_clean_text(raw_input: Any) -> str:
#     """Extracts clean string content from complex trace inputs/outputs."""
#     if isinstance(raw_input, str):
#         return raw_input
    
#     if isinstance(raw_input, dict):
#         if "q" in raw_input:
#             return extract_trace_clean_text(raw_input["q"])
#         if "input" in raw_input:
#             return extract_trace_clean_text(raw_input["input"])
#         if "content" in raw_input:
#             return extract_trace_clean_text(raw_input["content"])
#         if "messages" in raw_input:
#             return extract_trace_clean_text(raw_input["messages"])
#         if "kwargs" in raw_input and "content" in raw_input["kwargs"]:
#             return extract_trace_clean_text(raw_input["kwargs"]["content"])

#     if isinstance(raw_input, (list, tuple)) and len(raw_input) > 0:
#         last_item = raw_input[-1]
#         return extract_trace_clean_text(last_item)

#     if hasattr(raw_input, "content"):
#         return str(raw_input.content)

#     return str(raw_input)


# # ==========================================
# # 3. SEED API CALLS
# # ==========================================
# def hit_api_with_questions() -> List[str]:
#     """Reads JSON questions and sends POST requests to trigger LangSmith traces."""
#     print("\n" + "="*80)
#     print("🚀 STEP 1: SEEDING API WITH EVALUATION QUESTIONS")
#     print("="*80)
    
#     if not os.path.exists(DATASET_PATH):
#         print(f"⚠️ Warning: Dataset file not found at {DATASET_PATH}. Skipping API seed.")
#         return []

#     with open(DATASET_PATH, "r", encoding="utf-8") as f:
#         data = json.load(f)
    
#     raw_questions = data.get("questions", [])[:LIMIT_QUESTIONS]
#     sent_questions = []

#     print(f"📊 Total Questions Selected for Evaluation: {len(raw_questions)}\n")

#     with httpx.Client(timeout=60.0) as http_client:
#         for idx, q in enumerate(raw_questions, 1):
#             q_text = extract_dataset_question(q)
#             sent_questions.append(q_text)
            
#             print(f"  [Req {idx}/{len(raw_questions)}] 📤 Sending Query: \"{q_text[:70]}...\"")
            
#             try:
#                 start_time = time.time()
#                 with http_client.stream("POST", API_URL, json={"q": q_text}) as response:
#                     response.raise_for_status()
#                     _ = [chunk for chunk in response.iter_text() if chunk]
#                 elapsed = time.time() - start_time
#                 print(f"  [Req {idx}/{len(raw_questions)}] ✅ Success (Latency: {elapsed:.2f}s)")
#             except Exception as e:
#                 print(f"  [Req {idx}/{len(raw_questions)}] ❌ API Error: {str(e)}")

#     print("\n⏳ Waiting 5 seconds for LangSmith traces to fully ingest & sync...")
#     time.sleep(5)
#     return sent_questions


# # ==========================================
# # 4. FETCH TRACES (ROOT LANGGRAPH ONLY)
# # ==========================================
# def fetch_latest_traces(limit: int) -> List[Dict[str, Any]]:
#     print("\n" + "="*80)
#     print("🚀 STEP 2: FETCHING LANGGRAPH ROOT TRACES FROM LANGSMITH")
#     print("="*80)
#     print(f"🔍 Searching Project: '{PROJECT_NAME}' for Top-Level 'LangGraph' Runs...\n")

#     runs = list(client.list_runs(
#         project_name=PROJECT_NAME,
#         execution_order=1,
#         limit=limit * 3
#     ))

#     # Keep only LangGraph executions
#     langgraph_runs = [r for r in runs if r.name == "LangGraph"][:limit]

#     print(f"📦 Fetched {len(langgraph_runs)} Root LangGraph Traces.")
    
#     extracted_data = []

#     for idx, r in enumerate(langgraph_runs, 1):
#         trace_id = str(r.id)
#         short_id = trace_id[:8]
        
#         # 1. Parse Input User Query
#         query = "N/A"
#         if r.inputs:
#             query = extract_trace_clean_text(r.inputs)

#         # 2. Extract Output Response
#         final_output = "N/A"
#         if r.outputs:
#             final_output = extract_trace_clean_text(r.outputs)

#         # 3. Extract Context Chunks from Child Tool Executions
#         retrieved_chunks = []
#         child_runs = list(client.list_runs(trace_id=r.trace_id))
        
#         for child in child_runs:
#             is_retriever_node = (
#                 child.run_type in ["retriever", "tool"] 
#                 or any(kw in child.name.lower() for kw in ["retriev", "search", "vector", "rag_search_tool"])
#             )

#             if is_retriever_node and child.outputs:
#                 docs = child.outputs.get("documents") or child.outputs.get("output") or child.outputs.get("result")
                
#                 if isinstance(docs, dict):
#                     docs = docs.get("documents") or docs.get("messages") or [docs]

#                 if isinstance(docs, list):
#                     for doc in docs:
#                         if isinstance(doc, dict):
#                             content = doc.get("page_content") or doc.get("text") or doc.get("content") or str(doc)
#                             retrieved_chunks.append(content)
#                         elif hasattr(doc, "page_content"):
#                             retrieved_chunks.append(doc.page_content)
#                         elif isinstance(doc, str):
#                             retrieved_chunks.append(doc)

#         print("-" * 80)
#         print(f"📌 TRACE #{idx} [ID: {short_id} | Full ID: {trace_id}]")
#         print(f"❓ User Query     : {query}")
#         print(f"📦 Chunks Captured : {len(retrieved_chunks)}")
        
#         if retrieved_chunks:
#             for c_idx, chunk in enumerate(retrieved_chunks, 1):
#                 clean_chunk = chunk.replace('\n', ' ')[:120]
#                 print(f"   ├─ Chunk {c_idx}: \"{clean_chunk}...\"")
#         else:
#             print("   ⚠️ No Chunks Captured (Query might have hit Guardrail or Direct Agent Response)")

#         print(f"🤖 Final Output   : {str(final_output)[:120]}...")
#         print("-" * 80)

#         extracted_data.append({
#             "trace_id": short_id,
#             "full_trace_id": trace_id,
#             "question": str(query),
#             "retrieved_chunks": retrieved_chunks,
#             "agent_output": str(final_output)
#         })

#     return extracted_data


# # ==========================================
# # 5. LLM-AS-A-JUDGE EVALUATION
# # ==========================================
# class AdvancedRAGEvaluation(BaseModel):
#     context_precision: float = Field(
#         description="Score 0.0-1.0: Measure of signal-to-noise ratio in retrieved context."
#     )
#     context_recall: float = Field(
#         description="Score 0.0-1.0: Measures if all necessary information was retrieved."
#     )
#     faithfulness: float = Field(
#         description="Score 0.0-1.0: Measures groundedness without hallucination."
#     )
#     answer_relevance: float = Field(
#         description="Score 0.0-1.0: Measures if the answer directly addresses the question."
#     )
#     overall_score: float = Field(
#         description="Weighted average score 0.0-1.0 representing total pipeline health."
#     )
#     reason: str = Field(
#         description="Detailed justification for scores."
#     )

# structured_judge = judge_llm.with_structured_output(AdvancedRAGEvaluation)

# def evaluate_trace(trace: Dict[str, Any]) -> Dict[str, Any]:
#     question = trace["question"]
#     chunks_list = trace["retrieved_chunks"]
#     answer = trace["agent_output"]

#     if not chunks_list:
#         chunks_str = "NO_CONTEXT_RETRIEVED (Interaction was handled directly or rejected by Guardrails)"
#     else:
#         chunks_str = "\n---\n".join(chunks_list)

#     prompt = f"""
#     You are an expert Production RAG Evaluation Judge. Evaluate the following RAG interaction.

#     USER QUESTION: {question}
#     RETRIEVED CONTEXT CHUNKS:
#     {chunks_str}
#     GENERATED ANSWER: {answer}

#     Assess rigorously on:
#     1. Context Precision (0.0-1.0): If no context retrieved, score 0.0 unless query required no context.
#     2. Context Recall (0.0-1.0): If no context retrieved, score 0.0 unless query required no context.
#     3. Faithfulness (0.0-1.0): Groundedness of the answer against context/knowledge.
#     4. Answer Relevance (0.0-1.0): Directly addresses user prompt.
#     5. Overall Score (0.0-1.0): Comprehensive assessment.
#     """
    
#     res: AdvancedRAGEvaluation = structured_judge.invoke(prompt)

#     return {
#         "trace_id": trace["trace_id"],
#         "question": question,
#         "chunks_count": len(chunks_list),
#         "context_precision": res.context_precision,
#         "context_recall": res.context_recall,
#         "faithfulness": res.faithfulness,
#         "answer_relevance": res.answer_relevance,
#         "overall": res.overall_score,
#         "reason": res.reason
#     }



# # ==========================================
# # HELPER: CLEAN MARKDOWN & FORMAT TEXT
# # ==========================================
# def clean_markdown_text(text: str) -> str:
#     """Markdown symbols (##, **, __, `, etc.) remove karta hai aur cleanly format karta hai."""
#     if not text:
#         return ""
#     # Header aur Bullet formatting cleanup
#     text = re.sub(r"#{1,6}\s*", "", text)  # Removes ##, ###
#     text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)  # Converts **bold** to <b>bold</b> HTML for ReportLab
#     text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)  # Converts *italic* to <i>italic</i>
#     text = re.sub(r"`([^`]+)`", r"\1", text)  # Removes backticks
#     text = re.sub(r"^[-\*]\s+", "• ", text, flags=re.MULTILINE)  # Replaces - or * bullets with clean • symbol
#     text = re.sub(r"\n+", "<br/>", text)  # Converts linebreaks to ReportLab <br/>
#     return text.strip()


# # ==========================================
# # 6. PDF REPORT GENERATOR (UPDATED)
# # ==========================================
# def draw_score_bar(score: float, width=55, height=8):
#     d = Drawing(width, height)
#     d.add(Rect(0, 0, width, height, fillColor=colors.HexColor('#E2E8F0'), strokeColor=None, rx=3, ry=3))
    
#     if score >= 0.8:
#         fill_col = colors.HexColor('#10B981')
#     elif score >= 0.5:
#         fill_col = colors.HexColor('#F59E0B')
#     else:
#         fill_col = colors.HexColor('#EF4444')

#     fill_width = max(0.0, min(1.0, score)) * width
#     if fill_width > 0:
#         d.add(Rect(0, 0, fill_width, height, fillColor=fill_col, strokeColor=None, rx=3, ry=3))
#     return d


# def generate_executive_pdf(eval_results: List[Dict[str, Any]], filepath: str):
#     print("\n" + "="*80)
#     print("🚀 STEP 4: GENERATING EXECUTIVE PDF REPORT")
#     print("="*80)

#     # Page Margins Optimized for A4
#     doc = SimpleDocTemplate(
#         filepath, pagesize=A4,
#         rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
#     )
#     styles = getSampleStyleSheet()
#     story = []

#     # Color Palette
#     PRIMARY = colors.HexColor('#0F172A')     # Slate 900
#     SECONDARY = colors.HexColor('#475569')   # Slate 600
#     ACCENT = colors.HexColor('#2563EB')      # Blue 600
#     BG_LIGHT = colors.HexColor('#F8FAFC')    # Slate 50
#     BORDER_COL = colors.HexColor('#CBD5E1')  # Slate 300

#     # Custom Typography Styles
#     title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=15, leading=18, textColor=PRIMARY, fontName='Helvetica-Bold')
#     meta_style = ParagraphStyle('DocMeta', parent=styles['Normal'], fontSize=8, leading=11, textColor=SECONDARY)
#     h2_style = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=11, leading=14, textColor=PRIMARY, fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=6)
#     card_title_style = ParagraphStyle('CardTitle', parent=styles['Normal'], fontSize=7, leading=9, textColor=SECONDARY, alignment=1)
#     card_val_style = ParagraphStyle('CardValue', parent=styles['Normal'], fontSize=12, leading=14, textColor=PRIMARY, fontName='Helvetica-Bold', alignment=1)
    
#     # Table Specific Styles (Auto-wrap fixed!)
#     table_header_style = ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=7.5, leading=9, textColor=colors.white, fontName='Helvetica-Bold')
#     body_style = ParagraphStyle('TableText', parent=styles['Normal'], fontSize=7, leading=9.5, textColor=PRIMARY)
#     reason_style = ParagraphStyle('ReasonText', parent=styles['Normal'], fontSize=6.8, leading=9, textColor=SECONDARY)

#     # Header Section
#     header_data = [
#         [
#             Paragraph("<b>PRODUCTION RAG EVALUATION REPORT</b>", title_style),
#             Paragraph(f"<b>Project:</b> {PROJECT_NAME}<br/><b>Date:</b> {datetime.now().strftime('%b %d, %Y | %H:%M')}<br/><b>Judge:</b> {EVAL_MODEL_NAME}", meta_style)
#         ]
#     ]
#     header_table = Table(header_data, colWidths=[330, 205])
#     header_table.setStyle(TableStyle([
#         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#         ('ALIGN', (1, 0), (1, 0), 'RIGHT')
#     ]))
#     story.append(header_table)
#     story.append(Spacer(1, 4))
#     story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=8))

#     # Calculate KPIs
#     total = len(eval_results)
#     avg_overall = sum(r['overall'] for r in eval_results) / total if total > 0 else 0
#     avg_prec = sum(r['context_precision'] for r in eval_results) / total if total > 0 else 0
#     avg_rec = sum(r['context_recall'] for r in eval_results) / total if total > 0 else 0
#     avg_faith = sum(r['faithfulness'] for r in eval_results) / total if total > 0 else 0
#     avg_rel = sum(r['answer_relevance'] for r in eval_results) / total if total > 0 else 0

#     # KPI Summary Cards
#     kpi_data = [
#         [
#             Paragraph("OVERALL HEALTH", card_title_style),
#             Paragraph("CTX PRECISION", card_title_style),
#             Paragraph("CTX RECALL", card_title_style),
#             Paragraph("FAITHFULNESS", card_title_style),
#             Paragraph("ANSWER RELEVANCE", card_title_style)
#         ],
#         [
#             Paragraph(f"{avg_overall:.2f}", card_val_style),
#             Paragraph(f"{avg_prec:.2f}", card_val_style),
#             Paragraph(f"{avg_rec:.2f}", card_val_style),
#             Paragraph(f"{avg_faith:.2f}", card_val_style),
#             Paragraph(f"{avg_rel:.2f}", card_val_style)
#         ]
#     ]
    
#     kpi_table = Table(kpi_data, colWidths=[107]*5)
#     kpi_table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
#         ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COL),
#         ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COL),
#         ('PADDING', (0, 0), (-1, -1), 4),
#         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#     ]))
#     story.append(kpi_table)
#     story.append(Spacer(1, 6))

#     # Trace Breakdown Section
#     story.append(Paragraph("Trace Performance Breakdown", h2_style))
    
#     table_headers = [
#         Paragraph("Trace & Question", table_header_style),
#         Paragraph("Prec.", table_header_style),
#         Paragraph("Rec.", table_header_style),
#         Paragraph("Faith.", table_header_style),
#         Paragraph("Relev.", table_header_style),
#         Paragraph("Visual", table_header_style),
#         Paragraph("Justification / Reason", table_header_style)
#     ]
#     table_rows = [table_headers]

#     for r in eval_results:
#         # Full question without truncation (Paragraph auto-wraps cleanly)
#         full_question = clean_markdown_text(r["question"])
#         trace_cell = Paragraph(f"<b>#{r['trace_id'][:8]}</b><br/><font color='#475569'>{full_question}</font>", body_style)
        
#         prec_cell = Paragraph(f"{r['context_precision']:.2f}", body_style)
#         rec_cell = Paragraph(f"{r['context_recall']:.2f}", body_style)
#         faith_cell = Paragraph(f"{r['faithfulness']:.2f}", body_style)
#         rel_cell = Paragraph(f"{r['answer_relevance']:.2f}", body_style)
#         bar_cell = draw_score_bar(r['overall'], width=50, height=7)
        
#         # Reason cleaned from Markdown symbols
#         clean_reason = clean_markdown_text(r["reason"])
#         reason_cell = Paragraph(clean_reason, reason_style)

#         table_rows.append([trace_cell, prec_cell, rec_cell, faith_cell, rel_cell, bar_cell, reason_cell])

#     # Adjusted Column Widths (Total Width = 535 pt for A4 Page)
#     details_table = Table(table_rows, colWidths=[130, 32, 32, 32, 35, 55, 219])
#     details_table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
#         ('PADDING', (0, 0), (-1, -1), 4),
#         ('VALIGN', (0, 0), (-1, -1), 'TOP'),
#         ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COL),
#         ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
#     ]))

#     story.append(details_table)
#     doc.build(story)
#     print(f"✅ Executive PDF Generated Successfully: {filepath}\n")


# # ==========================================
# # 7. MAIN PIPELINE EXECUTION
# # ==========================================
# def main():
#     hit_api_with_questions()
#     traces = fetch_latest_traces(limit=LIMIT_QUESTIONS)
    
#     if not traces:
#         print("❌ Error: No valid LangGraph traces captured. Check API connection.")
#         return

#     eval_results = []
#     print("\n" + "="*80)
#     print("🚀 STEP 3: EVALUATING TRACES WITH GPT-4O JUDGE")
#     print("="*80)
    
#     for idx, trace in enumerate(traces, 1):
#         print(f"  -> [{idx}/{len(traces)}] Evaluating Trace ID: {trace['trace_id']}...")
#         res = evaluate_trace(trace)
#         eval_results.append(res)
#         print(f"     Score: {res['overall']:.2f} | Faithfulness: {res['faithfulness']:.2f} | Precision: {res['context_precision']:.2f}")

#     generate_executive_pdf(eval_results, PDF_OUTPUT_PATH)
    
#     print("="*80)
#     print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
#     print("="*80 + "\n")

# if __name__ == "__main__":
#     main()








import json
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
import httpx
from langchain_openai import ChatOpenAI
from langsmith import Client
from pydantic import BaseModel, Field

from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ==========================================
# 1. CONFIGURATION & SETUP
# ==========================================
load_dotenv()

PROJECT_NAME = os.getenv("LANGCHAIN_PROJECT", "pydocs-ai")
PDF_OUTPUT_PATH = "rag_evaluation_executive_report.pdf"
DATASET_PATH = os.path.join(os.path.dirname(__file__), "rag_evaluation_questions.json")
API_URL = "http://127.0.0.1:8000/query"
EVAL_MODEL_NAME = "gpt-4o"
LIMIT_QUESTIONS = 30

client = Client()
judge_llm = ChatOpenAI(model=EVAL_MODEL_NAME, temperature=0)


# ==========================================
# 2. HELPER FUNCTIONS FOR CLEAN PARSING
# ==========================================
def extract_dataset_question(q: Any) -> str:
    """Safely extracts clean question string from raw dataset JSON."""
    if isinstance(q, dict):
        return str(q.get("question", "")).strip()
    return str(q).strip()


def extract_trace_clean_text(raw_input: Any) -> str:
    """Extracts clean string content from complex trace inputs/outputs."""
    if isinstance(raw_input, str):
        return raw_input

    if isinstance(raw_input, dict):
        if "q" in raw_input:
            return extract_trace_clean_text(raw_input["q"])
        if "input" in raw_input:
            return extract_trace_clean_text(raw_input["input"])
        if "content" in raw_input:
            return extract_trace_clean_text(raw_input["content"])
        if "messages" in raw_input:
            return extract_trace_clean_text(raw_input["messages"])
        if "kwargs" in raw_input and "content" in raw_input["kwargs"]:
            return extract_trace_clean_text(raw_input["kwargs"]["content"])

    if isinstance(raw_input, (list, tuple)) and len(raw_input) > 0:
        last_item = raw_input[-1]
        return extract_trace_clean_text(last_item)

    if hasattr(raw_input, "content"):
        return str(raw_input.content)

    return str(raw_input)


# ==========================================
# 3. SEED API CALLS
# ==========================================
def hit_api_with_questions() -> List[str]:
    """Reads JSON questions and sends POST requests to trigger LangSmith traces."""
    print("\n" + "=" * 80)
    print("🚀 STEP 1: SEEDING API WITH EVALUATION QUESTIONS")
    print("=" * 80)

    if not os.path.exists(DATASET_PATH):
        print(f"⚠️ Warning: Dataset file not found at {DATASET_PATH}. Skipping API seed.")
        return []

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_questions = data.get("questions", [])[:LIMIT_QUESTIONS]
    sent_questions = []

    print(f"📊 Total Questions Selected for Evaluation: {len(raw_questions)}\n")

    with httpx.Client(timeout=60.0) as http_client:
        for idx, q in enumerate(raw_questions, 1):
            q_text = extract_dataset_question(q)
            sent_questions.append(q_text)

            print(f'  [Req {idx}/{len(raw_questions)}] 📤 Sending Query: "{q_text[:70]}..."')

            try:
                start_time = time.time()
                with http_client.stream("POST", API_URL, json={"q": q_text}) as response:
                    response.raise_for_status()
                    _ = [chunk for chunk in response.iter_text() if chunk]
                elapsed = time.time() - start_time
                print(f"  [Req {idx}/{len(raw_questions)}] ✅ Success (Latency: {elapsed:.2f}s)")
            except Exception as e:
                print(f"  [Req {idx}/{len(raw_questions)}] ❌ API Error: {str(e)}")

    print("\n⏳ Waiting 10 seconds for LangSmith traces to fully ingest & sync...")
    time.sleep(10)  # Increased from 5s to 10s for better sync reliability
    return sent_questions


# ==========================================
# 4. FETCH TRACES (ROOT LANGGRAPH ONLY)
# ==========================================
def fetch_latest_traces(limit: int) -> List[Dict[str, Any]]:
    print("\n" + "=" * 80)
    print("🚀 STEP 2: FETCHING LANGGRAPH ROOT TRACES FROM LANGSMITH")
    print("=" * 80)
    print(f"🔍 Searching Project: '{PROJECT_NAME}' for Top-Level 'LangGraph' Runs...\n")

    runs = list(client.list_runs(
        project_name=PROJECT_NAME,
        execution_order=1,
        limit=limit * 3
    ))

    # Keep only LangGraph executions
    langgraph_runs = [r for r in runs if r.name == "LangGraph"][:limit]

    print(f"📦 Fetched {len(langgraph_runs)} Root LangGraph Traces.")

    extracted_data = []

    for idx, r in enumerate(langgraph_runs, 1):
        trace_id = str(r.id)
        short_id = trace_id[:8]

        # 1. Parse Input User Query
        query = "N/A"
        if r.inputs:
            query = extract_trace_clean_text(r.inputs)

        # 2. Extract Output Response
        final_output = "N/A"
        if r.outputs:
            final_output = extract_trace_clean_text(r.outputs)

        # 3. Extract Context Chunks from Child Tool Executions
        retrieved_chunks = []
        child_runs = list(client.list_runs(trace_id=r.trace_id))

        for child in child_runs:
            is_retriever_node = (
                child.run_type in ["retriever", "tool"]
                or any(kw in child.name.lower() for kw in ["retriev", "search", "vector", "rag_search_tool"])
            )

            if is_retriever_node and child.outputs:
                docs = child.outputs.get("documents") or child.outputs.get("output") or child.outputs.get("result")

                if isinstance(docs, dict):
                    docs = docs.get("documents") or docs.get("messages") or [docs]

                if isinstance(docs, list):
                    for doc in docs:
                        if isinstance(doc, dict):
                            content = doc.get("page_content") or doc.get("text") or doc.get("content") or str(doc)
                            retrieved_chunks.append(content)
                        elif hasattr(doc, "page_content"):
                            retrieved_chunks.append(doc.page_content)
                        elif isinstance(doc, str):
                            retrieved_chunks.append(doc)

        print("-" * 80)
        print(f"📌 TRACE #{idx} [ID: {short_id} | Full ID: {trace_id}]")
        print(f"❓ User Query     : {query}")
        print(f"📦 Chunks Captured : {len(retrieved_chunks)}")

        if retrieved_chunks:
            for c_idx, chunk in enumerate(retrieved_chunks, 1):
                clean_chunk = chunk.replace('\n', ' ')[:120]
                print(f'   ├─ Chunk {c_idx}: "{clean_chunk}..."')
        else:
            print("   ⚠️ No Chunks Captured (Query might have hit Guardrail or Direct Agent Response)")

        print(f"🤖 Final Output   : {str(final_output)[:120]}...")
        print("-" * 80)

        extracted_data.append({
            "trace_id": short_id,
            "full_trace_id": trace_id,
            "question": str(query),
            "retrieved_chunks": retrieved_chunks,
            "agent_output": str(final_output)
        })

    return extracted_data


# ==========================================
# 5. LLM-AS-A-JUDGE EVALUATION
# ==========================================
class AdvancedRAGEvaluation(BaseModel):
    context_precision: float = Field(
        description="Score 0.0-1.0: Measure of signal-to-noise ratio in retrieved context."
    )
    context_recall: float = Field(
        description="Score 0.0-1.0: Measures if all necessary information was retrieved."
    )
    faithfulness: float = Field(
        description="Score 0.0-1.0: Measures groundedness without hallucination."
    )
    answer_relevance: float = Field(
        description="Score 0.0-1.0: Measures if the answer directly addresses the question."
    )
    overall_score: float = Field(
        description="Weighted average score 0.0-1.0 representing total pipeline health."
    )
    reason: str = Field(
        description="Detailed justification for scores."
    )


structured_judge = judge_llm.with_structured_output(AdvancedRAGEvaluation)


def evaluate_trace(trace: Dict[str, Any]) -> Dict[str, Any]:
    question = trace["question"]
    chunks_list = trace["retrieved_chunks"]
    answer = trace["agent_output"]

    if not chunks_list:
        chunks_str = "NO_CONTEXT_RETRIEVED (Interaction was handled directly or rejected by Guardrails)"
    else:
        chunks_str = "\n---\n".join(chunks_list)

    prompt = f"""
    You are an expert Production RAG Evaluation Judge. Evaluate the following RAG interaction.

    USER QUESTION: {question}
    RETRIEVED CONTEXT CHUNKS:
    {chunks_str}
    GENERATED ANSWER: {answer}

    Assess rigorously on:
    1. Context Precision (0.0-1.0): If no context retrieved, score 0.0 unless query required no context.
    2. Context Recall (0.0-1.0): If no context retrieved, score 0.0 unless query required no context.
    3. Faithfulness (0.0-1.0): Groundedness of the answer against context/knowledge.
    4. Answer Relevance (0.0-1.0): Directly addresses user prompt.
    5. Overall Score (0.0-1.0): Comprehensive assessment.
    """

    res: AdvancedRAGEvaluation = structured_judge.invoke(prompt)

    return {
        "trace_id": trace["trace_id"],
        "question": question,
        "chunks_count": len(chunks_list),
        "context_precision": res.context_precision,
        "context_recall": res.context_recall,
        "faithfulness": res.faithfulness,
        "answer_relevance": res.answer_relevance,
        "overall": res.overall_score,
        "reason": res.reason
    }


# ==========================================
# HELPER: CLEAN MARKDOWN & FORMAT TEXT
# ==========================================
def clean_markdown_text(text: str) -> str:
    """Markdown symbols (##, **, __, `, etc.) remove karta hai aur cleanly format karta hai."""
    if not text:
        return ""
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"^[-\*]\s+", "• ", text, flags=re.MULTILINE)
    text = re.sub(r"\n+", "<br/>", text)
    return text.strip()


# ==========================================
# 6. PDF REPORT GENERATOR
# ==========================================
def draw_score_bar(score: float, width=50, height=8):
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, fillColor=colors.HexColor('#E2E8F0'), strokeColor=None, rx=3, ry=3))

    if score >= 0.8:
        fill_col = colors.HexColor('#10B981')
    elif score >= 0.5:
        fill_col = colors.HexColor('#F59E0B')
    else:
        fill_col = colors.HexColor('#EF4444')

    fill_width = max(0.0, min(1.0, score)) * width
    if fill_width > 0:
        d.add(Rect(0, 0, fill_width, height, fillColor=fill_col, strokeColor=None, rx=3, ry=3))
    return d


def generate_executive_pdf(eval_results: List[Dict[str, Any]], filepath: str):
    print("\n" + "=" * 80)
    print("🚀 STEP 4: GENERATING EXECUTIVE PDF REPORT")
    print("=" * 80)

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )
    styles = getSampleStyleSheet()
    story = []

    PRIMARY = colors.HexColor('#0F172A')
    SECONDARY = colors.HexColor('#475569')
    ACCENT = colors.HexColor('#2563EB')
    BG_LIGHT = colors.HexColor('#F8FAFC')
    BORDER_COL = colors.HexColor('#CBD5E1')

    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=15, leading=18, textColor=PRIMARY, fontName='Helvetica-Bold')
    meta_style = ParagraphStyle('DocMeta', parent=styles['Normal'], fontSize=8, leading=11, textColor=SECONDARY)
    h2_style = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=11, leading=14, textColor=PRIMARY, fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=6)
    card_title_style = ParagraphStyle('CardTitle', parent=styles['Normal'], fontSize=7, leading=9, textColor=SECONDARY, alignment=1)
    card_val_style = ParagraphStyle('CardValue', parent=styles['Normal'], fontSize=12, leading=14, textColor=PRIMARY, fontName='Helvetica-Bold', alignment=1)

    table_header_style = ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=7.5, leading=9, textColor=colors.white, fontName='Helvetica-Bold')
    body_style = ParagraphStyle('TableText', parent=styles['Normal'], fontSize=7, leading=9.5, textColor=PRIMARY)
    reason_style = ParagraphStyle('ReasonText', parent=styles['Normal'], fontSize=6.8, leading=9, textColor=SECONDARY)

    header_data = [
        [
            Paragraph("<b>PRODUCTION RAG EVALUATION REPORT</b>", title_style),
            Paragraph(f"<b>Project:</b> {PROJECT_NAME}<br/><b>Date:</b> {datetime.now().strftime('%b %d, %Y | %H:%M')}<br/><b>Judge:</b> {EVAL_MODEL_NAME}", meta_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[330, 205])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT')
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=8))

    total = len(eval_results)
    avg_overall = sum(r['overall'] for r in eval_results) / total if total > 0 else 0
    avg_prec = sum(r['context_precision'] for r in eval_results) / total if total > 0 else 0
    avg_rec = sum(r['context_recall'] for r in eval_results) / total if total > 0 else 0
    avg_faith = sum(r['faithfulness'] for r in eval_results) / total if total > 0 else 0
    avg_rel = sum(r['answer_relevance'] for r in eval_results) / total if total > 0 else 0

    kpi_data = [
        [
            Paragraph("OVERALL HEALTH", card_title_style),
            Paragraph("CTX PRECISION", card_title_style),
            Paragraph("CTX RECALL", card_title_style),
            Paragraph("FAITHFULNESS", card_title_style),
            Paragraph("ANSWER RELEVANCE", card_title_style)
        ],
        [
            Paragraph(f"{avg_overall:.2f}", card_val_style),
            Paragraph(f"{avg_prec:.2f}", card_val_style),
            Paragraph(f"{avg_rec:.2f}", card_val_style),
            Paragraph(f"{avg_faith:.2f}", card_val_style),
            Paragraph(f"{avg_rel:.2f}", card_val_style)
        ]
    ]

    kpi_table = Table(kpi_data, colWidths=[107] * 5)
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COL),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COL),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Trace Performance Breakdown", h2_style))

    table_headers = [
        Paragraph("Trace & Question", table_header_style),
        Paragraph("Prec.", table_header_style),
        Paragraph("Rec.", table_header_style),
        Paragraph("Faith.", table_header_style),
        Paragraph("Relev.", table_header_style),
        Paragraph("Visual", table_header_style),
        Paragraph("Justification / Reason", table_header_style)
    ]
    table_rows = [table_headers]

    for r in eval_results:
        full_question = clean_markdown_text(r["question"])
        trace_cell = Paragraph(f"<b>#{r['trace_id'][:8]}</b><br/><font color='#475569'>{full_question}</font>", body_style)

        prec_cell = Paragraph(f"{r['context_precision']:.2f}", body_style)
        rec_cell = Paragraph(f"{r['context_recall']:.2f}", body_style)
        faith_cell = Paragraph(f"{r['faithfulness']:.2f}", body_style)
        rel_cell = Paragraph(f"{r['answer_relevance']:.2f}", body_style)
        bar_cell = draw_score_bar(r['overall'], width=50, height=7)

        clean_reason = clean_markdown_text(r["reason"])
        reason_cell = Paragraph(clean_reason, reason_style)

        table_rows.append([trace_cell, prec_cell, rec_cell, faith_cell, rel_cell, bar_cell, reason_cell])

    details_table = Table(table_rows, colWidths=[125, 32, 32, 32, 35, 55, 220])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COL),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
    ]))

    story.append(details_table)
    doc.build(story)
    print(f"✅ Executive PDF Generated Successfully: {filepath}\n")


# ==========================================
# 7. MAIN PIPELINE EXECUTION
# ==========================================
def main():
    hit_api_with_questions()
    traces = fetch_latest_traces(limit=LIMIT_QUESTIONS)

    if not traces:
        print("❌ Error: No valid LangGraph traces captured. Check API connection.")
        return

    eval_results = []
    print("\n" + "=" * 80)
    print("🚀 STEP 3: EVALUATING TRACES WITH GPT-4O JUDGE")
    print("=" * 80)

    for idx, trace in enumerate(traces, 1):
        print(f"  -> [{idx}/{len(traces)}] Evaluating Trace ID: {trace['trace_id']}...")
        res = evaluate_trace(trace)
        eval_results.append(res)
        print(f"     Score: {res['overall']:.2f} | Faithfulness: {res['faithfulness']:.2f} | Precision: {res['context_precision']:.2f}")

    generate_executive_pdf(eval_results, PDF_OUTPUT_PATH)

    print("=" * 80)
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()