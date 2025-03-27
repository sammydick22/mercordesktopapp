import { BrowserWindow } from 'electron';
import * as os from 'os';
import * as path from 'path';

export class SystemHandler {
  private mainWindow: BrowserWindow;

  constructor(mainWindow: BrowserWindow) {
    this.mainWindow = mainWindow;
  }

  async getSystemInfo(_event: Electron.IpcMainInvokeEvent): Promise<{
    platform: string;
    arch: string;
    hostname: string;
    totalMemory: number;
    freeMemory: number;
    cpus: os.CpuInfo[];
    userInfo: {
      username: string;
      homedir: string;
    };
    uptime: number;
    appVersion: string;
  }> {
    return {
      platform: process.platform,
      arch: process.arch,
      hostname: os.hostname(),
      totalMemory: os.totalmem(),
      freeMemory: os.freemem(),
      cpus: os.cpus(),
      userInfo: {
        username: os.userInfo().username,
        homedir: os.homedir()
      },
      uptime: os.uptime(),
      appVersion: process.env.npm_package_version || '1.0.0'
    };
  }
}
