import React, { useEffect, useRef, useState } from 'react';
import { useDispatch } from 'react-redux';
import { api } from '../api';
import { setDraft, fetchSubmittedInteractions } from '../features/interactions/interactionsSlice';

const SUGGESTIONS = [
  'Today I met with Dr. Smith and discussed Product X efficacy. Sentiment was positive, I shared brochures.',
  'Sorry, the name was actually Dr. John and the sentiment was negative.',
  'Schedule a follow-up for next Friday about the dosing question.',
  'Check compliance on this interaction.',
  'What should I focus on for my next visit with this doctor?',
  'Submit it.',
];

export default function AssistantChat({ sessionId, onNewSession }) {
  const dispatch = useDispatch();
  const [messages, setMessages] = useState([
    {
      role: 'agent',
      text: "Hi! I'm your interaction assistant. Describe a visit, call, or email you just had — I'll fill out the form on the left as we talk. Nothing is saved until you ask me to submit it.",
      tools: [],
    },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const resetChat = async () => {
    await api.resetChatSession(sessionId).catch(() => {});
    const freshDraft = await api.getDraft(sessionId).catch(() => null);
    if (freshDraft) dispatch(setDraft(freshDraft));
    setMessages([
      { role: 'agent', text: 'New session started. What would you like to log?', tools: [] },
    ]);
    onNewSession?.();
  };

  const send = async (text) => {
    const message = (text ?? input).trim();
    if (!message || sending) return;
    setInput('');
    setMessages((m) => [...m, { role: 'user', text: message, tools: [] }]);
    setSending(true);
    try {
      const res = await api.sendChatMessage(sessionId, message);
      setMessages((m) => [...m, { role: 'agent', text: res.reply, tools: res.tool_calls || [] }]);
      if (res.draft) dispatch(setDraft(res.draft));
      if (res.tool_calls?.some((t) => t.tool === 'submit_interaction')) {
        dispatch(fetchSubmittedInteractions());
      }
    } catch (err) {
      setMessages((m) => [...m, { role: 'agent', text: `⚠️ ${err.message}`, tools: [] }]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="panel right-panel">
      <div className="panel-header">
        <h2>AI Assistant</h2>
        <button className="btn ghost" onClick={resetChat} type="button">
          New conversation
        </button>
      </div>

      <div className="chat-window">
        <div className="chat-messages" ref={scrollRef}>
          {messages.map((m, i) => (
            <React.Fragment key={i}>
              {m.tools?.length > 0 && (
                <div className="tool-badge-row">
                  {m.tools.map((t, ti) => (
                    <span className="tool-badge" key={ti}>🛠 {t.tool}</span>
                  ))}
                </div>
              )}
              <div className={`chat-bubble ${m.role === 'user' ? 'user' : 'agent'}`}>{m.text}</div>
            </React.Fragment>
          ))}
          {sending && <div className="chat-bubble agent">Thinking…</div>}
        </div>

        <div className="chat-input-row">
          <input
            placeholder="Tell me about your interaction…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
          />
          <button className="btn" onClick={() => send()} disabled={sending}>
            Send
          </button>
        </div>
      </div>

      <div className="suggestion-row">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            className="btn secondary"
            onClick={() => send(s)}
            disabled={sending}
          >
            {s.length > 42 ? s.slice(0, 42) + '…' : s}
          </button>
        ))}
      </div>
    </div>
  );
}
