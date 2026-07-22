import datetime as dt

DRAFT_FIELDS = [
    "hcp_name", "hcp_specialty", "hcp_hospital",
    "interaction_type", "interaction_date",
    "topics_discussed", "products_discussed",
    "materials_shared", "samples_distributed",
    "summary", "sentiment",
    "follow_up_required", "follow_up_notes", "follow_up_date",
    "compliance_flag", "compliance_notes",
]

_DRAFTS: dict[str, dict] = {}


def blank_draft() -> dict:
    return {
        "hcp_name": None,
        "hcp_specialty": None,
        "hcp_hospital": None,
        "interaction_type": None,
        "interaction_date": None,
        "topics_discussed": None,
        "products_discussed": None,
        "materials_shared": None,
        "samples_distributed": None,
        "summary": None,
        "sentiment": None,
        "follow_up_required": None,
        "follow_up_notes": None,
        "follow_up_date": None,
        "compliance_flag": None,
        "compliance_notes": None,
        "submitted": False,
        "last_updated": dt.datetime.utcnow().isoformat(),
    }


def get_draft(session_id: str) -> dict:
    return _DRAFTS.setdefault(session_id, blank_draft())


def patch_draft(session_id: str, patch: dict) -> dict:
    """Merge only the non-empty fields in `patch` into the session's draft."""
    draft = get_draft(session_id)
    for key, value in patch.items():
        if key in DRAFT_FIELDS and value not in (None, "", "null"):
            draft[key] = value
    draft["last_updated"] = dt.datetime.utcnow().isoformat()
    return draft


def reset_draft(session_id: str) -> dict:
    _DRAFTS[session_id] = blank_draft()
    return _DRAFTS[session_id]
