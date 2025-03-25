import { app, BrowserWindow, Menu, Tray, dialog, ipcMain } from 'electron';
import * as path from 'path';
import * as url from 'url';
import { autoUpdater } from 'electron-updater';
import { PythonBackendService } from './services/python';
import { setupIPC } from './ipc';

class MainProcess {
  private mainWindow: BrowserWindow | null = null;
  private tray: Tray | null = null;
  private pythonBackend: PythonBackendService | null = null;
  private isQuitting = false;

  constructor() {
    // Handle creating/removing shortcuts on Windows when installing/uninstalling
    if (require('electron-squirrel-startup')) {
      app.quit();
    }

    this.registerAppEvents();

    // Start the app
    this.init();
  }

  private registerAppEvents() {
    app.on('window-all-closed', () => {
      // On OS X it is common for applications to stay active until the user quits
      if (process.platform !== 'darwin') {
        app.quit();
      }
    });

    app.on('activate', () => {
      // On OS X it's common to re-create a window in the app when the
      // dock icon is clicked and there are no other windows open.
      if (this.mainWindow === null) {
        this.createWindow();
      } else {
        this.mainWindow.show();
      }
    });

    app.on('before-quit', () => {
      this.isQuitting = true;
    });
  }

  private async init() {
    // Wait until the app is ready
    await app.whenReady();

    // Create the main window
    await this.createWindow();

    // Setup tray
    this.setupTray();

    // Start the Python backend
    this.startPythonBackend();

    // Setup IPC communication
    setupIPC(this.mainWindow, this.pythonBackend);

    // Check for updates
    if (process.env.NODE_ENV !== 'development') {
      this.setupAutoUpdater();
    }
  }

  private async createWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js')
      },
      icon: path.join(__dirname, '../frontend/public/favicon.ico'),
      show: false
    });

    // Load the app
    await this.loadApp();

    // Show window when it's ready to avoid flashing
    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow?.show();
    });

    this.mainWindow.on('close', (e) => {
      if (!this.isQuitting) {
        e.preventDefault();
        this.mainWindow?.hide();
        return false;
      }
      return true;
    });
  }

  private async loadApp() {
    if (!this.mainWindow) return;

    if (process.env.NODE_ENV === 'development') {
      // Load from Next.js development server
      await this.mainWindow.loadURL('http://localhost:3000');
      
      // Open DevTools in development mode
      this.mainWindow.webContents.openDevTools();
    } else {
      // Load from built Next.js app
      const appPath = path.join(process.resourcesPath, 'app');
      const indexPath = path.join(appPath, 'index.html');
      
      await this.mainWindow.loadURL(url.format({
        pathname: indexPath,
        protocol: 'file:',
        slashes: true
      }));
    }
  }

  private setupTray() {
    const iconPath = path.join(__dirname, '../frontend/public/favicon.ico');
    this.tray = new Tray(iconPath);

    const contextMenu = Menu.buildFromTemplate([
      { 
        label: 'Show App', 
        click: () => this.mainWindow?.show() 
      },
      { 
        label: 'Start Time Tracking',
        click: () => {
          this.mainWindow?.webContents.send('time-tracking:start-command');
        }
      },
      { 
        label: 'Stop Time Tracking',
        click: () => {
          this.mainWindow?.webContents.send('time-tracking:stop-command');
        }
      },
      { type: 'separator' },
      { 
        label: 'Quit', 
        click: () => {
          this.isQuitting = true;
          app.quit();
        }
      }
    ]);

    this.tray.setToolTip('Mercor Time Tracker');
    this.tray.setContextMenu(contextMenu);
    
    // Show the window when clicking the tray icon
    this.tray.on('click', () => {
      if (this.mainWindow) {
        if (this.mainWindow.isVisible()) {
          this.mainWindow.focus();
        } else {
          this.mainWindow.show();
        }
      }
    });
  }

  private startPythonBackend() {
    this.pythonBackend = new PythonBackendService();
    this.pythonBackend.start()
      .then(() => {
        console.log('Python backend started successfully');
      })
      .catch((err) => {
        console.error('Failed to start Python backend:', err);
        dialog.showErrorBox(
          'Python Backend Error', 
          'Failed to start the Python backend. The app may not function correctly.'
        );
      });
  }

  private setupAutoUpdater() {
    // Configure auto updater
    autoUpdater.autoDownload = false;

    autoUpdater.on('update-available', (info) => {
      dialog.showMessageBox({
        type: 'info',
        title: 'Update Available',
        message: `Version ${info.version} is available. Do you want to download it now?`,
        buttons: ['Yes', 'No']
      }).then((result: { response: number }) => {
        if (result.response === 0) {
          autoUpdater.downloadUpdate();
        }
      });
    });

    autoUpdater.on('update-downloaded', () => {
      dialog.showMessageBox({
        type: 'info',
        title: 'Update Ready',
        message: 'Update downloaded. It will be installed on restart. Would you like to restart now?',
        buttons: ['Restart', 'Later']
      }).then((result: { response: number }) => {
        if (result.response === 0) {
          this.isQuitting = true;
          autoUpdater.quitAndInstall();
        }
      });
    });

    autoUpdater.on('error', (err) => {
      console.error('Auto updater error:', err);
    });

    // Check for updates
    autoUpdater.checkForUpdates();
  }
}

// Create the main process instance
new MainProcess();
