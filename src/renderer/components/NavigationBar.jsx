import React from 'react';

export default function NavigationBar({
  address,
  onAddressChange,
  onGo,
  canGoBack,
  canGoForward,
  onBack,
  onForward,
  onReload,
  showAgent,
  onToggleAgent,
  urlInputRef,
}) {
  return (
    <div className="navigation-bar">
      <div className="nav-controls">
        <button id="back-button" className="nav-btn" onClick={onBack} disabled={!canGoBack} title="Voltar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="m15 18-6-6 6-6" />
          </svg>
        </button>
        <button id="forward-button" className="nav-btn" onClick={onForward} disabled={!canGoForward} title="Avançar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="m9 18 6-6-6-6" />
          </svg>
        </button>
        <button id="reload-button" className="nav-btn" onClick={onReload} title="Recarregar">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
            <path d="M21 3v5h-5" />
            <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
            <path d="M3 21v-5h5" />
          </svg>
        </button>
      </div>

      <div className="address-bar">
        <div className="security-icon">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
            <path d="m7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
        </div>
        <input
          id="url-input"
          className="url-input"
          required
          placeholder="Digite uma URL ou pesquisa"
          value={address}
          onChange={(e) => onAddressChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              onGo();
            }
          }}
          ref={urlInputRef}
        />
        <button id="go" className="bookmark-btn" onClick={onGo} title="Ir">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26" />
          </svg>
        </button>
      </div>

      <div className="nav-actions">
        <button
          id="agent-button"
          className="bookmark-btn"
          onClick={onToggleAgent}
          title={showAgent ? 'Fechar Agent' : 'Abrir Agent'}
          aria-pressed={showAgent}
        >
          Agent
        </button>
      </div>
    </div>
  );
}
