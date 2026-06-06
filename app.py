import os, uuid, time, tempfile
import concurrent.futures
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="NEXUS AI - Intelligent Multi-Mode Agent",
    page_icon="⚡", layout="wide", initial_sidebar_state="expanded",
)

# Force sidebar ALWAYS open — hide collapse button, lock sidebar open
st.markdown("""
<style>
/* Always show sidebar, never collapse */
[data-testid="stSidebar"] {
    min-width: 320px !important;
    max-width: 320px !important;
    transform: translateX(0) !important;
    visibility: visible !important;
    display: flex !important;
}
/* Hide the collapse arrow button inside sidebar */
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}
/* Hide the expand button (shown when sidebar is closed) */
[data-testid="collapsedControl"] {
    display: none !important;
}
/* Adjust main content so it doesn't overlap */
.main .block-container {
    padding-left: 1rem !important;
}
</style>
""", unsafe_allow_html=True)


if "theme"        not in st.session_state: st.session_state.theme        = "dark"
if "session_id"   not in st.session_state: st.session_state.session_id   = str(uuid.uuid4())[:8]
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "docs_indexed" not in st.session_state: st.session_state.docs_indexed = []
if "sel_mode"     not in st.session_state: st.session_state.sel_mode     = "auto"

IS_DARK = st.session_state.theme == "dark"

if IS_DARK:
    bg="rgba(7,8,26,1)"; bg2="rgba(13,15,38,1)"; sb_bg="rgba(9,10,30,1)"
    stat_bg="rgba(255,255,255,0.04)"; welcome="rgba(255,255,255,0.03)"
    card2="rgba(255,255,255,0.06)"; bdr="rgba(255,255,255,0.07)"; bdr_acc="rgba(99,102,241,0.30)"
    text="#e2e8f0"; text_mid="#94a3b8"; text_mut="#4b5563"
    bot_bub="rgba(255,255,255,0.04)"; bot_bdr="rgba(255,255,255,0.09)"; bot_txt="#e2e8f0"
    inp_bg="rgba(255,255,255,0.05)"; inp_bdr="rgba(99,102,241,0.40)"
    sec="#818cf8"; code_bg="rgba(139,92,246,0.14)"; pre_bg="rgba(0,0,0,0.50)"
else:
    bg="#eef2ff"; bg2="#f5f3ff"; sb_bg="#e0e7ff"
    stat_bg="#ffffff"; welcome="rgba(255,255,255,0.75)"
    card2="rgba(99,102,241,0.07)"; bdr="rgba(99,102,241,0.14)"; bdr_acc="rgba(99,102,241,0.35)"
    text="#1e1b4b"; text_mid="#4338ca"; text_mut="#6b7280"
    bot_bub="#ffffff"; bot_bdr="rgba(99,102,241,0.22)"; bot_txt="#1e1b4b"
    inp_bg="#ffffff"; inp_bdr="rgba(99,102,241,0.45)"
    sec="#4f46e5"; code_bg="rgba(99,102,241,0.10)"; pre_bg="rgba(238,242,255,0.95)"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*,*::before,*::after{box-sizing:border-box}
