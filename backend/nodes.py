from langchain_core.runnables import RunnableConfig
from backend.database import SessionLocal
from backend.models import Thread, Message, MemorySummary
from backend.state import ChatState
from backend.gemini_client import generate_text, generate_text_stream, generate_text_with_retry

def load_thread_history(state: ChatState) -> dict:
    """Fetches the message history of the current thread from SQLite."""
    thread_id = state.get("thread_id")
    db = SessionLocal()
    try:
        messages = (
            db.query(Message)
            .filter(Message.thread_id == thread_id)
            .order_by(Message.timestamp.asc())
            .all()
        )
        history = [{"role": msg.role, "content": msg.content} for msg in messages]
        return {"thread_history": history}
    except Exception as e:
        # Graceful fallback on DB errors
        print(f"Error loading thread history: {e}")
        return {"thread_history": []}
    finally:
        db.close()

def load_global_memory(state: ChatState) -> dict:
    """Fetches global memory summary. If empty, extracts facts from all threads."""
    db = SessionLocal()
    try:
        # Load the latest summary record
        latest_summary = db.query(MemorySummary).order_by(MemorySummary.created_at.desc()).first()
        if latest_summary:
            global_memory = [latest_summary.summary]
        else:
            # Fallback: Extract from all messages across all threads if no summary exists
            messages = db.query(Message).order_by(Message.timestamp.asc()).all()
            if messages:
                formatted_chats = "\n".join([f"{m.role}: {m.content}" for m in messages])
                prompt = (
                    "You are a memory extractor. Analyze the following chat history across multiple threads "
                    "and extract key long-term facts about the user (e.g. user's name, preferences, interests, "
                    "or facts mentioned). Write them as a concise bulleted list. Return ONLY the bullet points, "
                    "with no conversational intro or outro.\n\n"
                    f"Chat History:\n{formatted_chats}"
                )
                summary_text = generate_text_with_retry(prompt)
                if summary_text.strip():
                    new_summary = MemorySummary(summary=summary_text.strip())
                    db.add(new_summary)
                    db.commit()
                    global_memory = [summary_text.strip()]
                else:
                    global_memory = []
            else:
                global_memory = []
        return {"global_memory": global_memory}
    except Exception as e:
        print(f"Error loading global memory: {e}")
        return {"global_memory": []}
    finally:
        db.close()

def build_prompt(state: ChatState) -> dict:
    """Combines global memory context, thread history, and user input into a single prompt."""
    global_memory = state.get("global_memory", [])
    thread_history = state.get("thread_history", [])
    user_message = state.get("user_message", "")

    memory_context = "\n".join(global_memory) if global_memory else "No facts learned about the user yet."

    history_context = ""
    for msg in thread_history:
        role_label = "User" if msg["role"] == "user" else "Assistant"
        history_context += f"{role_label}: {msg['content']}\n"

    prompt = (
        "You are a helpful and intelligent AI Chatbot. You must follow these instructions:\n"
        "1. Respond to the User's latest message.\n"
        "2. Use the provided Long-Term Memory context about the user to personalize the response (e.g., refer to their name, preferences, or details they shared previously if relevant).\n"
        "3. Maintain context from the current thread history.\n\n"
        f"=== Long-Term Memory (Facts about User) ===\n{memory_context}\n\n"
        f"=== Current Thread History ===\n{history_context}\n"
        f"User: {user_message}\n"
        "Assistant:"
    )
    return {"prompt": prompt}

def call_gemini(state: ChatState, config: RunnableConfig) -> dict:
    """Calls Gemini API, supporting streaming output via a token queue if provided in config."""
    prompt = state.get("prompt")
    token_queue = config.get("configurable", {}).get("token_queue")

    if token_queue is not None:
        full_response = ""
        try:
            for chunk in generate_text_stream(prompt):
                token_queue.put(chunk)
                full_response += chunk
        except Exception as e:
            token_queue.put(f"\n[Error: {str(e)}]")
            raise e
        finally:
            # Signal end of stream
            token_queue.put(None)
        return {"response": full_response}
    else:
        response = generate_text_with_retry(prompt)
        return {"response": response}

