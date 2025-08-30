import React, { useEffect, useMemo, useRef, useState } from 'react';

function getTabTitle(url) {
  if (!url || url === 'about:blank') return 'Nova aba';
  try {
    const domain = new URL(url).hostname;
    return domain.replace('www.', '') || 'Nova aba';
  } catch {
    return 'Nova aba';
  }
}

export default function App() {
  const [tabs, setTabs] = useState([{ title: 'Nova aba', url: 'about:blank' }]);
  const [currentTabIndex, setCurrentTabIndex] = useState(0);
  const [address, setAddress] = useState('');
  const [canGoBack, setCanGoBack] = useState(false);
  const [canGoForward, setCanGoForward] = useState(false);

  const webviewRef = useRef(null);
  const urlInputRef = useRef(null);

  const activeTab = useMemo(() => tabs[currentTabIndex] ?? { title: 'Nova aba', url: 'about:blank' }, [tabs, currentTabIndex]);

  useEffect(() => {
    urlInputRef.current?.focus();
  }, []);

  useEffect(() => {
    const wv = webviewRef.current;
    if (!wv) return;

    const updateNavButtons = () => {
      try {
        setCanGoBack(Boolean(wv.canGoBack?.() ?? false));
        setCanGoForward(Boolean(wv.canGoForward?.() ?? false));
      } catch {
        // no-op
      }
    };

    const handleDidNavigate = (e) => {
      const url = e.url;
      setAddress(url);
      setTabs((prev) => {
        const next = [...prev];
        if (next[currentTabIndex]) {
          next[currentTabIndex] = { ...next[currentTabIndex], url, title: getTabTitle(url) };
        }
        return next;
      });
      updateNavButtons();
    };

    const handleDidNavigateInPage = () => {
      updateNavButtons();
    };

    wv.addEventListener('did-navigate', handleDidNavigate);
    wv.addEventListener('did-navigate-in-page', handleDidNavigateInPage);

    // Atualiza periodicamente os botões (alguns sites alteram histórico via SPA)
    const interval = setInterval(updateNavButtons, 500);

    return () => {
      wv.removeEventListener('did-navigate', handleDidNavigate);
      wv.removeEventListener('did-navigate-in-page', handleDidNavigateInPage);
      clearInterval(interval);
    };
  }, [currentTabIndex]);

  function normalizeUrl(input) {
    const value = input.trim();
    if (!value) return '';
    if (value.startsWith('http://') || value.startsWith('https://')) return value;
    if (value.includes('.') && !value.includes(' ')) return `https://${value}`;
    return `https://www.google.com/search?q=${encodeURIComponent(value)}`;
  }

  function handleGo() {
    const url = normalizeUrl(address);
    if (!url) return;
    setTabs((prev) => {
      const next = [...prev];
      if (next[currentTabIndex]) {
        next[currentTabIndex] = { ...next[currentTabIndex], url, title: getTabTitle(url) };
      }
      return next;
    });
  }

  function addTab() {
    setTabs((prev) => [...prev, { title: 'Nova aba', url: 'about:blank' }]);
    setCurrentTabIndex(tabs.length);
    setAddress('');
  }

  function switchToTab(index) {
    if (index < 0 || index >= tabs.length) return;
    setCurrentTabIndex(index);
    const t = tabs[index];
    setAddress(t.url === 'about:blank' ? '' : t.url);
  }

  function closeTab(index) {
    setTabs((prev) => {
      if (prev.length <= 1) return prev;
      const next = prev.slice(0, index).concat(prev.slice(index + 1));
      let newIndex = currentTabIndex;
      if (newIndex >= next.length) newIndex = next.length - 1;
      else if (newIndex > index) newIndex = newIndex - 1;
      setCurrentTabIndex(newIndex);
      const t = next[newIndex];
      setAddress(t?.url === 'about:blank' ? '' : t?.url ?? '');
      return next;
    });
  }

  function openNewWindow() {
    if (typeof window !== 'undefined' && window.api?.newWindow) {
      window.api.newWindow();
    }
  }

  function goBack() {
    webviewRef.current?.canGoBack?.() && webviewRef.current?.goBack?.();
  }
  function goForward() {
    webviewRef.current?.canGoForward?.() && webviewRef.current?.goForward?.();
  }
  function reload() {
    webviewRef.current?.reload?.();
  }

  useEffect(() => {
    const onKey = (event) => {
      if (!(event.ctrlKey || event.metaKey)) return;
      switch (event.key) {
        case 't':
          event.preventDefault();
          addTab();
          break;
        case 'w':
          event.preventDefault();
          if (tabs.length > 1) closeTab(currentTabIndex);
          break;
        case 'r':
          event.preventDefault();
          reload();
          break;
        case 'l':
          event.preventDefault();
          urlInputRef.current?.focus();
          urlInputRef.current?.select();
          break;
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [tabs.length, currentTabIndex]);

  return (
    <div className="browser-window">
      <div className="tab-bar">
        <div id="tabs-container" className="tabs-container">
          {tabs.map((tab, idx) => (
            <div
              key={idx}
              className={`tab ${idx === currentTabIndex ? 'active' : ''}`}
              onClick={() => switchToTab(idx)}
            >
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {tab.title}
              </span>
              {tabs.length > 1 && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    closeTab(idx);
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
        <button id="new-tab-button" className="add-tab-btn" onClick={addTab}>+</button>
        <div className="browser-controls">
          <button id="new-window-button" className="browser-menu" onClick={openNewWindow} title="Nova janela">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="1"></circle>
              <circle cx="12" cy="5" r="1"></circle>
              <circle cx="12" cy="19" r="1"></circle>
            </svg>
          </button>
        </div>
      </div>

      <div className="navigation-bar">
        <div className="nav-controls">
          <button id="back-button" className="nav-btn" onClick={goBack} disabled={!canGoBack} title="Voltar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="m15 18-6-6 6-6" />
            </svg>
          </button>
          <button id="forward-button" className="nav-btn" onClick={goForward} disabled={!canGoForward} title="Avançar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="m9 18 6-6-6-6" />
            </svg>
          </button>
          <button id="reload-button" className="nav-btn" onClick={reload} title="Recarregar">
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
            onChange={(e) => setAddress(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleGo();
              }
            }}
            ref={urlInputRef}
          />
          <button id="go" className="bookmark-btn" onClick={handleGo} title="Ir">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26" />
            </svg>
          </button>
        </div>
      </div>

      <div className="content-area">
        <div className="webview-container">
          <webview
            id="webview"
            ref={webviewRef}
            // Usa o URL da aba ativa; 'about:blank' quando vazia
            src={activeTab.url || ''}
            style={{ width: '100%', height: '100%', border: 'none', background: '#ffffff' }}
          />
        </div>
      </div>
    </div>
  );
}
