import { BrowserWindow, ipcMain } from 'electron';
import { TimeTrackingHandler } from './timeTracking';
import { ScreenshotHandler } from './screenshots';
import { SystemHandler } from './system';
import { PythonBackendService } from '../services/python';

export function setupIPC(mainWindow: BrowserWindow | null, pythonBackend: PythonBackendService | null) {
  if (!mainWindow || !pythonBackend) {
    console.error('Cannot setup IPC: window or Python backend is null');
    return;
  }

  const timeTracking = new TimeTrackingHandler(mainWindow, pythonBackend);
  const screenshots = new ScreenshotHandler(mainWindow, pythonBackend);
  const system = new SystemHandler(mainWindow);

  // Time tracking handlers
  ipcMain.handle('time-tracking:start', timeTracking.start.bind(timeTracking));
  ipcMain.handle('time-tracking:stop', timeTracking.stop.bind(timeTracking));
  ipcMain.handle('time-tracking:status', timeTracking.getStatus.bind(timeTracking));

  // Screenshot handlers
  ipcMain.handle('screenshots:capture', screenshots.capture.bind(screenshots));
  ipcMain.handle('screenshots:recent', screenshots.getRecent.bind(screenshots));

  // System handlers
  ipcMain.handle('system:info', system.getSystemInfo.bind(system));
  ipcMain.on('window:minimize', () => mainWindow.minimize());
  ipcMain.on('window:maximize', () => {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  });
}
