from typing import List, TypedDict

class ChatState(TypedDict):
    thread_id: int
    user_message: str
    thread_history: List[dict]  # List of dicts representing past messages, e.g., [{"role": "user", "content": "..."}]
    global_memory: List[str]    # List of memory summaries / extracted facts
    prompt: str
    response: str