def save_messages(state: ChatState) -> dict:
    """Saves user message, AI response, auto-names threads, and updates memory summaries."""
    thread_id = state.get("thread_id")
    user_msg = state.get("user_message")
    ai_res = state.get("response")

    db = SessionLocal()
    try:
        # 1. Save User Message
        user_message_db = Message(thread_id=thread_id, role="user", content=user_msg)
        db.add(user_message_db)

        # 2. Save Assistant Response
        assistant_message_db = Message(thread_id=thread_id, role="assistant", content=ai_res)
        db.add(assistant_message_db)
        db.commit()

        # 3. Auto-naming the Thread if it's still default
        message_count = db.query(Message).filter(Message.thread_id == thread_id).count()
        thread_obj = db.query(Thread).filter(Thread.id == thread_id).first()
        if thread_obj and thread_obj.title == "New Chat":
            title_prompt = (
                "You are a thread naming tool. Read the following user message and generate a short, "
                "concise thread title of 3 to 5 words max. Return ONLY the raw title. Do NOT explain your thinking, "
                "do NOT show any thinking process, do NOT include any thinking tags, and do NOT include quotes, markdown, or any prefix/suffix.\n\n"
                f"User Message: {user_msg}"
            )
            try:
                generated_title = generate_text_with_retry(title_prompt).strip()
                if generated_title:
                    generated_title = generated_title.strip('"\'')
                    thread_obj.title = generated_title
                    db.commit()
            except Exception as e:
                print(f"Failed to auto-name thread: {e}")

        # 4. Long-Term Memory Summary updates (Optimized to prevent 429 rate limits)
        latest_summary = db.query(MemorySummary).order_by(MemorySummary.created_at.desc()).first()
        existing_summary_text = latest_summary.summary if latest_summary else "No facts known yet."

        trigger_words = [
            "name", "like", "love", "hate", "prefer", "live", "work", 
            "job", "born", "interest", "hobby", "remember", "cold", 
            "sick", "allergy", "allergies", "food", "want", "need", "call me"
        ]
        has_trigger = any(word in user_msg.lower() for word in trigger_words)
        
        # Consolidation trigger: keyword match OR every 3 complete user-assistant turns (6 messages)
        should_update_memory = has_trigger or (message_count % 6 == 0)

        if should_update_memory:
            memory_update_prompt = (
                "You are a memory consolidation engine. Your task is to update a summary of facts about the user.\n"
                f"Existing Memory Summary:\n{existing_summary_text}\n\n"
                "New Conversation Turn:\n"
                f"User: {user_msg}\n"
                f"Assistant: {ai_res}\n\n"
                "Instructions:\n"
                "- Merge the new conversation details into the existing facts summary.\n"
                "- Extract new facts (e.g. name, preferences, hobbies, job, important details mentioned).\n"
                "- Resolve any contradictions (if the user corrected a previous preference, update it).\n"
                "- Keep the output as a clean, bulleted list of facts. Keep it concise.\n"
                "- If no new facts are learned and the existing facts remain accurate, output the existing facts unchanged.\n"
                "- Output ONLY the bullet points. Do not include any greeting, explanation, or conversational text.\n"
            )
            try:
                updated_summary_text = generate_text_with_retry(memory_update_prompt).strip()
                if updated_summary_text and updated_summary_text != "No facts known yet.":
                    new_summary_db = MemorySummary(summary=updated_summary_text)
                    db.add(new_summary_db)
                    db.commit()
            except Exception as e:
                print(f"Failed to update memory summary: {e}")

        return {}
    except Exception as e:
        print(f"Error in save_messages: {e}")
        db.rollback()
        return {}
    finally:
        db.close()
