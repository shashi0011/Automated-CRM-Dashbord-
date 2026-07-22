# AI-First CRM — HCP Module: Log Interaction Screen

"Log Interaction" screen for a pharma CRM's Healthcare Professional
(HCP) module: **left = Interaction Details form, right = AI Assistant chat.** The
form is filled and corrected *exclusively* through the chat — it is never typed into
by hand — and nothing is saved to the database until the rep explicitly asks the
assistant to submit it.

---

## 1. The core rule this project is built around

> The rep never touches the form. They talk to the assistant. The assistant fills
> the form. Nothing is persisted until they explicitly say "submit it."

Concretely:
- `log_interaction` and `edit_interaction` write to a **session-scoped draft** — an
  in-memory object mirroring the form fields — never to the database.
- The React left panel renders that draft **read-only**. There are no editable
  `<input>`s on it.
- A separate `submit_interaction` tool is the *only* thing that ever creates a real
  database row, and the agent is explicitly instructed never to call it until the rep
  confirms ("submit it", "save this", "log it for real"). A manual "Submit
  Interaction" button on the panel calls the exact same backend logic, for reps who'd
  rather click than type.
- After submit, the draft resets — ready for the next interaction — and the record
  appears in the "Submitted Interactions" history below, which is separately
  editable/deletable through normal REST calls (a real CRM needs to fix mistakes in
  already-saved records too — that part isn't required to be AI-only).

---

## 2. Architecture

```
frontend/   React 18 + Redux Toolkit — split-screen UI, Google Inter font
backend/    FastAPI + LangGraph agent + SQLAlchemy (SQLite by default, Postgres/MySQL ready)
```

```
                 ┌────────────────────┐        ┌─────────────────────┐
   React  ──────►│ Interaction Details│        │   AI Assistant Chat │
  (Redux)         │  (read-only panel) │◄───────┤   (the only writer) │
                 └────────────────────┘  draft  └──────────┬──────────┘
                                          patch             │ POST /api/chat
                                                             ▼
                                               FastAPI  ──►  LangGraph Agent (Groq gemma2-9b-it)
                                                             │
                                                             ├─ log_interaction     (writes DRAFT only)
                                                             ├─ edit_interaction    (writes DRAFT only)
                                                             ├─ get_hcp_history     (read-only, grounding)
                                                             ├─ check_compliance    (writes DRAFT only)
                                                             ├─ schedule_follow_up  (writes DRAFT only)
                                                             ├─ suggest_next_best_action (read-only)
                                                             └─ submit_interaction  (writes REAL DB row)
```

Each tool's Python signature (e.g. `hcp_name`, `sentiment`, `materials_shared`) *is*
the schema Groq's tool-calling fills in — the LLM performs the entity extraction
directly as structured function-call arguments, not through a hidden second prompt.
That's the LangGraph+LLM requirement satisfied in the most literal, inspectable way:
open `app/agent/tools.py` and the extraction logic is the type signature itself.

---

## 3. The 5 (+2) LangGraph Tools

| # | Tool | What it does | Writes to |
|---|---|---|---|
| 1 | **`log_interaction`** *(required)* | Rep describes a new visit/call/email in plain English. Groq extracts HCP name, interaction type, date, topics, products, materials/samples, sentiment, follow-up need, and writes a summary — all as structured tool-call arguments. | Draft only |
| 2 | **`edit_interaction`** *(required)* | Rep corrects something already on the form ("actually it was Dr. John, sentiment was negative"). Only the mentioned fields are patched; everything else is left untouched. Can optionally target an already-submitted record via `submitted_interaction_id`. | Draft (or a submitted row, if targeted) |
| 3 | `get_hcp_history` | Looks up an HCP by name, returns their past submitted interactions — used to check for duplicates, resolve ambiguity, or answer "what did we discuss last time?" | Read-only |
| 4 | `check_compliance` | The agent assesses the current draft for pharma compliance risk (off-label claims, excessive sampling/gifting, missing adverse-event capture) and records `Clear`/`Review` + a reason. | Draft only |
| 5 | `schedule_follow_up` | Sets follow-up required/date/notes — a sales-specific action distinct from a generic edit. | Draft (or a submitted row, if targeted) |
| 6 *(bonus)* | `suggest_next_best_action` | Recommends the single best talking point for the rep's next visit, based on the HCP's history. | Read-only |
| 7 *(bonus)* | `submit_interaction` | The **only** tool that writes a permanent row to the `interactions` table. Resolves/creates the HCP by name, persists the draft, then resets it. Only called on explicit confirmation. | **Real database** |

---

## 4. Tech stack

- **Frontend:** React + Redux Toolkit, Google Inter font
- **Backend:** Python + FastAPI
- **Agent framework:** LangGraph — a `StateGraph` with an `agent` node (Groq LLM bound
  to the 7 tools above) and a `tools` node (`ToolNode`), looping until the LLM
  returns plain text
- **LLM:** Groq `gemma2-9b-it` (primary); `llama-3.3-70b-versatile` wired in as a
  configurable alternative
- **Database:** SQLAlchemy ORM — SQLite out of the box for zero-setup review,
  Postgres/MySQL via `DATABASE_URL` (see below)

---

## 5. Running it locally

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste your Groq key from https://console.groq.com/keys
uvicorn app.main:app --reload --port 8000
```

API at `http://localhost:8000` (interactive docs at `/docs`). On first boot it
auto-creates the schema and seeds 3 demo HCPs (used by `get_hcp_history` so the
"does this HCP already exist" flow has something to find).

To point at Postgres/MySQL instead of SQLite, just change `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/hcp_crm
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/hcp_crm
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # defaults to http://localhost:8000
npm run dev
```

Open `http://localhost:5173`.

---

## 6. Using the app — a full example

1. On the right, type: *"Today I met with Dr. Smith and discussed Product X
   efficacy. Sentiment was positive, I shared brochures."*
   → `log_interaction` fires, and the left panel populates: HCP Name = Dr. Smith,
   Products Discussed = Product X, Sentiment = Positive, Materials Shared =
   Brochures, plus a generated Summary. **Nothing is saved yet.**
2. Notice a mistake? Type: *"Sorry, the name was actually Dr. John and the sentiment
   was negative."*
   → `edit_interaction` fires, only `hcp_name` and `sentiment` change on the left
   panel — everything else stays exactly as it was.
3. Want a follow-up? *"Schedule a follow-up for next Friday about the dosing
   question."* → `schedule_follow_up`.
4. Want a compliance pass? *"Check compliance on this."* → `check_compliance`.
5. Want strategy? *"What should I focus on next visit with this doctor?"* →
   `suggest_next_best_action`.
6. Ready to save it for real? Type *"Submit it"* (or click **Submit Interaction** on
   the left panel — same underlying action) → `submit_interaction` creates the HCP if
   needed, writes the interaction row, and the draft clears for the next one. It now
   appears in **Submitted Interactions** below, which supports normal edit/delete.

---

## 7. Project structure

```
backend/
  app/
    agent/
      llm.py            # Groq LLM wrapper
      draft_store.py     # session-scoped draft (the left panel's backing state)
      tools.py            # the 7 LangGraph tools, factory-built per session
      graph.py             # StateGraph wiring + submission-gating system prompt
    routers/
      hcps.py
      interactions.py    # REST CRUD for already-SUBMITTED interactions (history)
      chat.py              # the only entry point that can mutate a draft
      draft.py             # GET current draft, manual Submit button, reset
    models.py, schemas.py, database.py, config.py, main.py
  requirements.txt
  .env.example

frontend/
  src/
    components/
      InteractionFormPanel.jsx   # left panel — 100% read-only
      AssistantChat.jsx           # right panel — the only writer
      InteractionHistory.jsx       # submitted-interactions list (editable)
    features/interactions/interactionsSlice.js
    api.js, App.jsx, store.js, main.jsx, index.css
  index.html    # Google Inter font import
```

---

## 8. Design notes

- **Why a session-scoped draft instead of writing straight to the DB?** Because the
  spec is explicit: filling the form is not the same as logging the interaction. A
  draft lets the rep iterate — describe, correct, describe more — with zero DB writes
  until they consciously commit.
- **Why do log/edit take individual typed fields instead of a single "notes" string
  parsed by a nested LLM call?** So the entity extraction is verifiably done by
  Groq's tool-calling itself (visible in the tool schema and in the `tool_calls`
  the API returns), rather than hidden inside a second prompt a reviewer can't see.
- **Graceful LLM degradation:** every tool that does need a secondary LLM call
  (`suggest_next_best_action`) wraps it in try/except so a missing/rate-limited Groq
  key degrades to a clear message instead of crashing the request.
- **Session chat memory** is in-memory per `session_id` for simplicity; swap in a
  LangGraph `SqliteSaver`/`PostgresSaver` checkpointer for persistent memory across
  server restarts in production.
