import React, { useState, useRef, useEffect, useMemo } from 'react';

export default function ContentArea({ showAgent, webviewRef, src }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [showOrb, setShowOrb] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const endRef = useRef(null);

  // gera 300 partículas do orb uma vez
  const orbParticles = useMemo(() => {
    const total = 500;
    const arr = [];
    for (let i = 1; i <= total; i++) {
      const z = `${Math.floor(Math.random() * 360)}deg`;
      const y = `${Math.floor(Math.random() * 360)}deg`;
      const delay = `${(i / 100).toFixed(2)}s`;
      arr.push({ i, z, y, delay });
    }
    return arr;
  }, []);

  // cria nova sessão e define como atual
  const createNewSession = (initialMessages) => {
    const makeId = () =>
      (typeof crypto !== 'undefined' && crypto.randomUUID)
        ? crypto.randomUUID()
        : String(Date.now()) + Math.random().toString(16).slice(2);
    const msgs = initialMessages ?? [{ role: 'agent', text: 'Olá! Como posso te ajudar hoje?' }];
    const title = msgs.find(m => m.role === 'user')?.text?.slice(0, 40) || 'Nova conversa';
    const s = { id: makeId(), messages: msgs, title, updatedAt: Date.now() };
    setSessions((prev) => {
      const next = [s, ...prev];
      localStorage.setItem('chatSessions', JSON.stringify(next));
      return next;
    });
    setCurrentSessionId(s.id);
    setMessages(msgs);
  };

  // carrega histórico do localStorage uma vez
  useEffect(() => {
    try {
      const raw = localStorage.getItem('chatSessions');
      const parsed = raw ? JSON.parse(raw) : [];
      if (Array.isArray(parsed) && parsed.length) {
        setSessions(parsed);
        setCurrentSessionId(parsed[0].id);
        setMessages(parsed[0].messages || []);
      } else {
        createNewSession([
          { role: 'agent', text: 'Olá! Como posso te ajudar hoje?' },
        ]);
      }
    } catch {
      createNewSession([
        { role: 'agent', text: 'Olá! Como posso te ajudar hoje?' },
      ]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sendMessage = () => {
    const value = input.trim();
    if (!value) return;
    const nextMessages = [...messages, { role: 'user', text: value }];
    setMessages(nextMessages);
    setInput('');
    // atualiza sessão atual e move para o topo
    setSessions((prev) => {
      const idx = prev.findIndex(s => s.id === currentSessionId);
      let updated = prev.slice();
      if (idx >= 0) {
        const s = prev[idx];
        const title = s.title && s.title !== 'Nova conversa' ? s.title : value.slice(0, 40);
        const newSession = { ...s, messages: nextMessages, title, updatedAt: Date.now() };
        updated.splice(idx, 1);
        updated = [newSession, ...updated];
      } else {
        const s = {
          id: currentSessionId ?? String(Date.now()),
          messages: nextMessages,
          title: value.slice(0, 40),
          updatedAt: Date.now()
        };
        updated = [s, ...updated];
        if (!currentSessionId) setCurrentSessionId(s.id);
      }
      localStorage.setItem('chatSessions', JSON.stringify(updated));
      return updated;
    });
  };

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="content-area">
      <div
        className="webview-container"
        style={{ width: showAgent ? '60%' : '100%' }}
      >
        <webview
          id="webview"
          ref={webviewRef}
          src={src}
          style={{ width: '100%', height: '100%', border: 'none', background: '#ffffff' }}
        />
      </div>

      {showAgent && (
        <div className="agent-panel">
          <div className="agent-header">
            <span>Agent</span>
            <div className="agent-head-actions">
              <button
                className="agent-small-btn"
                onClick={() => setShowHistory(v => !v)}
                aria-pressed={showHistory}
                title="Mostrar histórico"
              >
                Histórico
              </button>
              <button
                className="agent-small-btn"
                onClick={() => createNewSession()}
                title="Nova conversa"
              >
                Nova
              </button>
            </div>
          </div>
          <div className="agent-body">
            {/* Lista de mensagens */}
            <div className="chat-messages">
              {messages.map((m, i) => (
                <div key={i} className={`chat-message ${m.role === 'user' ? 'user' : 'agent'}`}>
                  <div className="chat-bubble">
                    {m.text}
                  </div>
                </div>
              ))}
              <div ref={endRef} />
            </div>

            {/* Composer */}
            <div className="chat-compose">
              <button
                className="chat-icon-btn"
                title="Anexar"
                aria-label="Anexar arquivo"
              >
                {/* plus icon */}
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 5v14M5 12h14" />
                </svg>
              </button>

              <input
                className="chat-input"
                placeholder="Digite sua mensagem..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
              />

              <button
                className="chat-icon-btn"
                title="Áudio"
                aria-label="Gravar áudio"
                onClick={() => setShowOrb(true)}
              >
                {/* mic icon */}
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 1 0 6 0V4a3 3 0 0 0-3-3Z" />
                  <path d="M19 10a7 7 0 0 1-14 0" />
                  <path d="M12 19v4" />
                </svg>
              </button>

              <button
                id="send-button"
                className="chat-send-btn"
                onClick={sendMessage}
                title="Enviar"
                aria-label="Enviar"
              >
                {/* avião de papel */}
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M21.44 2.56a1 1 0 0 0-1.06-.23l-16 6a1 1 0 0 0-.07 1.87l6.78 2.71 2.71 6.78a1 1 0 0 0 .92.61h.05a1 1 0 0 0 .92-.64l6-16a1 1 0 0 0-.25-1.1ZM14.31 20l-2.05-5.12 4.8-4.8-6.81 3.61L4 12.69 20 6Z"/>
                </svg>
              </button>
            </div>
          </div>

          {/* Painel lateral de histórico */}
          {showHistory && (
            <>
              {/* backdrop para fechar ao clicar fora */}
              <div
                className="history-backdrop"
                onClick={() => setShowHistory(false)}
                aria-hidden="true"
              />
              <aside className="chat-history-panel" aria-label="Histórico de conversas">
                <div className="history-header">
                  <span>Histórico</span>
                  <button
                    className="history-close"
                    onClick={() => setShowHistory(false)}
                    aria-label="Fechar histórico"
                    title="Fechar"
                  >
                    ×
                  </button>
                </div>
                <div className="history-list">
                  {sessions.map((s) => (
                    <button
                      key={s.id}
                      className={`history-item ${s.id === currentSessionId ? 'active' : ''}`}
                      onClick={() => {
                        setCurrentSessionId(s.id);
                        setMessages(s.messages || []);
                      }}
                      title={new Date(s.updatedAt).toLocaleString()}
                    >
                      <div className="history-title">{s.title || 'Sem título'}</div>
                      <div className="history-meta">
                        {new Date(s.updatedAt).toLocaleDateString()} {new Date(s.updatedAt).toLocaleTimeString()}
                      </div>
                    </button>
                  ))}
                </div>
              </aside>
            </>
          )}
        </div>
      )}

      {/* Overlay full-screen com orb e botões */}
      {showOrb && (
        <div className="orb-overlay" role="dialog" aria-modal="true" aria-label="Visualização de Áudio">
          <div className="orb-stage">
            <div className="orb-wrap">
              {orbParticles.map(({ i, z, y, delay }) => (
                <div
                  key={i}
                  className="orb-p"
                  style={{ '--i': i, '--z': z, '--y': y, '--delay': delay }}
                />
              ))}
            </div>
          </div>

          <div className="orb-controls">
            <button
              className="orb-btn"
              onClick={() => setShowOrb(false)}
              aria-label="Fechar"
              title="Fechar"
            >
              ×
            </button>
            <button
              className="orb-btn primary"
              aria-label="Iniciar/Parar gravação"
              title="Áudio"
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 1 0 6 0V4a3 3 0 0 0-3-3Z" />
                <path d="M19 10a7 7 0 0 1-14 0" />
                <path d="M12 19v4" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
