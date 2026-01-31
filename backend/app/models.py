from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MessageBase(BaseModel):
    role: str
    content: str


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: str
    session_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class SessionBase(BaseModel):
    title: Optional[str] = "New Chat"


class SessionCreate(SessionBase):
    pass


class Session(SessionBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionWithMessages(Session):
    messages: List[Message] = []
