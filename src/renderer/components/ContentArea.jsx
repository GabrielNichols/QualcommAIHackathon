import React, { useState, useRef, useEffect } from 'react';

export default function ContentArea({ showAgent, webviewRef, src }) {
  const [messages, setMessages] = useState([
    { role: 'agent', text: 'Olá! Como posso te ajudar hoje?' },
  ]);
  const [input, setInput] = useState('');
  const endRef = useRef(null);

  const sendMessage = () => {
    const value = input.trim();
    if (!value) return;
    setMessages((prev) => [...prev, { role: 'user', text: value }]);
    setInput('');
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
          <div className="agent-header">Agent</div>
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
        </div>
      )}
    </div>
  );
}
