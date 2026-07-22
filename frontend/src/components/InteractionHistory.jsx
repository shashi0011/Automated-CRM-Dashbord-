import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { updateSubmittedInteraction, deleteSubmittedInteraction } from '../features/interactions/interactionsSlice';

function sentimentClass(s) {
  return { Positive: 'positive', Neutral: 'neutral', Negative: 'negative' }[s] || 'neutral';
}

function complianceClass(f) {
  return f === 'Review' ? 'review' : 'clear';
}

function EditRow({ interaction, onDone }) {
  const dispatch = useDispatch();
  const [draft, setDraft] = useState({
    summary: interaction.summary || '',
    sentiment: interaction.sentiment || 'Neutral',
    follow_up_required: interaction.follow_up_required || 'No',
    follow_up_notes: interaction.follow_up_notes || '',
  });
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      await dispatch(updateSubmittedInteraction({ id: interaction.id, payload: draft })).unwrap();
      onDone();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="interaction-row">
      <label>Summary</label>
      <textarea
        value={draft.summary}
        onChange={(e) => setDraft((d) => ({ ...d, summary: e.target.value }))}
      />
      <div className="form-grid" style={{ marginTop: 10 }}>
        <div>
          <label>Sentiment</label>
          <select
            value={draft.sentiment}
            onChange={(e) => setDraft((d) => ({ ...d, sentiment: e.target.value }))}
          >
            <option>Positive</option>
            <option>Neutral</option>
            <option>Negative</option>
          </select>
        </div>
        <div>
          <label>Follow-up Required</label>
          <select
            value={draft.follow_up_required}
            onChange={(e) => setDraft((d) => ({ ...d, follow_up_required: e.target.value }))}
          >
            <option value="No">No</option>
            <option value="Yes">Yes</option>
          </select>
        </div>
        <div className="full">
          <label>Follow-up Notes</label>
          <input
            value={draft.follow_up_notes}
            onChange={(e) => setDraft((d) => ({ ...d, follow_up_notes: e.target.value }))}
          />
        </div>
      </div>
      <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
        <button className="btn" onClick={save} disabled={saving}>
          {saving ? 'Saving…' : 'Save changes'}
        </button>
        <button className="btn ghost" onClick={onDone} type="button">
          Cancel
        </button>
      </div>
    </div>
  );
}

export default function InteractionHistory() {
  const dispatch = useDispatch();
  const interactions = useSelector((s) => s.interactions.submittedInteractions);
  const status = useSelector((s) => s.interactions.status);
  const [editingId, setEditingId] = useState(null);

  if (status === 'loading') {
    return <div className="card"><p className="empty-state">Loading history…</p></div>;
  }

  return (
    <div className="card">
      <h3 className="section-title">Submitted Interactions</h3>
      {interactions.length === 0 && (
        <p className="empty-state">Nothing submitted yet — use the AI assistant above to log and submit an interaction.</p>
      )}
      {interactions.map((it) =>
        editingId === it.id ? (
          <EditRow key={it.id} interaction={it} onDone={() => setEditingId(null)} />
        ) : (
          <div className="interaction-row" key={it.id}>
            <div className="interaction-row-header">
              <div>
                <span className="interaction-type">{it.interaction_type}</span>{' '}
                <span className={`badge ${sentimentClass(it.sentiment)}`}>{it.sentiment}</span>
                <span className={`badge ${complianceClass(it.compliance_flag)}`}>
                  {it.compliance_flag === 'Review' ? 'Compliance: Review' : 'Compliance: Clear'}
                </span>
                {it.source === 'chat' && <span className="badge neutral">via Chat Agent</span>}
              </div>
              <span className="interaction-date">
                {new Date(it.interaction_date).toLocaleString()}
              </span>
            </div>
            <p className="interaction-summary">{it.summary || '—'}</p>
            <p className="interaction-meta">
              {it.topics_discussed && <>Topics: {it.topics_discussed} · </>}
              {it.products_discussed && <>Products: {it.products_discussed} · </>}
              {it.follow_up_required === 'Yes' && <>Follow-up: {it.follow_up_notes || 'scheduled'}</>}
            </p>
            <div style={{ marginTop: 10, display: 'flex', gap: 8 }}>
              <button className="btn secondary" onClick={() => setEditingId(it.id)}>
                Edit
              </button>
              <button
                className="btn ghost"
                onClick={() => dispatch(deleteSubmittedInteraction(it.id))}
              >
                Delete
              </button>
            </div>
          </div>
        )
      )}
    </div>
  );
}
