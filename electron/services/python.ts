import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import { app } from 'electron';

export class PythonBackendService {
  private process: ChildProcess | null = null;
  private isReady: boolean = false;
  private port: number = 8000;
  private apiBaseUrl: string = 'http://localhost:8000';

  constructor() {}

  async start(): Promise<void> {
    if (this.process) {
      console.log('Python backend already running');
      return;
    }

    const pythonPath = this.getPythonPath();
    const scriptPath = this.getScriptPath();
    
    console.log(`Starting Python backend with path: ${pythonPath}`);
    console.log(`Script path: ${scriptPath}`);

    return new Promise<void>((resolve, reject) => {
      try {
        this.process = spawn(pythonPath, ['-m', 'api.main'], {
          cwd: scriptPath,
          stdio: ['pipe', 'pipe', 'pipe'],
          env: { ...process.env, ELECTRON_RUN: '1' }
        });

        this.process.stdout?.on('data', (data: Buffer) => {
          const message = data.toString();
          console.log(`Python stdout: ${message}`);

          if (message.includes('Time Tracker API started successfully') || 
              message.includes('Application startup complete')) {
            this.isReady = true;
            resolve();
          }
        });

        this.process.stderr?.on('data', (data: Buffer) => {
          const message = data.toString();
          console.error(`Python stderr: ${message}`);
        });

        this.process.on('error', (err: Error) => {
          console.error('Failed to start Python process:', err);
          reject(err);
        });

        this.process.on('exit', (code: number | null) => {
          console.log(`Python process exited with code ${code}`);
          this.process = null;
          this.isReady = false;
        });

        // Timeout if Python doesn't start in 10 seconds
        setTimeout(() => {
          if (!this.isReady) {
            const error = new Error('Python backend failed to start in time');
            console.error(error);
            reject(error);
          }
        }, 10000);
      } catch (err) {
        console.error('Error starting Python backend:', err);
        reject(err);
      }
    });
  }

  async stop(): Promise<void> {
    return new Promise<void>((resolve) => {
      if (!this.process) {
        resolve();
        return;
      }

      this.isReady = false;

      if (process.platform === 'win32') {
        // Windows requires taskkill to kill the process tree
        spawn('taskkill', ['/pid', this.process.pid!.toString(), '/f', '/t']);
      } else {
        // Unix-like systems can use kill signal
        this.process.kill('SIGTERM');
      }

      // Give process time to exit gracefully
      setTimeout(() => {
        if (this.process) {
          try {
            // Force kill if still running
            this.process.kill('SIGKILL');
          } catch (e) {
            // Process might already be gone
          }
          this.process = null;
        }
        resolve();
      }, 3000);
    });
  }

  isRunning(): boolean {
    return this.process !== null && this.isReady;
  }

  getApiBaseUrl(): string {
    return this.apiBaseUrl;
  }

  private getPythonPath(): string {
    if (process.env.NODE_ENV === 'development') {
      // Use system Python in development
      return process.platform === 'win32' ? 'python' : 'python3';
    } else {
      // Use bundled Python in production
      const pythonBinName = process.platform === 'win32' ? 'python.exe' : 'python';
      return path.join(process.resourcesPath, 'python', pythonBinName);
    }
  }

  private getScriptPath(): string {
    if (process.env.NODE_ENV === 'development') {
      // In development, use the local python directory
      return path.join(app.getAppPath(), 'python');
    } else {
      // In production, use the bundled python directory
      return path.join(process.resourcesPath, 'python');
    }
  }
}
