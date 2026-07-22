from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/interactions", tags=["Interactions"])

# NOTE: These REST endpoints exist for viewing/editing/deleting already-
# SUBMITTED interactions (the history list) and for API completeness. They
# are intentionally NOT used by the primary Log Interaction UI flow — per
# spec, new interactions only ever enter the system through the AI agent's
# `submit_interaction` tool (chat command or the "Submit" button, which both
# call the same tool), never through a manually-filled form.


@router.get("", response_model=list[schemas.InteractionOut])
def list_interactions(hcp_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Interaction)
    if hcp_id:
        q = q.filter(models.Interaction.hcp_id == hcp_id)
    return q.order_by(models.Interaction.interaction_date.desc()).all()


@router.post("", response_model=schemas.InteractionOut)
def create_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    """Structured-form submission path (non-chat)."""
    hcp = db.query(models.HCP).filter(models.HCP.id == payload.hcp_id).first()
    if not hcp:
        raise HTTPException(404, "HCP not found")

    interaction = models.Interaction(**payload.model_dump())
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


@router.get("/{interaction_id}", response_model=schemas.InteractionOut)
def get_interaction(interaction_id: str, db: Session = Depends(get_db)):
    row = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not row:
        raise HTTPException(404, "Interaction not found")
    return row


@router.put("/{interaction_id}", response_model=schemas.InteractionOut)
def update_interaction(interaction_id: str, payload: schemas.InteractionUpdate, db: Session = Depends(get_db)):
    """Structured edit path — mirrors the `edit_interaction` LangGraph tool."""
    row = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not row:
        raise HTTPException(404, "Interaction not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{interaction_id}")
def delete_interaction(interaction_id: str, db: Session = Depends(get_db)):
    row = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not row:
        raise HTTPException(404, "Interaction not found")
    db.delete(row)
    db.commit()
    return {"status": "deleted"}
