import React from 'react';

export default function TabBar({
  tabs,
  currentTabIndex,
  onSwitchTab,
  onCloseTab,
  onAddTab,
  onNewWindow,
}) {
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
        <button id="new-window-button" className="browser-menu" onClick={onNewWindow} title="Nova janela">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="1"></circle>
            <circle cx="12" cy="5" r="1"></circle>
            <circle cx="12" cy="19" r="1"></circle>
          </svg>
        </button>
      </div>
    </div>
  );
}
