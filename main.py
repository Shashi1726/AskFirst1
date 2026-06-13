import os
import queue
import threading
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

# Import backend modules
from backend.database import engine, Base, get_db
from backend.models import Thread, Message
from backend.schemas import ThreadCreate, ThreadOut, MessageOut, ChatRequest, ChatResponse
from backend.graph import compiled_graph

# Initialize Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LangGraph Chat App API")

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/threads", response_model=ThreadOut, status_code=201)
def create_thread(db: Session = Depends(get_db)):
    """Creates a new chat thread."""
    try:
        new_thread = Thread(title="New Chat")
        db.add(new_thread)
        db.commit()
        db.refresh(new_thread)
        return new_thread
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create thread: {str(e)}")

@app.get("/threads", response_model=List[ThreadOut])
def get_threads(db: Session = Depends(get_db)):
    """Retrieves all chat threads."""
    try:
        return db.query(Thread).order_by(Thread.created_at.desc()).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get threads: {str(e)}")

@app.get("/thread/{id}", response_model=List[MessageOut])
def get_thread_history(id: int, db: Session = Depends(get_db)):
    """Retrieves message history for a specific thread."""
    # Check if thread exists
    thread = db.query(Thread).filter(Thread.id == id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    try:
        return db.query(Message).filter(Message.thread_id == id).order_by(Message.timestamp.asc()).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch thread history: {str(e)}")

@app.get("/memory")
def get_memory(db: Session = Depends(get_db)):
    """Retrieves the latest long-term memory summary about the user."""
    from backend.models import MemorySummary
    try:
        latest = db.query(MemorySummary).order_by(MemorySummary.created_at.desc()).first()
        return {"summary": latest.summary if latest else "No facts known yet."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch memory summary: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Executes chat graph in blocking mode, returning the final response."""
    # Verify thread exists
    thread = db.query(Thread).filter(Thread.id == request.thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    config = {
        "configurable": {
            "thread_id": str(request.thread_id)
        }
    }
    
    initial_state = {
        "thread_id": request.thread_id,
        "user_message": request.message,
        "thread_history": [],
        "global_memory": [],
        "prompt": "",
        "response": ""
    }
    
    try:
        final_state = compiled_graph.invoke(initial_state, config=config)
        return ChatResponse(response=final_state.get("response", ""))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")

@app.post("/chat/stream")
def chat_stream(request: ChatRequest, db: Session = Depends(get_db)):
    """Executes chat graph in streaming mode, yielding chunks of text in real-time."""
    # Verify thread exists
    thread = db.query(Thread).filter(Thread.id == request.thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    token_queue = queue.Queue()
    
    config = {
        "configurable": {
            "thread_id": str(request.thread_id),
            "token_queue": token_queue
        }
    }
    
    initial_state = {
        "thread_id": request.thread_id,
        "user_message": request.message,
        "thread_history": [],
        "global_memory": [],
        "prompt": "",
        "response": ""
    }
    
    # Run graph in background thread so caller can stream from the queue concurrently
    def run_graph():
        try:
            compiled_graph.invoke(initial_state, config=config)
        except Exception as e:
            # Put error message and end token in queue
            token_queue.put(f"\n[Graph Error: {str(e)}]")
            token_queue.put(None)
            
    thread_worker = threading.Thread(target=run_graph)
    thread_worker.start()
    
    def event_generator():
        while True:
            try:
                # 30 seconds timeout to prevent hanging connections
                token = token_queue.get(timeout=30)
                if token is None:
                    break
                yield token
            except queue.Empty:
                break
                
    return StreamingResponse(event_generator(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
