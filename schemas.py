import datetime
from typing import List, Optional
from pydantic import BaseModel

class ThreadCreate(BaseModel):
    title: Optional[str] = "New Chat"

class ThreadOut(BaseModel):
    id: int
    title: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class MessageOut(BaseModel):
    id: int
    thread_id: int
    role: str
    content: str
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    thread_id: int
    message: str

class ChatResponse(BaseModel):
    response: str
