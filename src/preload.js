const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    newWindow: () => {
        ipcRenderer.send('new-window');
    },
    saveHTML: (html, suggestedName) => ipcRenderer.invoke('save-html', html, suggestedName),

  // Chamada ao servidor local FastAPI (server_quick_start.py)
  localChat: async (payload) => {
    const body =
      payload && typeof payload === 'object'
      ? payload
      : { message: String(payload ?? '') };

    const res = await fetch('http://localhost:8080/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`Local LLM request failed: ${res.status} ${text}`);
    }

    return res.json();
  },
});
