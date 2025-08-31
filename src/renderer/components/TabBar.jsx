import React, { useEffect, useRef, useState } from 'react';

export default function TabBar({
  tabs,
  currentTabIndex,
  onSwitchTab,
  onCloseTab,
  onAddTab,
  onNewWindow,
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const theme = localStorage.getItem('theme');
    const isDark = theme === 'dark';
    setDark(isDark);
    document.body.classList.toggle('dark', isDark);
  }, []);

  useEffect(() => {
    if (!menuOpen) return;
    const onKeyDown = (e) => {
      if (e.key === 'Escape') setMenuOpen(false);
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [menuOpen]);

  const toggleDark = () => {
    const next = !dark;
    setDark(next);
    document.body.classList.toggle('dark', next);
    localStorage.setItem('theme', next ? 'dark' : 'light');
  };

  const toggleMenu = () => setMenuOpen(v => !v);
  const closeMenu = () => setMenuOpen(false);

  return (
    <div className="tab-bar">
      <div id="tabs-container" className="tabs-container">
        {tabs.map((tab, idx) => (
          <div
            key={idx}
            className={`tab ${idx === currentTabIndex ? 'active' : ''}`}
            onClick={() => onSwitchTab(idx)}
          >
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {tab.title}
            </span>
            {tabs.length > 1 && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onCloseTab(idx);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontSize: '16px',
                  color: '#64748b',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#ef4444';
                  e.currentTarget.style.color = '#ffffff';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'none';
                  e.currentTarget.style.color = '#64748b';
                }}
              >
                ×
              </button>
            )}
          </div>
        ))}
      </div>
      <button id="new-tab-button" className="add-tab-btn" onClick={onAddTab}>+</button>
      <div className="browser-controls">
        <button
          id="new-window-button"
          className="browser-menu"
          onClick={toggleMenu}
          title="Menu"
          aria-expanded={menuOpen}
          aria-haspopup="menu"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="1"></circle>
            <circle cx="12" cy="5" r="1"></circle>
            <circle cx="12" cy="19" r="1"></circle>
          </svg>
        </button>

        {menuOpen && <div className="menu-backdrop" onClick={closeMenu} aria-hidden="true" />}

        {menuOpen && (
          <div className="app-menu" role="menu" aria-label="Menu">
            <button className="menu-item" role="menuitem">
              Configurações
            </button>

            <div className="menu-sep" />

            <div className="menu-title">Preferências</div>
            <label
              className="menu-item switch"
              role="menuitemcheckbox"
              aria-checked={dark}
            >
              <span>Modo escuro</span>
              <input type="checkbox" checked={dark} onChange={toggleDark} />
              <span className="switch-ui" aria-hidden="true"></span>
            </label>
          </div>
        )}
      </div>
    </div>
  );
}