html,body,[class*="css"]{font-family:'Inter',sans-serif!important}
.stApp{background:linear-gradient(145deg,BG0,BG2 50%,BG0);background-size:400% 400%;animation:bgS 12s ease infinite;min-height:100vh}
@keyframes bgS{0%,100%{background-position:0% 50%}50%{background-position:100% 50%}}
#MainMenu,footer,header{visibility:hidden}
.block-container{padding-top:.6rem!important;padding-bottom:2rem!important;max-width:1200px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,SBBG 0%,BG0 100%)!important;border-right:1px solid BDRA;box-shadow:4px 0 24px rgba(99,102,241,.08)}
[data-testid="collapsedControl"]{background:linear-gradient(135deg,#6366f1,#8b5cf6)!important;border-radius:0 14px 14px 0!important;width:30px!important;height:60px!important;display:flex!important;align-items:center!important;justify-content:center!important;box-shadow:4px 0 18px rgba(99,102,241,.55)!important;border:none!important;top:50%!important;transform:translateY(-50%)!important;transition:all .25s!important;z-index:9999!important}
[data-testid="collapsedControl"]:hover{width:36px!important;box-shadow:4px 0 28px rgba(99,102,241,.75)!important}
[data-testid="collapsedControl"] svg{fill:#fff!important;width:14px!important;height:14px!important}
::-webkit-scrollbar{width:4px;height:4px}::-webkit-scrollbar-thumb{background:linear-gradient(180deg,#6366f1,#8b5cf6);border-radius:4px}::-webkit-scrollbar-track{background:transparent}
.nexus-hdr{background:linear-gradient(135deg,#1e1b4b 0%,#4f46e5 30%,#7c3aed 60%,#0c4a6e 100%);border-radius:20px;padding:1.5rem 2rem;margin-bottom:1rem;box-shadow:0 8px 48px rgba(79,70,229,.35),0 0 0 1px rgba(99,102,241,.20);position:relative;overflow:hidden}
.nexus-hdr::before{content:'';position:absolute;top:-30%;right:-5%;width:280px;height:280px;background:radial-gradient(circle,rgba(167,139,250,.18) 0%,transparent 70%);border-radius:50%;animation:pulse 4s ease-in-out infinite}
.nexus-hdr::after{content:'';position:absolute;bottom:-40%;left:-5%;width:220px;height:220px;background:radial-gradient(circle,rgba(14,165,233,.12) 0%,transparent 70%);border-radius:50%;animation:pulse 4s ease-in-out infinite 2s}
@keyframes pulse{0%,100%{transform:scale(1);opacity:.7}50%{transform:scale(1.1);opacity:1}}
@keyframes glow{from{filter:drop-shadow(0 0 10px rgba(167,139,250,.4))}to{filter:drop-shadow(0 0 25px rgba(167,139,250,.8))}}
.nh{display:flex;align-items:center;gap:1.2rem;position:relative;z-index:1}
.nh-logo{font-size:3rem;animation:glow 2s ease-in-out infinite alternate}
.nh-name{font-size:2rem;font-weight:900;letter-spacing:-1.5px;background:linear-gradient(90deg,#fff 0%,#c4b5fd 50%,#93c5fd 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;line-height:1}
.nh-sub{font-size:.76rem;color:rgba(255,255,255,.72);margin:.25rem 0 0;font-weight:400}
.nh-bdg{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.6rem}
.nb{font-size:.62rem;font-weight:700;padding:3px 10px;border-radius:20px;background:rgba(255,255,255,.13);color:#fff;border:1px solid rgba(255,255,255,.22);letter-spacing:.5px;text-transform:uppercase;backdrop-filter:blur(8px);transition:background .2s}
.nb:hover{background:rgba(255,255,255,.22)}
.stats-row{display:flex;gap:.6rem;margin-bottom:.9rem;flex-wrap:wrap}
.sc{flex:1;min-width:120px;background:STBG;border:1px solid BDR;border-radius:14px;padding:.65rem .9rem;display:flex;align-items:center;gap:.65rem;transition:all .25s;cursor:default;backdrop-filter:blur(10px)}
.sc:hover{border-color:BDRA;transform:translateY(-2px);box-shadow:0 6px 20px rgba(99,102,241,.12)}
.sv{font-size:1.1rem;font-weight:800;color:TXT;line-height:1}
.sl{font-size:.62rem;color:TXTM;text-transform:uppercase;letter-spacing:.6px;margin-top:2px}
.mb{display:inline-block;font-size:.65rem;font-weight:700;padding:2px 10px;border-radius:20px;margin-bottom:4px;letter-spacing:.5px;text-transform:uppercase}
.mg{background:rgba(16,185,129,.15);color:#10b981;border:1px solid rgba(16,185,129,.30)}
.mw{background:rgba(59,130,246,.15);color:#3b82f6;border:1px solid rgba(59,130,246,.30)}
.mr{background:rgba(245,158,11,.15);color:#f59e0b;border:1px solid rgba(245,158,11,.30)}
.stButton>button{background:linear-gradient(135deg,#6366f1,#8b5cf6)!important;color:#fff!important;border:none!important;border-radius:12px!important;font-weight:600!important;font-size:.82rem!important;transition:all .22s!important;box-shadow:0 2px 10px rgba(99,102,241,.20)!important}
.stButton>button:hover{opacity:.90!important;transform:translateY(-2px)!important;box-shadow:0 6px 20px rgba(99,102,241,.35)!important}
.chat-row{display:flex;margin-bottom:1.2rem;animation:slideUp .32s cubic-bezier(.16,1,.3,1)}
.chat-row.ur{justify-content:flex-end}
@keyframes slideUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
.bubble{max-width:76%;padding:.9rem 1.15rem;border-radius:22px;font-size:.9rem;line-height:1.72;word-break:break-word}
.ub{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border-bottom-right-radius:4px;box-shadow:0 4px 20px rgba(99,102,241,.30)}
.bb{background:BOTB;border:1px solid BOTD;color:BOTT;border-bottom-left-radius:4px;backdrop-filter:blur(12px);box-shadow:0 2px 12px rgba(0,0,0,.06)}
.av{width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.85rem;font-weight:700;flex-shrink:0;margin-top:.25rem;color:#fff}
.av-u{background:linear-gradient(135deg,#6366f1,#8b5cf6);margin-left:10px;order:2;box-shadow:0 2px 10px rgba(99,102,241,.30)}
.av-g{background:linear-gradient(135deg,#10b981,#059669);margin-right:10px;box-shadow:0 2px 10px rgba(16,185,129,.25)}
.av-w{background:linear-gradient(135deg,#3b82f6,#1d4ed8);margin-right:10px;box-shadow:0 2px 10px rgba(59,130,246,.25)}
.av-r{background:linear-gradient(135deg,#f59e0b,#b45309);margin-right:10px;box-shadow:0 2px 10px rgba(245,158,11,.25)}
.ptag{font-size:.67rem;color:TXTM;margin-top:.35rem;display:flex;align-items:center;gap:5px}
.pd{width:7px;height:7px;border-radius:50%;display:inline-block}
.pf{background:#10b981;box-shadow:0 0 6px rgba(16,185,129,.5)}
.po{background:#f59e0b;box-shadow:0 0 6px rgba(245,158,11,.5)}
.ps{background:#ef4444;box-shadow:0 0 6px rgba(239,68,68,.5)}
.srcc{background:CARD2;border:1px solid BDRA;border-radius:10px;padding:.5rem .9rem;margin-top:.6rem;font-size:.74rem;color:TXTM}
.srcc b{color:#a78bfa}
[data-testid="stChatInput"]{background:INBG!important;border:1.5px solid INBD!important;border-radius:16px!important;color:TXT!important;font-size:.92rem!important;box-shadow:0 2px 12px rgba(99,102,241,.08)!important}
[data-testid="stChatInput"]:focus-within{border-color:#6366f1!important;box-shadow:0 0 0 3px rgba(99,102,241,.15)!important}
.bb code{background:CDBG;border-radius:5px;padding:1px 6px;font-size:.82em;color:#c4b5fd}
.bb pre{background:PRBG;border-radius:12px;padding:1rem;overflow-x:auto;border:1px solid BDR}
.sbhd{font-size:.63rem;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;color:SEC;margin:1rem 0 .4rem;padding-bottom:.28rem;border-bottom:1px solid BDRA}
.status-ok{display:inline-flex;align-items:center;gap:5px;font-size:.72rem;font-weight:600;padding:3px 12px;border-radius:20px;background:rgba(16,185,129,.12);color:#10b981;border:1px solid rgba(16,185,129,.25)}
.status-err{display:inline-flex;align-items:center;gap:5px;font-size:.72rem;font-weight:600;padding:3px 12px;border-radius:20px;background:rgba(239,68,68,.12);color:#ef4444;border:1px solid rgba(239,68,68,.25)}
[data-testid="stExpander"]{border:1px solid BDRA!important;border-radius:12px!important}
.wc{background:WELC;border:1px solid BDR;border-radius:22px;padding:2rem;text-align:center;margin:1rem 0;backdrop-filter:blur(12px);box-shadow:0 4px 24px rgba(99,102,241,.08)}
.wc h2{color:TXT;font-size:1.25rem;font-weight:800;margin-bottom:.35rem}
.wc p{color:TXTM;font-size:.85rem}
.capgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:.9rem;margin-top:1.2rem}
.cap{background:CARD2;border:1px solid BDR;border-radius:16px;padding:1.1rem;transition:all .22s cubic-bezier(.16,1,.3,1)}
.cap:hover{border-color:BDRA;transform:translateY(-4px);box-shadow:0 8px 28px rgba(99,102,241,.14)}
.cap .ci{font-size:1.8rem;margin-bottom:.35rem}
.cap .ct{font-size:.85rem;font-weight:700;color:TXT}
.cap .cd{font-size:.73rem;color:TXTM;margin-top:.25rem;line-height:1.5}
.chip{border-radius:22px;padding:4px 14px;font-size:.74rem;display:inline-block;margin:3px;font-weight:500;transition:all .18s;cursor:default}
.cg{background:rgba(16,185,129,.11);border:1px solid rgba(16,185,129,.25);color:#10b981}
.cw{background:rgba(59,130,246,.11);border:1px solid rgba(59,130,246,.25);color:#3b82f6}
.cr{background:rgba(245,158,11,.11);border:1px solid rgba(245,158,11,.25);color:#f59e0b}
.chip:hover{transform:scale(1.04)}
</style>
"""

# inject theme values
CSS = (CSS
  .replace("BG0", bg).replace("BG2", bg2).replace("SBBG", sb_bg)
  .replace("STBG", stat_bg).replace("WELC", welcome).replace("CARD2", card2)
  .replace("BDR", bdr).replace("BDRA", bdr_acc)
  .replace("TXT", text).replace("TXTM", text_mut).replace("TXTI", text_mid)
  .replace("BOTB", bot_bub).replace("BOTD", bot_bdr).replace("BOTT", bot_txt)
  .replace("INBG", inp_bg).replace("INBD", inp_bdr)
  .replace("SEC", sec).replace("CDBG", code_bg).replace("PRBG", pre_bg)
)
st.markdown(CSS, unsafe_allow_html=True)

# ── Imports ──────────────────────────────────────────────────────────────────
from rag_manager    import RAGManager
from memory_manager import MemoryManager
from agent          import create_agent_graph, run_agent

@st.cache_resource(show_spinner="Loading AI models...")
def get_rag_manager():
    rm = RAGManager()
    docs_dir = "documents"
    if os.path.isdir(docs_dir):
        for fn in os.listdir(docs_dir):
            fp = os.path.join(docs_dir, fn)
            if os.path.isfile(fp) and fn.lower().endswith((".txt",".pdf",".md")):
                rm.add_documents(fp, fn)
    return rm

@st.cache_resource(show_spinner=False)
def get_memory_manager(): return MemoryManager()

@st.cache_resource(show_spinner="Compiling agent graph...")
def get_agent_graph(_rag): return create_agent_graph(_rag)

rag_manager    = get_rag_manager()
memory_manager = get_memory_manager()
agent_graph    = get_agent_graph(rag_manager)

def safe_run(query, sid, rag, mem, graph, forced, timeout=15):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        f = ex.submit(run_agent, query, sid, rag, mem, graph, forced)
        try:   return f.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return {"response":"Request timed out. Please try again.","mode":"general","sources":[]}
        except Exception as e:
            return {"response":"Error: " + str(e)[:200],"mode":"general","sources":[]}

def load_session(sid):
    msgs = memory_manager.get_history(sid, limit=100)
    st.session_state.chat_history = [
        {"role":m["role"],"content":m["content"],
         "mode":m.get("mode","general") if m["role"]=="assistant" else None,
         "sources":m.get("sources",[]),"elapsed":None}
        for m in msgs
    ]
    st.session_state.session_id = sid

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding:.6rem 0 .2rem">
      <div style="font-size:2.2rem">⚡</div>
      <div style="font-size:1.55rem;font-weight:900;letter-spacing:-1px;
        background:linear-gradient(90deg,#818cf8,#c4b5fd);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">
        NEXUS AI</div>
      <div style="font-size:.65rem;color:{sec};font-weight:700;letter-spacing:.9px">INTELLIGENT MULTI-MODE AGENT</div>
      <div style="font-size:.6rem;color:{text_mut};margin-top:.2rem">NEOSTATS Innovation Sprint 2026</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    st.markdown('<div class="sbhd">Appearance</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🌙 Dark",  use_container_width=True, key="dk"):
            st.session_state.theme = "dark";  st.rerun()
    with c2:
        if st.button("☀️ Light", use_container_width=True, key="lt"):
            st.session_state.theme = "light"; st.rerun()
    st.markdown(f'<div style="text-align:center;font-size:.68rem;color:{sec};margin-top:.15rem">{"🌙 Dark" if IS_DARK else "☀️ Light"} Mode active</div>', unsafe_allow_html=True)
    st.divider()

    api_ok = bool(os.environ.get("GROQ_API_KEY",""))
    st.markdown('<div class="sbhd">API Status</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="{"status-ok" if api_ok else "status-err"}">{"● Connected" if api_ok else "● Not Connected"}</div>', unsafe_allow_html=True)
    with st.expander("⚙️ Configure API Key", expanded=not api_ok):
        ki = st.text_input("Key","",type="password",placeholder="gsk_...",label_visibility="collapsed",key="ki")
        if ki:
            os.environ["GROQ_API_KEY"] = ki; st.success("Key saved!")
        st.markdown(f'<div style="font-size:.68rem;color:{text_mut}">Free key at console.groq.com</div>', unsafe_allow_html=True)
    st.divider()

    st.markdown('<div class="sbhd">💬 Chat History</div>', unsafe_allow_html=True)
    try:    previews = memory_manager.get_session_previews()
    except: previews = []
    if not previews:
        st.markdown(f'<div style="font-size:.74rem;color:{text_mut}">No previous conversations yet.</div>', unsafe_allow_html=True)
    else:
        for p in previews:
            active = p["session_id"] == st.session_state.session_id
            lbl = ("▶ " if active else "") + p["title"]
            if st.button(lbl, key="h_"+p["session_id"], use_container_width=True,
                         help=str(p["total_msgs"])+" msgs · "+p["last_active"]):
                load_session(p["session_id"]); st.rerun()
    if st.button("✨ New Conversation", use_container_width=True, key="nc"):
        st.session_state.session_id   = str(uuid.uuid4())[:8]
        st.session_state.chat_history = []
        st.session_state.docs_indexed = []
        st.rerun()
    st.divider()

    st.markdown('<div class="sbhd">📄 Upload Documents (RAG)</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("docs", type=["txt","pdf"], accept_multiple_files=True, label_visibility="collapsed")
    if uploaded:
        for f in uploaded:
            if f.name not in st.session_state.docs_indexed:
                with st.spinner("Indexing "+f.name+"..."):
                    sfx = "."+f.name.rsplit(".",1)[-1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=sfx) as tmp:
                        tmp.write(f.read()); tp = tmp.name
                    ok = rag_manager.add_documents(tp, f.name)
                    try: os.unlink(tp)
                    except: pass
                    if ok: st.session_state.docs_indexed.append(f.name); st.success(f.name+" indexed!")
                    else:  st.error("Failed: "+f.name)

    all_docs = rag_manager.get_loaded_documents() or st.session_state.docs_indexed
    if all_docs:
        st.markdown(f'<div class="sbhd">📚 Knowledge Base ({len(all_docs)} docs)</div>', unsafe_allow_html=True)
        for d in all_docs:
            st.markdown(f'<div style="font-size:.74rem;color:{text_mid};padding:2px 0">📄 {d}</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="sbhd">⚡ SLA Targets</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:.7rem;line-height:2;color:{text_mut}">LLM &lt; 5s | RAG &lt; 1s | Web &lt; 3s<br>Session-isolated | Fallbacks active</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown(f'<div style="font-size:.63rem;color:{text_mut};text-align:center">Christ (Deemed to be University)<br>Dept. of Computer Science · MCA</div>', unsafe_allow_html=True)

# ── Force sidebar open via JS ────────────────────────────────────────────────
st.markdown("""
<script>
// Force sidebar open if it is collapsed
window.addEventListener('load', function() {
    setTimeout(function() {
        var btn = document.querySelector('[data-testid="collapsedControl"]');
        if (btn) btn.click();
    }, 400);
});
</script>
""", unsafe_allow_html=True)

# ── MAIN ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="nexus-hdr">
 <div class="nh">
  <div class="nh-logo">⚡</div>
  <div>
   <div class="nh-name">NEXUS AI</div>
   <div class="nh-sub">Intelligent Multi-Mode Conversational AI Agent &nbsp;·&nbsp; NEOSTATS Innovation Sprint 2026</div>
   <div class="nh-bdg">
    <span class="nb">General Chat</span>
    <span class="nb">Web Search</span>
    <span class="nb">RAG Retrieval</span>
    <span class="nb">Memory</span>
    <span class="nb">Secure</span>
    <span class="nb">LangGraph</span>
   </div>
  </div>
 </div>
</div>""", unsafe_allow_html=True)

# ── API Key banner (shown on main page when not configured) ───────────────────
if not os.environ.get("GROQ_API_KEY"):
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(239,68,68,0.12),rgba(245,158,11,0.10));
        border:1.5px solid rgba(239,68,68,0.35);border-radius:16px;padding:1.1rem 1.4rem;
        margin-bottom:1rem;display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
      <div style="font-size:1.6rem">🔑</div>
      <div style="flex:1;min-width:200px">
        <div style="font-size:.9rem;font-weight:700;color:#f87171;margin-bottom:.2rem">Groq API Key Required</div>
        <div style="font-size:.78rem;color:{text_mut}">Enter your key below to start chatting. Get a free key at
          <b style="color:#818cf8">console.groq.com</b></div>
      </div>
    </div>""", unsafe_allow_html=True)
    col1, col2 = st.columns([4,1])
    with col1:
        new_key = st.text_input("Groq API Key", placeholder="gsk_...", type="password",
                                 label_visibility="collapsed", key="main_key_input")
    with col2:
        if st.button("✅ Save Key", use_container_width=True, key="save_key"):
            if new_key:
                os.environ["GROQ_API_KEY"] = new_key
                st.success("Key saved! Reloading...")
                st.rerun()
    if new_key:
        os.environ["GROQ_API_KEY"] = new_key
    st.divider()

# Stats
n_g = sum(1 for m in st.session_state.chat_history if m.get("mode")=="general"    and m["role"]=="assistant")
n_w = sum(1 for m in st.session_state.chat_history if m.get("mode")=="web_search" and m["role"]=="assistant")
n_r = sum(1 for m in st.session_state.chat_history if m.get("mode")=="rag"        and m["role"]=="assistant")
n_t = len([m for m in st.session_state.chat_history if m["role"]=="assistant"])
times = [m["elapsed"] for m in st.session_state.chat_history if m.get("elapsed")]
avg_t = str(round(sum(times)/len(times),1))+"s" if times else "--"

st.markdown(f"""
<div class="stats-row">
 <div class="sc"><div style="font-size:1.3rem">💬</div><div><div class="sv">{n_t}</div><div class="sl">Total</div></div></div>
 <div class="sc"><div style="font-size:1.3rem">🤖</div><div><div class="sv">{n_g}</div><div class="sl">General</div></div></div>
 <div class="sc"><div style="font-size:1.3rem">🌐</div><div><div class="sv">{n_w}</div><div class="sl">Web</div></div></div>
 <div class="sc"><div style="font-size:1.3rem">📚</div><div><div class="sv">{n_r}</div><div class="sl">RAG</div></div></div>
 <div class="sc"><div style="font-size:1.3rem">⚡</div><div><div class="sv">{avg_t}</div><div class="sl">Avg Time</div></div></div>
</div>""", unsafe_allow_html=True)

# Mode selector
st.markdown(f'<div style="font-size:.72rem;font-weight:700;color:{text_mut};text-transform:uppercase;letter-spacing:.8px;margin-bottom:.4rem">Select Mode:</div>', unsafe_allow_html=True)
modes = {"auto":"🧠 Auto","general":"💬 General","web_search":"🌐 Web Search","rag":"📚 RAG"}
cols = st.columns(len(modes))
for i,(key,label) in enumerate(modes.items()):
    with cols[i]:
        active = st.session_state.sel_mode == key
        btn_label = ("✅ " if active else "") + label
        if st.button(btn_label, key="mode_"+key, use_container_width=True):
            st.session_state.sel_mode = key; st.rerun()

hints = {
    "auto":       "🧠 Agent auto-detects the best mode for each query",
    "general":    "💬 Fast direct LLM — no classification overhead",
    "web_search": "🌐 Fast real-time web search via DuckDuckGo",
    "rag":        "📚 Fast document retrieval from your knowledge base",
}
st.markdown(f'<div style="font-size:.72rem;color:{text_mut};margin-bottom:.7rem">{hints[st.session_state.sel_mode]}</div>', unsafe_allow_html=True)

# ── Chat render ──────────────────────────────────────────────────────────────
def render_msg(role, content, mode="general", sources=None, elapsed=None):
    if role == "user":
        st.markdown(f'<div class="chat-row ur"><div class="bubble ub">{content}</div><div class="av av-u">U</div></div>', unsafe_allow_html=True)
        return
    meta = {
        "general":    ("General Chat",  "mb mg","av-g","G"),
        "web_search": ("Web Search",    "mb mw","av-w","W"),
        "rag":        ("RAG Retrieval", "mb mr","av-r","R"),
    }
    lbl, bdg, avc, icon = meta.get(mode, meta["general"])
    body = content.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
    src = ""
    if sources:
        src = '<div class="srcc">Source: '+" | ".join(f"<b>{s}</b>" for s in sources)+"</div>"
    perf = ""
    if elapsed is not None:
        dc = "pf" if elapsed < 3 else ("po" if elapsed < 6 else "ps")
        perf = f'<div class="ptag"><span class="pd {dc}"></span>{elapsed:.1f}s response time</div>'
    st.markdown(f"""<div class="chat-row">
      <div class="av {avc}">{icon}</div>
      <div style="max-width:78%">
        <span class="{bdg}">{lbl}</span>
        <div class="bubble bb">{body}{src}</div>{perf}
      </div></div>""", unsafe_allow_html=True)

# ── Welcome or chat ──────────────────────────────────────────────────────────
if not st.session_state.chat_history:
    st.markdown(f"""
    <div class="wc">
      <h2>👋 Welcome to NEXUS AI</h2>
      <p>Intelligent Multi-Mode Conversational AI — powered by LangGraph, Groq LLM and FAISS</p>
      <div class="capgrid">
        <div class="cap"><div class="ci">🤖</div><div class="ct">General Chat</div>
          <div style="margin:.25rem 0"><span class="mb mg">General</span></div>
          <div class="cd">AI knowledge, coding, math &amp; science</div></div>
        <div class="cap"><div class="ci">🌐</div><div class="ct">Web Search</div>
          <div style="margin:.25rem 0"><span class="mb mw">Web Search</span></div>
          <div class="cd">Real-time news, prices &amp; events via DuckDuckGo</div></div>
        <div class="cap"><div class="ci">📚</div><div class="ct">RAG Retrieval</div>
          <div style="margin:.25rem 0"><span class="mb mr">RAG</span></div>
          <div class="cd">Enterprise docs, HR policies &amp; uploaded manuals</div></div>
      </div>
    </div>
    <div style="text-align:center;margin-top:.8rem">
      <div style="font-size:.74rem;color:{text_mut};margin-bottom:.5rem">✨ Try these example queries:</div>
      <span class="chip cg">What is LangGraph?</span>
      <span class="chip cg">Write a Python quicksort</span>
      <span class="chip cw">Latest AI news today</span>
      <span class="chip cw">Current BTC price</span>
      <span class="chip cr">What is the leave policy?</span>
      <span class="chip cr">Explain onboarding process</span>
    </div>""", unsafe_allow_html=True)
else:
    for m in st.session_state.chat_history:
        render_msg(m["role"], m["content"], m.get("mode","general"), m.get("sources",[]), m.get("elapsed"))

# ── Input ────────────────────────────────────────────────────────────────────
user_query = st.chat_input("Ask NEXUS AI anything...")
if user_query:
    if not os.environ.get("GROQ_API_KEY"):
        st.error("Please configure your Groq API Key in the sidebar first.")
        st.stop()
    st.session_state.chat_history.append({"role":"user","content":user_query,"mode":None,"sources":[],"elapsed":None})
    forced = "" if st.session_state.sel_mode == "auto" else st.session_state.sel_mode
    with st.spinner("NEXUS AI is thinking..."):
        t0  = time.time()
        res = safe_run(user_query, st.session_state.session_id, rag_manager, memory_manager, agent_graph, forced)
        elapsed = round(time.time()-t0, 2)
    st.session_state.chat_history.append({
        "role":"assistant","content":res["response"],
        "mode":res["mode"],"sources":res["sources"],"elapsed":elapsed,
    })
    st.rerun()