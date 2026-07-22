import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { submitDraft, resetDraft } from '../features/interactions/interactionsSlice';

function Field({ label, value, placeholder }) {
  return (
    <div className="ai-field">
      <label>{label}</label>
      <div className={`ai-field-value ${!value ? 'empty' : ''}`}>
        {value || placeholder || '— not yet captured —'}
      </div>
    </div>
  );
}

function sentimentDotClass(s) {
  if (s === 'Positive') return 'dot positive';
  if (s === 'Negative') return 'dot negative';
  if (s === 'Neutral') return 'dot neutral';
  return 'dot';
}

export default function InteractionFormPanel({ sessionId }) {
  const dispatch = useDispatch();
  const draft = useSelector((s) => s.interactions.draft);
  const [submitting, setSubmitting] = useState(false);
  const [justSubmitted, setJustSubmitted] = useState(false);
  const [err, setErr] = useState(null);

  const hasContent = Object.entries(draft).some(
    ([k, v]) => v && !['submitted'].includes(k)
  );

  const handleSubmit = async () => {
    setErr(null);
    setSubmitting(true);
    try {
      await dispatch(submitDraft(sessionId)).unwrap();
      setJustSubmitted(true);
      setTimeout(() => setJustSubmitted(false), 3000);
    } catch (e) {
      setErr(e.message || 'Could not submit — make sure an HCP name has been captured first.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleClear = () => {
    dispatch(resetDraft(sessionId));
  };

  return (
    <div className="panel left-panel">
      <div className="panel-header">
        <h2>Interaction Details</h2>
        <span className="ai-controlled-badge">🔒 AI-controlled — filled via chat →</span>
      </div>

      <div className="ai-form">
        <div className="ai-field-row">
          <Field label="HCP Name" value={draft.hcp_name} />
          <Field label="Specialty" value={draft.hcp_specialty} />
        </div>
        <div className="ai-field-row">
          <Field label="Hospital / Clinic" value={draft.hcp_hospital} />
          <Field label="Interaction Type" value={draft.interaction_type} />
        </div>
        <div className="ai-field-row">
          <Field label="Date" value={draft.interaction_date} />
          <div className="ai-field">
            <label>Sentiment</label>
            <div className={`ai-field-value ${!draft.sentiment ? 'empty' : ''}`}>
              {draft.sentiment && <span className={sentimentDotClass(draft.sentiment)} />}
              {draft.sentiment || '— not yet captured —'}
            </div>
          </div>
        </div>

        <Field label="Topics Discussed" value={draft.topics_discussed} />
        <Field label="Products Discussed" value={draft.products_discussed} />

        <div className="ai-field-row">
          <Field label="Materials Shared" value={draft.materials_shared} />
          <Field label="Samples Distributed" value={draft.samples_distributed} />
        </div>

        <div className="ai-field full">
          <label>Summary</label>
          <div className={`ai-field-value multiline ${!draft.summary ? 'empty' : ''}`}>
            {draft.summary || '— not yet captured —'}
          </div>
        </div>

        <div className="ai-field-row">
          <Field label="Follow-up Required" value={draft.follow_up_required} />
          <Field label="Follow-up Date" value={draft.follow_up_date} />
        </div>
        {draft.follow_up_notes && <Field label="Follow-up Notes" value={draft.follow_up_notes} />}

        {draft.compliance_flag && (
          <div className="ai-field full">
            <label>Compliance</label>
            <div className="ai-field-value">
              <span className={`badge ${draft.compliance_flag === 'Review' ? 'review' : 'clear'}`}>
                {draft.compliance_flag}
              </span>
              <span style={{ marginLeft: 8, fontSize: 13, color: 'var(--color-text-muted)' }}>
                {draft.compliance_notes}
              </span>
            </div>
          </div>
        )}
      </div>

      {err && <div className="form-error">{err}</div>}
      {justSubmitted && (
        <div className="form-success">✓ Interaction submitted and saved to the CRM.</div>
      )}

      <div className="panel-actions">
        <button
          className="btn"
          onClick={handleSubmit}
          disabled={submitting || !draft.hcp_name}
          title={!draft.hcp_name ? 'Ask the assistant to capture an HCP name first' : ''}
        >
          {submitting ? 'Submitting…' : 'Submit Interaction'}
        </button>
        <button className="btn ghost" onClick={handleClear} disabled={!hasContent} type="button">
          Clear draft
        </button>
      </div>
      <p className="panel-hint">
        You can also just tell the assistant "submit it" — typing here does nothing;
        only the AI assistant on the right can fill or change these fields.
      </p>
    </div>
  );
}
