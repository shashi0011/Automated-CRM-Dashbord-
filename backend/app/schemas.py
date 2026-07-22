import datetime as dt
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    hospital: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class HCPCreate(HCPBase):
    pass


class HCPOut(HCPBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: dt.datetime


class InteractionBase(BaseModel):
    hcp_id: str
    interaction_type: str = "In-Person Visit"
    interaction_date: Optional[dt.datetime] = None
    topics_discussed: Optional[str] = None
    products_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = "Neutral"
    follow_up_required: Optional[str] = "No"
    follow_up_notes: Optional[str] = None
    follow_up_date: Optional[dt.datetime] = None
    compliance_flag: Optional[str] = "Clear"
    compliance_notes: Optional[str] = None
    raw_notes: Optional[str] = None
    source: Optional[str] = "form"


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = None
    interaction_date: Optional[dt.datetime] = None
    topics_discussed: Optional[str] = None
    products_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    samples_distributed: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    follow_up_required: Optional[str] = None
    follow_up_notes: Optional[str] = None
    follow_up_date: Optional[dt.datetime] = None
    compliance_flag: Optional[str] = None
    compliance_notes: Optional[str] = None
    raw_notes: Optional[str] = None


class InteractionOut(InteractionBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: dt.datetime
    updated_at: dt.datetime


class ChatMessage(BaseModel):
    session_id: str
    message: str
    hcp_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tool_calls: List[dict] = []
    draft: Optional[dict] = None
