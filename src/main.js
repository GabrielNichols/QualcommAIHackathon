import { app, BrowserWindow , ipcMain, dialog } from 'electron';
import path from 'node:path';
import started from 'electron-squirrel-startup';
import fs from 'node:fs/promises';

if (started) {
  app.quit();
}

const createWindow = () => {
  
  const mainWindow = new BrowserWindow({
    autoHideMenuBar:true,
    fullscreen: true,
    fullscreenable: true,
    show: false, // cria oculta para evitar "flash" antes do fullscreen
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      webviewTag:true,
      disableHardwareAcceleration: true
    },
  });
  //bro seriously 
  mainWindow.setAlwaysOnTop(false,'screen');

  // Garante maximize + fullscreen antes de mostrar
  mainWindow.once('ready-to-show', () => {
    try {
      mainWindow.maximize();
      // mainWindow.setFullScreen(true);
    } finally {
      mainWindow.show();
    }
  });

  if (MAIN_WINDOW_VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
  } else {
    mainWindow.loadFile(path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`));
  }

  // Abrir DevTools automaticamente em desenvolvimento (destacado)
  if (MAIN_WINDOW_VITE_DEV_SERVER_URL) {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }

  // Atalhos: F12 e Ctrl+Shift+I para alternar DevTools
  mainWindow.webContents.on('before-input-event', (event, input) => {
    const key = String(input.key || '').toLowerCase();
    const isF12 = key === 'f12';
    const isCtrlShiftI = (input.control || input.meta) && input.shift && key === 'i';
    if (isF12 || isCtrlShiftI) {
      mainWindow.webContents.toggleDevTools();
      event.preventDefault();
    }
  });

 //mainWindow.webContents.openDevTools(); so irritating
};

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});


app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();

// in case you are reding this : You are doing great work in your life ...CC
// Mir Niyazul Haque 
  }
});

ipcMain.on("new-window",createWindow);

// Salva HTML em arquivo escolhido pelo usuário
ipcMain.handle('save-html', async (_event, html, suggestedName) => {
  try {
    const { canceled, filePath } = await dialog.showSaveDialog({
      title: 'Salvar HTML da página',
      defaultPath: suggestedName || 'pagina.html',
      filters: [{ name: 'HTML', extensions: ['html'] }],
    });
    if (canceled || !filePath) return { canceled: true };
    await fs.writeFile(filePath, html ?? '', 'utf8');
    return { canceled: false, filePath };
  } catch (err) {
    return { canceled: true, error: err?.message };
  }
});