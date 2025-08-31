const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
    newWindow: () => {
        ipcRenderer.send('new-window');
    },
    saveHTML: (html, suggestedName) => ipcRenderer.invoke('save-html', html, suggestedName),
});
