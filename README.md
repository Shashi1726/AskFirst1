# LangGraph Universal Memory Chat Application

A production-ready AI chatbot application built using LangGraph (StateGraph), FastAPI, SQLite, SQLAlchemy, and Streamlit, featuring long-term Universal Memory across multiple threads and real-time streaming support.

## Project Structure

```
├── backend/
│   ├── main.py            # FastAPI App & Endpoints
│   ├── database.py        # SQLAlchemy engine and session configuration
│   ├── models.py          # Database Models (Thread, Message, MemorySummary)
│   ├── schemas.py         # Pydantic Schemas
│   ├── graph.py           # LangGraph StateGraph structure and compilation
│   ├── state.py           # LangGraph ChatState (TypedDict) definition
│   ├── nodes.py           # Graph Node definitions
│   └── gemini_client.py   # Gemini API Client using the new google-genai SDK
├── frontend/
│   └── app.py             # Streamlit UI
├── requirements.txt       # Project dependencies
├── .env.example           # Template for environment variables
└── README.md              # Documentation and execution instructions
```

## Features

1. **Multiple Chat Threads**: Users can create, switch between, and view thread histories.
2. **Persistent Message Store**: All interactions are stored in a local SQLite database using SQLAlchemy.
3. **Universal Memory**: The AI remembers user details (name, preferences, habits) across different chat threads. This is done by extracting facts during interactions, maintaining a unified list in the database (`memory_summaries` table), and injects them dynamically.
4. **Token-Level Streaming**: Fully integrated with Gemini streaming to stream answers token-by-token back to the Streamlit frontend.
5. **Auto Thread Naming**: The application automatically generates a relevant title for a thread from the first user message.
6. **LangGraph StateGraph Checkpointing**: Built-in state recovery and orchestration using a LangGraph `MemorySaver` checkpointer.

---

## Setup Instructions

### 1. Prerequisites
- Python 3.10 or higher installed.
- `uv` package installer (recommended) or `pip`.

### 2. Environment Configuration
Create a `.env` file in the root workspace directory from the `.env.example` file:
```bash
cp .env.example .env
```
Open the `.env` file and insert your Gemini API Key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000
DATABASE_URL=sqlite:///./chat_app.db
```

### 3. Installation
Using `uv`, initialize the virtual environment and install the required dependencies:
```bash
uv venv
uv pip install -r requirements.txt
```

---

## Running the Application

Ensure the virtual environment is activated, or run python modules directly.

### Step 1: Start the Backend Server (FastAPI)
From the root project directory, run:
```bash
.venv\Scripts\python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
The FastAPI documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### Step 2: Start the Frontend Application (Streamlit)
In a separate terminal, run:
```bash
.venv\Scripts\streamlit run frontend/app.py
```
The Streamlit interface will automatically open in your browser, typically at [http://localhost:8501](http://localhost:8501).

---

## Architecture Flow

The LangGraph Orchestration State Graph workflow flows as follows:

```
[START]
   │
   ▼
[load_thread_history] (Loads database history for the thread)
   │
   ▼
[load_global_memory]  (Retrieves the consolidated user fact summary)
   │
   ▼
[build_prompt]        (Assembles memory + history + user message)
   │
   ▼
[call_gemini]         (Invokes Gemini API and streams tokens to a thread queue)
   │
   ▼
[save_messages]       (Persists the new messages, auto-names if first message, updates memory summary)
   │
   ▼
[END]
```
"# AskFirst1" 
