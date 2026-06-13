from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from backend.state import ChatState
from backend.nodes import (
    load_thread_history,
    load_global_memory,
    build_prompt,
    call_gemini,
    save_messages,
)

# Initialize the StateGraph
workflow = StateGraph(ChatState)

# Add all nodes
workflow.add_node("load_thread_history", load_thread_history)
workflow.add_node("load_global_memory", load_global_memory)
workflow.add_node("build_prompt", build_prompt)
workflow.add_node("call_gemini", call_gemini)
workflow.add_node("save_messages", save_messages)

# Define transitions
workflow.add_edge(START, "load_thread_history")
workflow.add_edge("load_thread_history", "load_global_memory")
workflow.add_edge("load_global_memory", "build_prompt")
workflow.add_edge("build_prompt", "call_gemini")
workflow.add_edge("call_gemini", "save_messages")
workflow.add_edge("save_messages", END)

# Initialize the checkpointer
memory_checkpointer = MemorySaver()

# Compile the workflow graph
compiled_graph = workflow.compile(checkpointer=memory_checkpointer)
