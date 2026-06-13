import os
import streamlit as st
import requests

# Page Configuration
st.set_page_config(
    page_title="Universal Memory AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend URL (can be customized via environment variables)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Inject Custom CSS for premium styling (ChatGPT / Claude Dark Theme look)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap');
        
        /* Global Styles */
        html, body, [class*="css"], .stApp {
            background-color: #1e1e1f !important;
            color: #e3e3e3 !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Centered App Container */
        .block-container {
            max-width: 840px !important;
            padding-top: 2.5rem !important;
            padding-bottom: 7.5rem !important;
            margin: 0 auto !important;
        }
        
        /* Header styling */
        h1, h2, h3, h4 {
            font-family: 'Outfit', sans-serif !important;
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        /* Hide Streamlit default branding and menu */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stHeader"] {display: none;}
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #171717 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding: 1.5rem 1rem !important;
        }
        
        /* New Chat Button (matches primary action button styling) */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:nth-child(2) button {
            background: linear-gradient(135deg, #6200ea 0%, #4a00e0 100%) !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            border: none !important;
            border-radius: 24px !important;
            padding: 12px 24px !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            width: 100% !important;
            margin-bottom: 20px !important;
            box-shadow: 0 4px 12px rgba(98, 0, 234, 0.2) !important;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:nth-child(2) button:hover {
            background: linear-gradient(135deg, #7700ff 0%, #5d00ff 100%) !important;
            box-shadow: 0 6px 16px rgba(98, 0, 234, 0.35) !important;
            transform: translateY(-1px) !important;
        }
        
        /* Sidebar List Item Buttons (Thread list) */
        [data-testid="stSidebar"] [data-testid="stButton"] button {
            background-color: transparent !important;
            border: none !important;
            color: #b4b4b4 !important;
            text-align: left !important;
            justify-content: flex-start !important;
            border-radius: 8px !important;
            padding: 10px 14px !important;
            width: 100% !important;
            transition: all 0.2s ease !important;
            font-size: 0.9rem !important;
            font-weight: 400 !important;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] button:hover {
            background-color: rgba(255, 255, 255, 0.06) !important;
            color: #ffffff !important;
        }
        
        /* Active Sidebar Item */
        /* To make active indicator look distinct, we target buttons that have specific symbol or active state */
        [data-testid="stSidebar"] [data-testid="stButton"] button:active,
        [data-testid="stSidebar"] [data-testid="stButton"] button:focus {
            background-color: rgba(255, 255, 255, 0.08) !important;
            color: #ffffff !important;
        }
        
        /* Expanders in Sidebar (Universal Memory drawer) */
        [data-testid="stSidebar"] .streamlit-expanderHeader {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-radius: 10px !important;
            padding: 10px !important;
            font-size: 0.9rem !important;
            color: #bb86fc !important;
        }
        [data-testid="stSidebar"] .streamlit-expanderContent {
            background-color: rgba(255, 255, 255, 0.01) !important;
            border-left: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-bottom-left-radius: 10px !important;
            border-bottom-right-radius: 10px !important;
            padding: 12px !important;
        }
        
        /* Chat Messages */
        [data-testid="stChatMessage"] {
            border-radius: 16px !important;
            padding: 1.25rem 1.5rem !important;
            margin-bottom: 1.25rem !important;
            border: 1px solid rgba(255, 255, 255, 0.04) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
            transition: all 0.2s ease !important;
        }
        
        /* User vs Assistant styling via custom markers */
        [data-testid="stChatMessage"]:has(.user-msg-marker) {
            background-color: #2b2b2f !important;
            border-right: 4px solid #b19ffb !important;
        }
        [data-testid="stChatMessage"]:has(.assistant-msg-marker) {
            background-color: #202023 !important;
            border-left: 4px solid #fc8fa6 !important;
        }
        
        /* Chat Input Styling */
        [data-testid="stBottom"] {
            background-color: #1e1e1f !important;
            border-top: 1px solid rgba(255, 255, 255, 0.05) !important;
        }
        [data-testid="stBottom"] > div {
            background-color: transparent !important;
        }
        [data-testid="stChatInput"] {
            border-radius: 28px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            background-color: #2a2a2b !important;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3) !important;
            max-width: 840px !important;
            margin: 0 auto !important;
        }
        [data-testid="stChatInput"] textarea {
            background-color: transparent !important;
            color: #ffffff !important;
            font-size: 1rem !important;
            padding: 12px 6px !important;
        }
        
        /* suggestion cards styling (only targeting buttons inside columns in main area) */
        div[data-testid="column"] button {
            background-color: #252527 !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            color: #d2d2d7 !important;
            border-radius: 14px !important;
            padding: 22px !important;
            text-align: left !important;
            align-items: center !important;
            justify-content: flex-start !important;
            font-weight: 500 !important;
            font-size: 0.95rem !important;
            min-height: 80px !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            width: 100% !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1) !important;
        }
        div[data-testid="column"] button:hover {
            background-color: #2c2c2f !important;
            border-color: rgba(177, 159, 251, 0.3) !important;
            color: #ffffff !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 18px rgba(177, 159, 251, 0.15) !important;
        }
    </style>
""", unsafe_allow_html=True)

# Session state initialization
if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Fetch active threads
def get_threads():
    try:
        response = requests.get(f"{BACKEND_URL}/threads")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
    return []

# Fetch thread history
def get_thread_history(thread_id):
    try:
        response = requests.get(f"{BACKEND_URL}/thread/{thread_id}")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error fetching thread history: {e}")
    return []

# Fetch latest memory summary
def get_memory_summary():
    try:
        response = requests.get(f"{BACKEND_URL}/memory")
        if response.status_code == 200:
            return response.json().get("summary", "No facts known yet.")
    except Exception:
        pass
    return "No facts known yet."

# Create new thread
def create_new_thread():
    try:
        response = requests.post(f"{BACKEND_URL}/threads")
        if response.status_code == 201:
            thread = response.json()
            st.session_state.current_thread_id = thread["id"]
            st.session_state.messages = []
            return thread["id"]
    except Exception as e:
        st.error(f"Error creating thread: {e}")
    return None

# Fetch active threads
threads = get_threads()

# Auto-initialize session thread if none selected or if list is empty
if st.session_state.current_thread_id is None:
    if threads:
        st.session_state.current_thread_id = threads[0]["id"]
        st.session_state.messages = []
    else:
        new_id = create_new_thread()
        if new_id:
            st.session_state.current_thread_id = new_id
            st.session_state.messages = []
            st.rerun()
        else:
            st.warning("Failed to initialize session. Please verify backend connection.")
            st.stop()

# Sidebar UI
with st.sidebar:
    st.markdown("## 🧠 Universal Memory AI")
    
    if st.button("➕ New Chat"):
        create_new_thread()
        st.rerun()
        
    st.markdown("---")
    
    # Universal Memory Expandable Panel
    with st.expander("🔑 Extracted Facts About You", expanded=True):
        memory_text = get_memory_summary()
        if memory_text and memory_text != "No facts known yet.":
            # Clean rendering of memories/facts
            facts = [f.strip() for f in memory_text.split("\n") if f.strip()]
            for fact in facts:
                clean_fact = fact.lstrip("- *•").strip()
                if clean_fact:
                    st.markdown(f"<div style='font-size: 0.85rem; color: #ececec; margin-bottom: 6px;'>🔹 {clean_fact}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size: 0.82rem; color: #8a8a8f; font-style: italic;'>No facts saved yet. Chat with the assistant, and it will auto-extract facts about you!</div>", unsafe_allow_html=True)
            
    st.markdown("---")
    st.markdown("### 💬 Chat History")
    
    if not threads:
        st.info("No active chats yet. Click 'New Chat' to start.")
    else:
        for t in threads:
            is_current = t["id"] == st.session_state.current_thread_id
            # Distinct labels for active vs inactive
            label = f"🎯  {t['title']}" if is_current else f"💬  {t['title']}"
            
            if st.button(label, key=f"thread_{t['id']}"):
                st.session_state.current_thread_id = t["id"]
                st.session_state.messages = []
                st.rerun()

# Check for active prompt from suggestion clicks
active_prompt = None
if "active_prompt" in st.session_state and st.session_state.active_prompt:
    active_prompt = st.session_state.active_prompt
    del st.session_state.active_prompt

# Synchronize message history from database for the active thread
if not st.session_state.messages and st.session_state.current_thread_id:
    db_messages = get_thread_history(st.session_state.current_thread_id)
    st.session_state.messages = [{"role": msg["role"], "content": msg["content"]} for msg in db_messages]

# Display current message history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # Inject custom user/assistant classes for message bubble styling via :has()
        if msg["role"] == "user":
            st.markdown('<span class="user-msg-marker"></span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="assistant-msg-marker"></span>', unsafe_allow_html=True)
        st.markdown(msg["content"])

# Empty/Welcome state screen if there are no messages
if not st.session_state.messages:
    st.markdown("""
        <div style="text-align: center; margin-top: 50px; margin-bottom: 40px;">
            <h1 style="font-size: 2.8rem; font-weight: 700; background: linear-gradient(135deg, #b19ffb 0%, #fc8fa6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 15px;">
                How can I help you today?
            </h1>
            <p style="color: #a0a0a5; font-size: 1.05rem; max-width: 600px; margin: 0 auto 30px auto; line-height: 1.5;">
                Ask questions, code, plan, or brainstorm! The AI auto-extracts facts about you (e.g. preferences, names, habits) and stores them in long-term memory.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Suggestion grids
    cols = st.columns(2)
    suggestions = [
        ("💡  Brainstorm ideas", "Brainstorm 5 creative ideas for a new application with AI long-term memory."),
        ("📝  Draft a message", "Draft a professional email to my team introducing our new LangGraph chatbot."),
        ("✈️  Plan a trip", "Help me plan a weekend getaway. Remind me what you know about my travel preferences!"),
        ("⚡  Coding helper", "Explain the core concepts of LangGraph StateGraph orchestration with a simple code snippet.")
    ]
    
    for idx, (label, prompt_text) in enumerate(suggestions):
        col_idx = idx % 2
        with cols[col_idx]:
            if st.button(label, key=f"suggest_{idx}"):
                st.session_state.active_prompt = prompt_text
                st.rerun()

# User Chat Input
prompt = st.chat_input("Message Universal Memory AI...")
if active_prompt:
    prompt = active_prompt

# Process prompt
if prompt:
    # Render user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown('<span class="user-msg-marker"></span>', unsafe_allow_html=True)
        st.markdown(prompt)
        
    # Request stream from backend
    with st.chat_message("assistant"):
        st.markdown('<span class="assistant-msg-marker"></span>', unsafe_allow_html=True)
        response_placeholder = st.empty()
        
        # Generator function for streaming response to st.write_stream
        def stream_generator():
            try:
                response = requests.post(
                    f"{BACKEND_URL}/chat/stream",
                    json={"thread_id": st.session_state.current_thread_id, "message": prompt},
                    stream=True
                )
                if response.status_code == 200:
                    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            yield chunk
                else:
                    yield f"Error calling streaming API (Status Code: {response.status_code})"
            except Exception as e:
                yield f"Network Error: {str(e)}"

        # Display streaming response
        full_response = response_placeholder.write_stream(stream_generator())
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Force rerun to update sidebar thread list (especially titles) and memory summary
    st.rerun()
