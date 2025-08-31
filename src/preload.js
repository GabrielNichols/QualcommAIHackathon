const { contextBridge, ipcRenderer } = require('electron');

// Coloque sua chave aqui
const GEMINI_API_KEY = 'COLOQUE_SUA_CHAVE_AQUI';

contextBridge.exposeInMainWorld('api', {
    newWindow: () => {
        ipcRenderer.send('new-window');
    },
    saveHTML: (html, suggestedName) => ipcRenderer.invoke('save-html', html, suggestedName),

    // Chamada à API do Gemini (usa a env GEMINI_API_KEY)
    geminiGenerate: async (body) => {
        const key =
          (typeof GEMINI_API_KEY === 'string' && "AIzaSyDriQrhWKfiXk8H942gENbBNxaCpBTixlg") ||
          process.env.GEMINI_API_KEY ||
          process.env.VITE_GEMINI_API_KEY ||
          process.env.GOOGLE_AI_STUDIO_API_KEY;

        if (!key) {
          throw new Error('GEMINI_API_KEY ausente. Defina em src/preload.js.');
        }

        const res = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${key}`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
          }
        );
        if (!res.ok) {
          const text = await res.text().catch(() => '');
          throw new Error(`Gemini request failed: ${res.status} ${text}`);
        }
        return res.json();
    },
});
