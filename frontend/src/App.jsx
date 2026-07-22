import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { fetchDraft, fetchSubmittedInteractions } from './features/interactions/interactionsSlice';
import InteractionFormPanel from './components/InteractionFormPanel';
import AssistantChat from './components/AssistantChat';
import InteractionHistory from './components/InteractionHistory';

function newSessionId() {
  return 'sess_' + Math.random().toString(36).slice(2, 10);
}

export default function App() {
  const dispatch = useDispatch();
  const [sessionId, setSessionId] = useState(newSessionId());

  useEffect(() => {
    dispatch(fetchDraft(sessionId));
    dispatch(fetchSubmittedInteractions());
  }, [dispatch, sessionId]);

  return (
    <div className="app-shell">
      <header className="top-bar">
        <div className="brand">HCP<span>CRM</span> — Log Interaction</div>
        <div className="top-bar-sub">
          AI-first: the form on the left is filled entirely by the assistant on the right.
        </div>
      </header>

      <div className="split-shell">
        <InteractionFormPanel sessionId={sessionId} />
        <AssistantChat sessionId={sessionId} />
      </div>

      <div className="history-shell">
        <InteractionHistory />
      </div>
    </div>
  );
}
