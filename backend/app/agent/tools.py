
import json
import datetime as dt
from typing import Optional
from langchain_core.tools import tool
from app.database import SessionLocal
from app import models
from app.agent.llm import get_llm
from app.agent import draft_store


def build_tools(session_id: str):
    """Factory: returns a fresh tool list bound to one chat session's draft."""

    # -----------------------------------------------------------------
    # Tool 1 (required): Log Interaction
    # -----------------------------------------------------------------
    @tool
    def log_interaction(
        hcp_name: Optional[str] = None,
        hcp_specialty: Optional[str] = None,
        hcp_hospital: Optional[str] = None,
        interaction_type: Optional[str] = None,
        interaction_date: Optional[str] = None,
        topics_discussed: Optional[str] = None,
        products_discussed: Optional[str] = None,
        materials_shared: Optional[str] = None,
        samples_distributed: Optional[str] = None,
        summary: Optional[str] = None,
        sentiment: Optional[str] = None,
        follow_up_required: Optional[str] = None,
        follow_up_notes: Optional[str] = None,
    ) -> str:
        """Capture a NEW interaction the rep is describing for the first time in
        this conversation, and populate the left-hand form panel with it. Do NOT
        save anything to the database here — this only fills the on-screen draft.

        Call this once per new visit/call/email the rep describes. Extract every
        field you can infer from their sentence:
        - hcp_name: the doctor's name exactly as said (e.g. "Dr. Smith").
        - hcp_specialty / hcp_hospital: only if explicitly mentioned.
        - interaction_type: one of "In-Person Visit", "Virtual Meeting",
          "Phone Call", "Email", "Conference/Event". Default to "In-Person Visit"
          if the rep says "met with" and nothing else is implied.
        - interaction_date: resolve relative dates ("today", "yesterday") into
          an ISO date (YYYY-MM-DD) using the current date given in the system
          prompt. Default to today if not mentioned.
        - topics_discussed / products_discussed: comma-separated.
        - materials_shared / samples_distributed: only if mentioned (e.g.
          "shared the brochures" -> materials_shared="Brochures").
        - sentiment: infer "Positive", "Neutral", or "Negative" from tone/wording.
        - follow_up_required: "Yes" or "No" based on whether the rep implies a
          next step.
        - summary: a concise 1-2 sentence professional summary of what happened,
          written by you.
        Leave any field you genuinely cannot infer as null — do not guess wildly.
        """
        patch = {
            "hcp_name": hcp_name, "hcp_specialty": hcp_specialty, "hcp_hospital": hcp_hospital,
            "interaction_type": interaction_type, "interaction_date": interaction_date,
            "topics_discussed": topics_discussed, "products_discussed": products_discussed,
            "materials_shared": materials_shared, "samples_distributed": samples_distributed,
            "summary": summary, "sentiment": sentiment,
            "follow_up_required": follow_up_required, "follow_up_notes": follow_up_notes,
        }
        draft = draft_store.patch_draft(session_id, patch)
        return json.dumps({"status": "draft_updated", "draft": draft})

    # -----------------------------------------------------------------
    # Tool 2 (required): Edit Interaction
    # -----------------------------------------------------------------
    @tool
    def edit_interaction(
        hcp_name: Optional[str] = None,
        hcp_specialty: Optional[str] = None,
        hcp_hospital: Optional[str] = None,
        interaction_type: Optional[str] = None,
        interaction_date: Optional[str] = None,
        topics_discussed: Optional[str] = None,
        products_discussed: Optional[str] = None,
        materials_shared: Optional[str] = None,
        samples_distributed: Optional[str] = None,
        summary: Optional[str] = None,
        sentiment: Optional[str] = None,
        follow_up_required: Optional[str] = None,
        follow_up_notes: Optional[str] = None,
        submitted_interaction_id: Optional[str] = None,
    ) -> str:
        """Correct or change ONE OR MORE fields on the CURRENT draft (or, if
        `submitted_interaction_id` is given, on an already-submitted interaction
        from history). Only pass the fields that are actually changing — leave
        everything else null so it stays untouched.

        Use this when the rep corrects something they already told you, e.g.
        "sorry, the name was actually Dr. John and the sentiment was negative"
        -> call with hcp_name="Dr. John", sentiment="Negative" and nothing else.

        Do NOT use this to log a brand-new, unrelated visit — use
        `log_interaction` for that.
        """
        patch = {
            "hcp_name": hcp_name, "hcp_specialty": hcp_specialty, "hcp_hospital": hcp_hospital,
            "interaction_type": interaction_type, "interaction_date": interaction_date,
            "topics_discussed": topics_discussed, "products_discussed": products_discussed,
            "materials_shared": materials_shared, "samples_distributed": samples_distributed,
            "summary": summary, "sentiment": sentiment,
            "follow_up_required": follow_up_required, "follow_up_notes": follow_up_notes,
        }

        if submitted_interaction_id:
            db = SessionLocal()
            try:
                row = db.query(models.Interaction).filter(
                    models.Interaction.id == submitted_interaction_id
                ).first()
                if not row:
                    return json.dumps({"error": f"No submitted interaction with id {submitted_interaction_id}"})
                field_map = {
                    "interaction_type": interaction_type, "topics_discussed": topics_discussed,
                    "products_discussed": products_discussed, "materials_shared": materials_shared,
                    "samples_distributed": samples_distributed, "summary": summary,
                    "sentiment": sentiment, "follow_up_required": follow_up_required,
                    "follow_up_notes": follow_up_notes,
                }
                for k, v in field_map.items():
                    if v not in (None, ""):
                        setattr(row, k, v)
                row.updated_at = dt.datetime.utcnow()
                db.commit()
                db.refresh(row)
                return json.dumps({"status": "submitted_interaction_updated", "interaction_id": row.id})
            finally:
                db.close()

        draft = draft_store.patch_draft(session_id, patch)
        return json.dumps({"status": "draft_updated", "draft": draft})

    # -----------------------------------------------------------------
    # Tool 3: HCP / interaction history lookup (grounding)
    # -----------------------------------------------------------------
    @tool
    def get_hcp_history(hcp_name: str, limit: int = 5) -> str:
        """Look up an HCP by name and return their recent submitted interaction
        history. Use this to check whether an HCP already exists in the system,
        to resolve ambiguity, or to answer the rep's questions about past visits.

        Args:
            hcp_name: The HCP's name to search for (fuzzy match).
            limit: Max past interactions to return.
        """
        db = SessionLocal()
        try:
            hcp = (
                db.query(models.HCP)
                .filter(models.HCP.name.ilike(f"%{hcp_name}%"))
                .first()
            )
            if not hcp:
                return json.dumps({"found": False, "message": f"No existing HCP matching '{hcp_name}'. A new HCP record will be created on submit."})
            rows = (
                db.query(models.Interaction)
                .filter(models.Interaction.hcp_id == hcp.id)
                .order_by(models.Interaction.interaction_date.desc())
                .limit(limit)
                .all()
            )
            history = [
                {
                    "date": str(r.interaction_date), "summary": r.summary,
                    "sentiment": r.sentiment, "topics": r.topics_discussed,
                }
                for r in rows
            ]
            return json.dumps({
                "found": True, "hcp_id": hcp.id, "name": hcp.name,
                "specialty": hcp.specialty, "hospital": hcp.hospital,
                "history": history,
            })
        finally:
            db.close()

    # -----------------------------------------------------------------
    # Tool 4: Compliance check on the current draft
    # -----------------------------------------------------------------
    @tool
    def check_compliance(flag: str, notes: str) -> str:
        """Assess the current draft for pharma compliance risk — off-label
        promotion, unsubstantiated claims, excessive sampling/gifting, or missing
        adverse-event capture — and record your assessment on the form.

        Args:
            flag: "Clear" if no concerns, "Review" if something needs human review.
            notes: One sentence explaining your assessment.
        """
        draft = draft_store.patch_draft(session_id, {"compliance_flag": flag, "compliance_notes": notes})
        return json.dumps({"status": "compliance_recorded", "draft": draft})

    # -----------------------------------------------------------------
    # Tool 5: Schedule a follow-up
    # -----------------------------------------------------------------
    @tool
    def schedule_follow_up(
        follow_up_required: str = "Yes",
        follow_up_date: Optional[str] = None,
        follow_up_notes: Optional[str] = None,
        submitted_interaction_id: Optional[str] = None,
    ) -> str:
        """Mark that this interaction needs a follow-up, with an optional date
        and notes on what the follow-up should cover. Applies to the current
        draft unless `submitted_interaction_id` is given, in which case it
        updates that already-submitted interaction instead.

        Args:
            follow_up_required: "Yes" or "No".
            follow_up_date: ISO date (YYYY-MM-DD) if mentioned.
            follow_up_notes: What the follow-up should address.
            submitted_interaction_id: Optional id of an already-submitted interaction to update instead of the draft.
        """
        if submitted_interaction_id:
            db = SessionLocal()
            try:
                row = db.query(models.Interaction).filter(
                    models.Interaction.id == submitted_interaction_id
                ).first()
                if not row:
                    return json.dumps({"error": f"No submitted interaction with id {submitted_interaction_id}"})
                row.follow_up_required = follow_up_required
                if follow_up_date:
                    try:
                        row.follow_up_date = dt.datetime.fromisoformat(follow_up_date)
                    except ValueError:
                        pass
                if follow_up_notes:
                    row.follow_up_notes = follow_up_notes
                db.commit()
                return json.dumps({"status": "submitted_interaction_updated", "interaction_id": row.id})
            finally:
                db.close()

        patch = {
            "follow_up_required": follow_up_required,
            "follow_up_date": follow_up_date,
            "follow_up_notes": follow_up_notes,
        }
        draft = draft_store.patch_draft(session_id, patch)
        return json.dumps({"status": "draft_updated", "draft": draft})

    # -----------------------------------------------------------------
    # Tool 6: Suggest next best action (read-only, bonus)
    # -----------------------------------------------------------------
    @tool
    def suggest_next_best_action(hcp_name: Optional[str] = None) -> str:
        """Suggest the single best talking point/action for the rep's NEXT visit
        with this HCP, based on their interaction history. Read-only — does not
        change the form.

        Args:
            hcp_name: Name to look up; defaults to the HCP currently on the draft.
        """
        name = hcp_name or draft_store.get_draft(session_id).get("hcp_name")
        if not name:
            return json.dumps({"error": "No HCP name available yet — ask the rep who this is for."})

        db = SessionLocal()
        try:
            hcp = db.query(models.HCP).filter(models.HCP.name.ilike(f"%{name}%")).first()
            history_text = "No prior interactions on file."
            if hcp:
                rows = (
                    db.query(models.Interaction)
                    .filter(models.Interaction.hcp_id == hcp.id)
                    .order_by(models.Interaction.interaction_date.desc())
                    .limit(5)
                    .all()
                )
                if rows:
                    history_text = "\n".join(
                        f"- {r.interaction_date}: {r.summary} (sentiment: {r.sentiment})" for r in rows
                    )
        finally:
            db.close()

        try:
            llm = get_llm(temperature=0.3)
            prompt = f"""You are a pharma sales strategy assistant. Based on this HCP's
history, suggest the single next best action for the rep's next visit.

HCP: {name}
History:
{history_text}

Respond in 2-3 concise sentences, no JSON."""
            suggestion = llm.invoke(prompt).content
        except Exception as e:
            suggestion = f"(LLM unavailable: {e}). Fallback tip: review the history above before your next call."
        return json.dumps({"hcp_name": name, "suggestion": suggestion})

    # -----------------------------------------------------------------
    # Tool 7: Submit — the ONLY tool that writes to the real database
    # -----------------------------------------------------------------
    @tool
    def submit_interaction() -> str:
        """Persist the CURRENT draft as a real, permanent interaction log entry.

        ONLY call this when the rep has explicitly confirmed they want to save/
        submit/log the interaction for real (e.g. "submit it", "save this",
        "log it", "yes that's correct, submit"). NEVER call this automatically
        right after log_interaction or edit_interaction — always wait for
        explicit confirmation first. If required info (at minimum the HCP name)
        is missing, do not call this — ask the rep for it instead.
        """
        draft = draft_store.get_draft(session_id)
        if not draft.get("hcp_name"):
            return json.dumps({"error": "Cannot submit: no HCP name captured yet. Ask the rep who the interaction was with."})

        db = SessionLocal()
        try:
            hcp = db.query(models.HCP).filter(models.HCP.name.ilike(draft["hcp_name"])).first()
            if not hcp:
                hcp = models.HCP(
                    name=draft["hcp_name"],
                    specialty=draft.get("hcp_specialty"),
                    hospital=draft.get("hcp_hospital"),
                )
                db.add(hcp)
                db.commit()
                db.refresh(hcp)

            interaction_date = dt.datetime.utcnow()
            if draft.get("interaction_date"):
                try:
                    interaction_date = dt.datetime.fromisoformat(draft["interaction_date"])
                except ValueError:
                    pass

            interaction = models.Interaction(
                hcp_id=hcp.id,
                interaction_type=draft.get("interaction_type") or "In-Person Visit",
                interaction_date=interaction_date,
                topics_discussed=draft.get("topics_discussed"),
                products_discussed=draft.get("products_discussed"),
                materials_shared=draft.get("materials_shared"),
                samples_distributed=draft.get("samples_distributed"),
                summary=draft.get("summary"),
                sentiment=draft.get("sentiment") or "Neutral",
                follow_up_required=draft.get("follow_up_required") or "No",
                follow_up_notes=draft.get("follow_up_notes"),
                compliance_flag=draft.get("compliance_flag") or "Clear",
                compliance_notes=draft.get("compliance_notes"),
                source="chat",
            )
            db.add(interaction)
            db.commit()
            db.refresh(interaction)
            result = {
                "status": "submitted", "interaction_id": interaction.id,
                "hcp_name": hcp.name,
            }
        finally:
            db.close()

        draft_store.reset_draft(session_id)
        return json.dumps(result)

    return [
        log_interaction,
        edit_interaction,
        get_hcp_history,
        check_compliance,
        schedule_follow_up,
        suggest_next_best_action,
        submit_interaction,
    ]
