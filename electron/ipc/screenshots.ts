import { BrowserWindow, desktopCapturer, screen } from 'electron';
import * as path from 'path';
import * as fs from 'fs';
import axios from 'axios';
import { PythonBackendService } from '../services/python';

export class ScreenshotHandler {
  private mainWindow: BrowserWindow;
  private pythonBackend: PythonBackendService;

  constructor(mainWindow: BrowserWindow, pythonBackend: PythonBackendService) {
    this.mainWindow = mainWindow;
    this.pythonBackend = pythonBackend;
  }

  async capture(): Promise<{ success: boolean; message?: string; screenshotId?: string; screenshotUrl?: string }> {
    try {
      if (!this.pythonBackend.isRunning()) {
        return { success: false, message: 'Python backend is not running' };
      }

      // Capture the screenshot
      const screenshot = await this.captureScreen();
      if (!screenshot) {
        return { success: false, message: 'Failed to capture screenshot' };
      }

      // Convert base64 string to buffer
      const imageBuffer = Buffer.from(screenshot.replace(/^data:image\/\w+;base64,/, ''), 'base64');

      // Create form data for the API request
      const formData = new FormData();
      
      // Create a Blob from the buffer
      const blob = new Blob([imageBuffer], { type: 'image/png' });
      formData.append('file', blob, 'screenshot.png');

      // Send the screenshot to the Python API
      const response = await axios.post(
        `${this.pythonBackend.getApiBaseUrl()}/screenshots/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      if (response.status === 200 && response.data.success) {
        // Notify renderer process that a screenshot was captured
        this.mainWindow.webContents.send('screenshots:captured', {
          screenshotId: response.data.screenshot_id,
          timestamp: new Date().toISOString()
        });
        
        return { 
          success: true, 
          screenshotId: response.data.screenshot_id,
          screenshotUrl: response.data.screenshot_url
        };
      } else {
        return { 
          success: false, 
          message: response.data.message || 'Failed to upload screenshot' 
        };
      }
    } catch (error) {
      console.error('Error capturing screenshot:', error);
      return { 
        success: false, 
        message: error instanceof Error ? error.message : 'Unknown error' 
      };
    }
  }

  async getRecent(_event: Electron.IpcMainInvokeEvent, limit: number = 10): Promise<{ success: boolean; message?: string; screenshots?: any[] }> {
    try {
      if (!this.pythonBackend.isRunning()) {
        return { success: false, message: 'Python backend is not running' };
      }

      // Get recent screenshots from the Python API
      const response = await axios.get(
        `${this.pythonBackend.getApiBaseUrl()}/screenshots/recent`,
        { params: { limit } }
      );

      if (response.status === 200) {
        return { 
          success: true, 
          screenshots: response.data.screenshots || []
        };
      } else {
        return { 
          success: false, 
          message: response.data.message || 'Failed to get recent screenshots' 
        };
      }
    } catch (error) {
      console.error('Error getting recent screenshots:', error);
      return { 
        success: false, 
        message: error instanceof Error ? error.message : 'Unknown error' 
      };
    }
  }

  private async captureScreen(): Promise<string | null> {
    try {
      // Get the primary display dimensions
      const primaryDisplay = screen.getPrimaryDisplay();
      const { width, height } = primaryDisplay.size;

      // Capture the screen
      const sources = await desktopCapturer.getSources({
        types: ['screen'],
        thumbnailSize: { width, height }
      });

      // Get the first source which is the entire screen
      const source = sources[0];
      if (!source) {
        console.error('No screen capture source found');
        return null;
      }

      // Return the thumbnail as a data URL (base64 encoded)
      return source.thumbnail.toDataURL();
    } catch (error) {
      console.error('Error capturing screen:', error);
      return null;
    }
  }
}
