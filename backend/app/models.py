import uuid
import datetime as dt
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


def gen_id():
    return str(uuid.uuid4())


class InteractionType(str, enum.Enum):
    IN_PERSON = "In-Person Visit"
    VIRTUAL = "Virtual Meeting"
    CALL = "Phone Call"
    EMAIL = "Email"
    CONFERENCE = "Conference/Event"


class Sentiment(str, enum.Enum):
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"


class HCP(Base):
    __tablename__ = "hcps"

    id = Column(String(36), primary_key=True, default=gen_id)
    name = Column(String(255), nullable=False)
    specialty = Column(String(255))
    hospital = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String(36), primary_key=True, default=gen_id)
    hcp_id = Column(String(36), ForeignKey("hcps.id"), nullable=False)

    interaction_type = Column(Enum(InteractionType), default=InteractionType.IN_PERSON)
    interaction_date = Column(DateTime, default=dt.datetime.utcnow)

    topics_discussed = Column(Text)          # comma separated or free text
    products_discussed = Column(Text)
    materials_shared = Column(Text)
    samples_distributed = Column(Text)

    summary = Column(Text)                   # AI generated or manual summary
    sentiment = Column(Enum(Sentiment), default=Sentiment.NEUTRAL)
    follow_up_required = Column(String(10), default="No")   # Yes/No
    follow_up_notes = Column(Text)
    follow_up_date = Column(DateTime, nullable=True)

    compliance_flag = Column(String(10), default="Clear")   # Clear / Review
    compliance_notes = Column(Text)

    raw_notes = Column(Text)                 # original free-text / chat transcript
    source = Column(String(20), default="form")  # form | chat

    created_at = Column(DateTime, default=dt.datetime.utcnow)
    updated_at = Column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")
