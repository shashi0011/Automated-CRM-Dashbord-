from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import hcps, interactions, chat, draft
from app import models  # noqa: F401  (ensures models are registered before create_all)
import datetime as dt

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-First HCP CRM — Log Interaction API",
    description="Backend for the HCP module Log Interaction screen: structured "
                 "form + LangGraph conversational agent, powered by Groq.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hcps.router)
app.include_router(interactions.router)
app.include_router(chat.router)
app.include_router(draft.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "time": dt.datetime.utcnow().isoformat()}


@app.on_event("startup")
def seed_demo_data():
    from app.database import SessionLocal
    from app import models as m

    db = SessionLocal()
    try:
        if db.query(m.HCP).count() == 0:
            demo_hcps = [
                m.HCP(name="Dr. Anjali Mehra", specialty="Cardiology",
                      hospital="Fortis Escorts Heart Institute", email="a.mehra@example.com",
                      phone="+91-9876500001"),
                m.HCP(name="Dr. Rohan Kapoor", specialty="Endocrinology",
                      hospital="AIIMS Delhi", email="r.kapoor@example.com",
                      phone="+91-9876500002"),
                m.HCP(name="Dr. Sana Iyer", specialty="Oncology",
                      hospital="Tata Memorial Hospital", email="s.iyer@example.com",
                      phone="+91-9876500003"),
            ]
            db.add_all(demo_hcps)
            db.commit()
    finally:
        db.close()
