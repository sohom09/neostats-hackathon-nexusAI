"""
agent.py
LangGraph-based intelligent agent with three operational modes:
  - Mode 1: General Chat   (LLM only)
  - Mode 2: Web Search     (DuckDuckGo → LLM)
  - Mode 3: RAG Retrieval  (FAISS → LLM)

The agent classifies intent first and only invokes the required tool.
"""

import os
from typing import TypedDict, Annotated, List

from langchain_groq import ChatGroq
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
    BaseMessage,
)
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from rag_manager import RAGManager
from memory_manager import MemoryManager


# ---------------------------------------------------------------------------
# Shared tools
# ---------------------------------------------------------------------------

_search_tool = DuckDuckGoSearchRun()


# ---------------------------------------------------------------------------
# Agent state
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    messages:     Annotated[List[BaseMessage], add_messages]
    query:        str
    mode:         str          # "general" | "web_search" | "rag"
    forced_mode:  str          # if set, skip LLM classification
    context:      str          # additional context injected by tools
    sources:      List[str]    # citations shown in the UI


# ---------------------------------------------------------------------------
# LLM factory
# ---------------------------------------------------------------------------

def _get_llm() -> ChatGroq:
    return ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.5,
        max_tokens=1024,
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
    )


# ---------------------------------------------------------------------------
# Node: classify intent
# ---------------------------------------------------------------------------

CLASSIFY_PROMPT = """You are an expert query router for NEXUS AI — an enterprise-grade multi-mode intelligence platform.

Your job: classify the user query into EXACTLY ONE category.

  general
    • General knowledge, science, history, math, logic, coding help
    • Explanations, definitions, creative writing, summarisation
    • Does NOT need live internet data or specific uploaded documents
    • Examples: "What is RAG?", "Write a Python function", "Explain neural networks"

  web_search
    • Needs real-time, current, or recent information from the internet
    • Prices, news, scores, weather, recent events, latest releases
    • Examples: "Latest ChatGPT news", "Current Bitcoin price", "IPL 2025 results"

  rag
    • Needs information from uploaded enterprise/internal documents
    • Company policies, HR manuals, onboarding guides, internal reports
    • Examples: "What is the leave policy?", "Explain the onboarding steps", "What does our handbook say about..."

Rules:
  - Reply with ONLY one word: general, web_search, or rag
  - No punctuation, no explanation, no extra words
  - When in doubt between general and web_search, prefer general"""


def classify_node(state: AgentState, rag_manager: RAGManager) -> dict:
    """Classify user intent. If forced_mode is set, skip LLM call entirely."""
    # ── Fast path: manual mode selected by user ──────────────────────────────
    forced = state.get("forced_mode", "").strip()
    if forced in {"general", "web_search", "rag"}:
        # Fallback: if RAG forced but no index ready, drop to general
        if forced == "rag" and not rag_manager.is_ready():
            return {"mode": "general"}
        return {"mode": forced}

    # ── Slow path: ask LLM to classify ──────────────────────────────────────
    llm   = _get_llm()
    query = state["query"]

    response = llm.invoke([
        SystemMessage(content=CLASSIFY_PROMPT),
        HumanMessage(content=f"Query: {query}"),
    ])

    mode = response.content.strip().lower().strip(".")
    if mode not in {"general", "web_search", "rag"}:
        mode = "general"

    if mode == "rag" and not rag_manager.is_ready():
        mode = "general"

    return {"mode": mode}


# ---------------------------------------------------------------------------
# Node: web search
# ---------------------------------------------------------------------------

def web_search_node(state: AgentState) -> dict:
    """Invoke DuckDuckGo and store results as context."""
    query = state["query"]
    try:
        results = _search_tool.run(query)
        return {
            "context": results,
            "sources": ["🌐 DuckDuckGo Web Search"],
        }
    except Exception as exc:
        return {
            "context": f"Web search temporarily unavailable: {exc}",
            "sources": [],
        }


# ---------------------------------------------------------------------------
# Node: RAG retrieval
# ---------------------------------------------------------------------------

def rag_retrieval_node(state: AgentState, rag_manager: RAGManager) -> dict:
    """Retrieve the top-k relevant document chunks from FAISS."""
    query = state["query"]
    docs  = rag_manager.search(query, k=4)

    if docs:
        context = "\n\n".join(
            f"[Source: {doc.metadata.get('source', 'Document')}]\n{doc.page_content}"
            for doc in docs
        )
        sources = list({doc.metadata.get("source", "Document") for doc in docs})
        return {"context": context, "sources": [f"📄 {s}" for s in sources]}

    return {
        "context": "No relevant content found in the knowledge base.",
        "sources": [],
    }


# ---------------------------------------------------------------------------
# Node: generate final response
# ---------------------------------------------------------------------------

GENERAL_SYSTEM = """\
You are NEXUS AI — an elite, enterprise-grade conversational intelligence assistant.

Core capabilities:
• Deep expertise across technology, science, business, mathematics, and the humanities
• Expert-level software engineering (Python, JavaScript, SQL, system design, algorithms)
• Structured reasoning, analysis, and step-by-step problem solving
• Clear, professional communication tailored to the user's level

Formatting guidelines:
• Use markdown: ## headers, **bold** key terms, bullet points, numbered steps
• Wrap ALL code in fenced code blocks with the language tag (```python, ```sql, etc.)
• For multi-step answers: use numbered lists
• Keep answers concise but complete — avoid filler phrases
• End complex answers with a brief "Key Takeaway" or "Summary" section

Tone: Expert, precise, professional — like a senior consultant explaining to a colleague."""

