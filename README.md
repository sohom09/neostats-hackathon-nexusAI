# ⚡ NEXUS AI — Intelligent Multi-Mode Conversational AI Agent

<div align="center">

![NEXUS AI Banner](https://img.shields.io/badge/NEXUS%20AI-Intelligent%20Agent-6366f1?style=for-the-badge&logo=lightning&logoColor=white)

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-Latest-1C3C3C?style=flat-square&logo=chainlink&logoColor=white)](https://langchain.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Stateful%20Agent-7C3AED?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-llama--3.1--8b--instant-F55036?style=flat-square)](https://groq.com)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20DB-009688?style=flat-square)](https://faiss.ai)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**A production-grade, enterprise-ready conversational AI agent with automatic multi-mode routing, persistent memory, real-time web search, and RAG-based document intelligence.**

*Built for NEOSTATS Innovation Sprint 2026 · Christ (Deemed to be University)*

[🚀 Quick Start](#-quick-start) · [🧠 Architecture](#-architecture) · [✨ Features](#-features) · [📸 Demo](#-demo)

</div>

---

## 🎯 What is NEXUS AI?

NEXUS AI is an **Intelligent Multi-Mode Conversational AI Agent** that automatically selects the best approach to answer your query:

| Mode | Description | Use Case |
|------|-------------|----------|
| 🤖 **General Chat** | Direct LLM reasoning | Coding, math, explanations, creative writing |
| 🌐 **Web Search** | Real-time DuckDuckGo + LLM synthesis | News, prices, current events |
| 📚 **RAG Retrieval** | FAISS vector search + LLM grounding | Company policies, uploaded documents |

The agent **intelligently routes** each query to the right tool — no unnecessary API calls, no hallucination from stale data.

---

## ✨ Features

### 🧠 Intelligence
- **Auto-routing** via LLM intent classifier — picks the right mode automatically
- **Forced modes** — users can bypass classification for faster, predictable responses
- **Graceful fallbacks** — RAG with no docs → auto-falls back to General Chat
- **15-second timeout** with friendly error message (no hanging)

### 💾 Memory & Persistence
- **SQLite-based conversation memory** — persistent across browser refreshes
- **Session isolation** — each conversation has a unique `session_id`
- **12-turn context window** — accurate multi-turn follow-up responses
- **Chat history sidebar** — browse and resume past conversations

### 📄 Document Intelligence (RAG)
- Upload **PDF** and **TXT** files directly from the UI
- Chunked with `RecursiveCharacterTextSplitter` (256 chars, 20 overlap)
- Embedded with `BAAI/bge-small-en-v1.5` (local CPU, no cloud embedding costs)
- Stored in **FAISS** vector index (persisted to disk)
- Top-4 semantically relevant chunks retrieved per query
- Source citations shown with every RAG response

### 🎨 User Interface
- **Dark / Light mode** toggle
- **Live performance metrics** — response time, per-mode stats
- **Color-coded mode badges** — instantly see which tool answered
- **Animated header** with gradient and glow effects
- **Glassmorphism UI** with Inter font
- **Secure API key** input (hidden, never displayed)

### ⚡ Performance
| Metric | Target | Implementation |
|--------|--------|----------------|
| LLM Response | < 5 seconds | Groq ultra-fast inference |
| RAG Retrieval | < 1 second | FAISS similarity search |
| Web Search | < 3 seconds | DuckDuckGo lightweight API |
| Model Load | Instant (after first run) | `@st.cache_resource` |

---

## 🧠 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        NEXUS AI System                          │
│                                                                 │
│   ┌──────────────┐     ┌────────────────────────────────────┐  │
│   │   app.py     │────▶│           agent.py                 │  │
│   │  Streamlit   │     │         LangGraph DAG              │  │
│   │  UI + CSS    │     │                                    │  │
│   └──────────────┘     │  START → classify_node             │  │
│                        │         ↓ (conditional route)       │  │
│   ┌──────────────┐     │  ┌──────┴──────────────────────┐  │  │
│   │rag_manager   │◀────│  │  general │ web_search │ rag  │  │  │
│   │    .py       │     │  └──────────┴─────────┬────┘    │  │  │
│   │ FAISS Index  │     │                        ↓          │  │
│   │ bge-small    │     │              generate_node         │  │
│   └──────────────┘     │                   ↓ END            │  │
│                        └────────────────────────────────────┘  │
│   ┌──────────────┐                                             │
│   │memory_manager│     ┌──────────┐    ┌──────────────────┐   │
│   │    .py       │     │  SQLite  │    │   Groq LLM API   │   │
│   │ Conversation │────▶│  Memory  │    │ llama-3.1-8b-    │   │
│   │   History    │     │   DB     │    │    instant       │   │
│   └──────────────┘     └──────────┘    └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### LangGraph Flow

```
User Query
    │
    ▼
[classify_node] ──── forced_mode set? ──▶ skip LLM, use forced mode
    │ (LLM classifies intent)
    │
    ├──▶ "general"    ──▶ [generate_node] ──▶ Response
    ├──▶ "web_search" ──▶ [web_search_node] ──▶ [generate_node] ──▶ Response
    └──▶ "rag"        ──▶ [rag_retrieval_node] ──▶ [generate_node] ──▶ Response
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Groq API → `llama-3.1-8b-instant` |
| **Agent Orchestration** | LangGraph (stateful DAG) |
| **Web Search** | DuckDuckGo (`langchain_community`) |
| **Vector Database** | FAISS (Facebook AI Similarity Search) |
| **Embedding Model** | `BAAI/bge-small-en-v1.5` (HuggingFace, local) |
| **Conversation Memory** | SQLite (`sqlite3`) |
| **Document Loaders** | LangChain `PyPDFLoader`, `TextLoader` |
| **Text Chunking** | `RecursiveCharacterTextSplitter` |
| **Frontend** | Streamlit + Vanilla CSS |
| **Language** | Python 3.11 |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Free Groq API key → [console.groq.com](https://console.groq.com)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/nexus-ai.git
cd nexus-ai

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key
echo GROQ_API_KEY=your_key_here > .env

# 5. Run the app
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## 📦 Project Structure

```
nexus-ai/
├── app.py              # Streamlit UI — frontend, mode selector, chat rendering
├── agent.py            # LangGraph agent — classify, web search, RAG, generate nodes
├── rag_manager.py      # FAISS vector store — document indexing & semantic search
├── memory_manager.py   # SQLite memory — persistent conversation history
├── requirements.txt    # Python dependencies
├── .env                # API keys (not committed)
├── .gitignore          # Excludes .env, faiss_index/, __pycache__/
├── faiss_index/        # Auto-created — persisted FAISS vector index
└── documents/          # Optional — pre-load documents here on startup
```

---

## 🔧 Configuration

### Environment Variables (`.env`)
```env
GROQ_API_KEY=gsk_your_key_here
```

### Supported Document Formats
- **PDF** — `.pdf`
- **Plain Text** — `.txt`, `.md`

---

## 📋 Requirements

```txt
streamlit
langchain
langchain-groq
langchain-community
langchain-huggingface
langchain-text-splitters
langchain-core
langgraph
faiss-cpu
sentence-transformers
transformers==4.44.2
python-dotenv
pypdf
duckduckgo-search
markdown
```

---

## 🎮 Usage Guide

### 1. Configure API Key
Enter your Groq API key in the sidebar under **Configure API Key**.

### 2. Select Mode
| Button | When to use |
|--------|-------------|
| 🧠 **Auto** | Let the agent decide (default) |
| 💬 **General** | Fast — coding, knowledge, explanations |
| 🌐 **Web Search** | Real-time info — news, prices, events |
| 📚 **RAG** | Ask questions about your uploaded documents |

### 3. Upload Documents (RAG)
Click **Upload Documents** in the sidebar → upload `.pdf` or `.txt` files → the agent automatically indexes them into FAISS.

### 4. Chat
Type in the chat box and press Enter. Each response shows:
- Mode badge (General / Web Search / RAG)
- Source citations (for Web & RAG)
- Response time indicator (green < 3s, yellow < 6s, red > 6s)

---

## 🏆 Evaluation Rubric Compliance

| Criterion | Status | Implementation |
|-----------|--------|----------------|
| All 3 modes implemented | ✅ | `agent.py` — 3 LangGraph nodes |
| Intelligent tool routing | ✅ | LLM classify + conditional edges |
| No unnecessary tool calls | ✅ | Each mode calls only its tool |
| Accurate follow-up responses | ✅ | SQLite memory, 12-turn context |
| Relevant document retrieval | ✅ | FAISS top-4 semantic search |
| Quality Streamlit UI | ✅ | Dark/light, animations, stats |
| Modularity | ✅ | 4 files, single responsibility each |
| Scalability | ✅ | FAISS + cache_resource + timeouts |
| Maintainability | ✅ | Type hints, docstrings, clean code |

---

## 👥 Team

**Christ (Deemed to be University), Bangalore**
Department of Computer Science — MCA Program
NEOSTATS Innovation Sprint 2026

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ using LangGraph · Groq · FAISS · Streamlit**

⚡ *NEXUS AI — Where Intelligence Meets Efficiency*

</div>
