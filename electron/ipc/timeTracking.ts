import { BrowserWindow } from 'electron';
import * as path from 'path';
import * as fs from 'fs';
import axios from 'axios';
import { PythonBackendService } from '../services/python';

export class TimeTrackingHandler {
  private mainWindow: BrowserWindow;
  private pythonBackend: PythonBackendService;
  private isTracking: boolean = false;
  private currentSessionId: string | undefined = undefined;

  constructor(mainWindow: BrowserWindow, pythonBackend: PythonBackendService) {
    this.mainWindow = mainWindow;
    this.pythonBackend = pythonBackend;
  }

  async start(_event: Electron.IpcMainInvokeEvent): Promise<{ success: boolean; message?: string; sessionId?: string }> {
    try {
      if (!this.pythonBackend.isRunning()) {
        return { success: false, message: 'Python backend is not running' };
      }

      if (this.isTracking) {
        return { success: false, message: 'Time tracking is already active' };
      }

      // Call the Python API to start time tracking
      const response = await axios.post(
        `${this.pythonBackend.getApiBaseUrl()}/time-entries/start`,
        {}
      );

      if (response.status === 200 && response.data.success) {
        this.isTracking = true;
        this.currentSessionId = response.data.session_id;
        
        // Notify renderer process that tracking has started
        this.mainWindow.webContents.send('time-tracking:started', {
          sessionId: this.currentSessionId,
          timestamp: new Date().toISOString()
        });
        
        return { 
          success: true, 
          sessionId: this.currentSessionId 
        };
      } else {
        return { 
          success: false, 
          message: response.data.message || 'Failed to start time tracking' 
        };
      }
    } catch (error) {
      console.error('Error starting time tracking:', error);
      return { 
        success: false, 
        message: error instanceof Error ? error.message : 'Unknown error' 
      };
    }
  }

  async stop(_event: Electron.IpcMainInvokeEvent): Promise<{ success: boolean; message?: string; sessionData?: any }> {
    try {
      if (!this.pythonBackend.isRunning()) {
        return { success: false, message: 'Python backend is not running' };
      }

      if (!this.isTracking) {
        return { success: false, message: 'No active time tracking session' };
      }

      // Call the Python API to stop time tracking
      const response = await axios.post(
        `${this.pythonBackend.getApiBaseUrl()}/time-entries/stop`,
        { session_id: this.currentSessionId }
      );

      if (response.status === 200 && response.data.success) {
        this.isTracking = false;
        const sessionData = response.data.session;
        
        // Notify renderer process that tracking has stopped
        this.mainWindow.webContents.send('time-tracking:stopped', {
          sessionId: this.currentSessionId,
          sessionData,
          timestamp: new Date().toISOString()
        });
        
        this.currentSessionId = undefined;
        
        return { 
          success: true, 
          sessionData 
        };
      } else {
        return { 
          success: false, 
          message: response.data.message || 'Failed to stop time tracking' 
        };
      }
    } catch (error) {
      console.error('Error stopping time tracking:', error);
      return { 
        success: false, 
        message: error instanceof Error ? error.message : 'Unknown error' 
      };
    }
  }

  async getStatus(_event: Electron.IpcMainInvokeEvent): Promise<{ isTracking: boolean; sessionId?: string; startTime?: string }> {
    try {
      if (!this.pythonBackend.isRunning()) {
        return { isTracking: false };
      }

      if (!this.isTracking || !this.currentSessionId) {
        // Check with the Python API if there's an active session
        const response = await axios.get(
          `${this.pythonBackend.getApiBaseUrl()}/time-entries/active`
        );

        if (response.status === 200 && response.data.active_session) {
          this.isTracking = true;
          this.currentSessionId = response.data.session_id;
          return {
            isTracking: true,
            sessionId: this.currentSessionId,
            startTime: response.data.start_time
          };
        } else {
          return { isTracking: false };
        }
      }

      return {
        isTracking: this.isTracking,
        sessionId: this.currentSessionId
      };
    } catch (error) {
      console.error('Error getting time tracking status:', error);
      return { isTracking: false };
    }
  }
}
