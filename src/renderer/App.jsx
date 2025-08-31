import React, { useEffect, useMemo, useRef, useState } from 'react';
import TabBar from './components/TabBar.jsx';
import NavigationBar from './components/NavigationBar.jsx';
import ContentArea from './components/ContentArea.jsx';

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
  const [showAgent, setShowAgent] = useState(false);

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
    wv.addEventListener('did-finish-load', handleDidFinishLoad);

    const interval = setInterval(updateNavButtons, 500);

    return () => {
      wv.removeEventListener('did-navigate', handleDidNavigate);
      wv.removeEventListener('did-navigate-in-page', handleDidNavigateInPage);
      wv.removeEventListener('did-finish-load', handleDidFinishLoad);
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

  // Home: vai para Google (ajuste se quiser outra home)
  function goHome() {
    const url = 'https://www.google.com';
    setTabs(prev => {
      const next = [...prev];
      if (next[currentTabIndex]) {
        next[currentTabIndex] = { ...next[currentTabIndex], url, title: getTabTitle(url) };
      }
      return next;
    });
    setAddress(url);
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
      <TabBar
        tabs={tabs}
        currentTabIndex={currentTabIndex}
        onSwitchTab={switchToTab}
        onCloseTab={closeTab}
        onAddTab={addTab}
        onNewWindow={openNewWindow}
      />

      <NavigationBar
        address={address}
        onAddressChange={setAddress}
        onGo={handleGo}
        canGoBack={canGoBack}
        canGoForward={canGoForward}
        onBack={goBack}
        onForward={goForward}
        onReload={reload}
        showAgent={showAgent}
        onToggleAgent={() => setShowAgent(v => !v)}
        urlInputRef={urlInputRef}
        onHome={goHome}
      />

      <ContentArea
        showAgent={showAgent}
        webviewRef={webviewRef}
        src={activeTab.url || ''}
      />
    </div>
  );
}