WEB_SYSTEM_TEMPLATE = """\
You are NEXUS AI — an enterprise intelligence assistant with live web search capability.

The following real-time search results were retrieved for the user's query:

────────────────────────────────────────────────────────────────
{context}
────────────────────────────────────────────────────────────────

Your task:
1. Synthesise the search results into a clear, accurate, well-structured answer
2. Prioritise the most recent and relevant information
3. Use ## headers and bullet points to organise information
4. If results conflict, highlight the discrepancy and present both sides
5. Conclude with a brief **Summary** line
6. Always note: “Source: Live web search via DuckDuckGo” at the end

Do NOT fabricate details beyond what the search results provide."""

RAG_SYSTEM_TEMPLATE = """\
You are NEXUS AI — an enterprise intelligence assistant with access to the organisation's internal knowledge base.

The following content was retrieved from enterprise documents relevant to the user's query:

────────────────────────────────────────────────────────────────
{context}
────────────────────────────────────────────────────────────────

Your task:
1. Answer the user's question using ONLY the information in the retrieved context above
2. Quote or paraphrase specific sections directly — be precise
3. Use ## headers and bullet points to organise your response clearly
4. Cite the source document for key facts: (Source: document_name)
5. If the context does NOT contain sufficient information, respond exactly with:
   “I could not find this information in the available documents. Please upload more relevant files or rephrase your query.”

Do NOT invent, assume, or add information beyond the retrieved context. Accuracy is critical."""


def generate_node(state: AgentState) -> dict:
    """Generate the final answer using the LLM and available context."""
    llm     = _get_llm()
    query   = state["query"]
    mode    = state.get("mode", "general")
    context = state.get("context", "")
    history = state.get("messages", [])

    # Build system prompt
    if mode == "web_search":
        system_content = WEB_SYSTEM_TEMPLATE.format(context=context)
    elif mode == "rag":
        system_content = RAG_SYSTEM_TEMPLATE.format(context=context)
    else:
        system_content = GENERAL_SYSTEM

    # Compose message list: system + last N history turns + current query
    chat_messages: List[BaseMessage] = [SystemMessage(content=system_content)]

    # Include recent conversation history (last 8 messages, excluding current query)
    prior = [m for m in history if not (isinstance(m, HumanMessage) and m.content == query)]
    chat_messages.extend(prior[-8:])
    chat_messages.append(HumanMessage(content=query))

    response = llm.invoke(chat_messages)
    return {"messages": [AIMessage(content=response.content)]}


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def _route(state: AgentState) -> str:
    mode = state.get("mode", "general")
    return {"web_search": "web_search", "rag": "rag_retrieval"}.get(mode, "generate")


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def create_agent_graph(rag_manager: RAGManager):
    """
    Build and compile the LangGraph stateful agent.

    Returns:
        A compiled LangGraph graph ready to be invoked.
    """

    def _classify(state: AgentState) -> dict:
        return classify_node(state, rag_manager)

    def _rag(state: AgentState) -> dict:
        return rag_retrieval_node(state, rag_manager)

    graph = StateGraph(AgentState)

    graph.add_node("classify",      _classify)
    graph.add_node("web_search",    web_search_node)
    graph.add_node("rag_retrieval", _rag)
    graph.add_node("generate",      generate_node)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        _route,
        {
            "web_search":    "web_search",
            "rag_retrieval": "rag_retrieval",
            "generate":      "generate",
        },
    )
    graph.add_edge("web_search",    "generate")
    graph.add_edge("rag_retrieval", "generate")
    graph.add_edge("generate",      END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Public run function
# ---------------------------------------------------------------------------

def run_agent(
    query:          str,
    session_id:     str,
    rag_manager:    RAGManager,
    memory_manager: MemoryManager,
    compiled_graph,
    forced_mode:    str = "",   # "" = auto-detect, else "general"/"web_search"/"rag"
) -> dict:
    """
    Execute one turn of conversation through the agent.

    Args:
        query:          The user's raw input.
        session_id:     Unique identifier for the current chat session.
        rag_manager:    The shared RAGManager instance.
        memory_manager: The shared MemoryManager instance.
        compiled_graph: The compiled LangGraph graph.

    Returns:
        dict with keys: response (str), mode (str), sources (List[str])
    """
    # ---- Load conversation history from SQLite ----
    history      = memory_manager.get_history(session_id, limit=12)
    msg_history: List[BaseMessage] = []
    for msg in history:
        if msg["role"] == "user":
            msg_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            msg_history.append(AIMessage(content=msg["content"]))

    # Add current query
    msg_history.append(HumanMessage(content=query))

    # ---- Build initial state ----
    initial_state = AgentState(
        messages=msg_history,
        query=query,
        mode="general",
        forced_mode=forced_mode,
        context="",
        sources=[],
    )

    # ---- Invoke the graph ----
    result = compiled_graph.invoke(initial_state)

    # ---- Extract AI response ----
    ai_msgs  = [m for m in result["messages"] if isinstance(m, AIMessage)]
    response = ai_msgs[-1].content if ai_msgs else "I was unable to generate a response."

    mode    = result.get("mode",    "general")
    sources = result.get("sources", [])

    # ---- Persist to memory ----
    memory_manager.save_message(session_id, "user",      query,    mode=None, sources=None)
    memory_manager.save_message(session_id, "assistant", response, mode=mode, sources=sources)

    return {"response": response, "mode": mode, "sources": sources}
