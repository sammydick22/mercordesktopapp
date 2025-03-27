import { contextBridge, ipcRenderer } from 'electron';

// Define the API exposed to the renderer process
contextBridge.exposeInMainWorld('electron', {
  // Time tracking functionality
  timeTracking: {
    start: () => ipcRenderer.invoke('time-tracking:start'),
    stop: () => ipcRenderer.invoke('time-tracking:stop'),
    getStatus: () => ipcRenderer.invoke('time-tracking:status'),
    onStarted: (callback: (event: any, data: any) => void) => {
      ipcRenderer.on('time-tracking:started', callback);
      return () => ipcRenderer.removeListener('time-tracking:started', callback);
    },
    onStopped: (callback: (event: any, data: any) => void) => {
      ipcRenderer.on('time-tracking:stopped', callback);
      return () => ipcRenderer.removeListener('time-tracking:stopped', callback);
    },
    onStartCommand: (callback: (event: any) => void) => {
      ipcRenderer.on('time-tracking:start-command', callback);
      return () => ipcRenderer.removeListener('time-tracking:start-command', callback);
    },
    onStopCommand: (callback: (event: any) => void) => {
      ipcRenderer.on('time-tracking:stop-command', callback);
      return () => ipcRenderer.removeListener('time-tracking:stop-command', callback);
    }
  },
  
  // Screenshots functionality
  screenshots: {
    capture: () => ipcRenderer.invoke('screenshots:capture'),
    getRecent: (limit?: number) => ipcRenderer.invoke('screenshots:recent', limit),
    onCaptured: (callback: (event: any, data: any) => void) => {
      ipcRenderer.on('screenshots:captured', callback);
      return () => ipcRenderer.removeListener('screenshots:captured', callback);
    }
  },
  
  // System information
  system: {
    getSystemInfo: () => ipcRenderer.invoke('system:info'),
    minimizeWindow: () => ipcRenderer.send('window:minimize'),
    maximizeWindow: () => ipcRenderer.send('window:maximize'),
    getPlatform: () => process.platform
  },
  
  // App version
  app: {
    getVersion: () => process.env.npm_package_version || '1.0.0'
  }
});

// Log when preload script is executed
console.log('Preload script executed');
