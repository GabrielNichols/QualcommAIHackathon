export async function CapturePage({ save = false } = {}) {
    const wv = webviewRef.current;
    if (!wv) return;
    try {
      const [text, meta] = await Promise.all([
        wv.executeJavaScript(`(() => {
          const raw = document.body?.innerText || '';
          // normaliza: tira espaços extras, remove linhas vazias e colapsa quebras
          return raw
            .replace(/[\\t\\r]+/g, ' ')
            .split('\\n')
            .map(l => l.trim().replace(/\\s{2,}/g, ' '))
            .filter(l => l.length > 0)
            .join('\\n');
        })()`),
        wv.executeJavaScript('({ url: location.href, title: document.title })'),
      ]);

      const capture = {
        url: meta?.url ?? activeTab.url,
        title: meta?.title ?? activeTab.title,
        text,              // apenas texto
        capturedAt: Date.now(),
      };
      localStorage.setItem('lastPageCapture', JSON.stringify(capture));

      // salvar em arquivo está desativado no UI; mantido para compatibilidade futura
      if (save) {
        // exemplo (desativado): await window.api?.saveHTML?.(text, `${safe}.txt`);
      }
    } catch (e) {
      console.error('Falha ao capturar texto da página:', e);
    }
    return text;
  }