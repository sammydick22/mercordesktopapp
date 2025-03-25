const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const findProcess = require('find-process');

let mainWindow;
let pythonProcess;
let nextProcess;

// Find and kill any existing processes on our ports
async function killExistingProcesses() {
  try {
    const port8000Processes = await findProcess('port', 8000);
    const port3000Processes = await findProcess('port', 3000);
    
    [...port8000Processes, ...port3000Processes].forEach(proc => {
      console.log(`Killing process ${proc.name} (PID: ${proc.pid}) on port ${proc.port}`);
      try {
        process.kill(proc.pid, 'SIGTERM');
      } catch (e) {
        console.error(`Failed to kill process ${proc.pid}:`, e);
      }
    });
  } catch (e) {
    console.error('Error killing existing processes:', e);
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  // Wait a bit for servers to start before loading the URL
  setTimeout(() => {
    mainWindow.loadURL('http://localhost:3000');
    // Optional: Open DevTools automatically (comment out for production)
    // mainWindow.webContents.openDevTools();
  }, 5000);

  mainWindow.on('closed', function() {
    mainWindow = null;
  });
}

async function startApp() {
  // Kill any existing processes that might block our ports
  await killExistingProcesses();
  
  // Start Python backend (using direct path to Python executable)
  const pythonPath = path.join(__dirname, '..', 'python');
  
  // For Windows, directly use the Python executable from venv
  if (process.platform === 'win32') {
    const pythonExecutable = path.join(pythonPath, 'venv', 'Scripts', 'python.exe');
    console.log(`Starting Python backend with: ${pythonExecutable}`);
    
    pythonProcess = spawn(pythonExecutable, ['-m', 'uvicorn', 'api.main:app', '--reload'], {
      cwd: pythonPath,
      shell: true
    });
  } else {
    // For Mac/Linux
    const pythonExecutable = path.join(pythonPath, 'venv', 'bin', 'python');
    pythonProcess = spawn(pythonExecutable, ['-m', 'uvicorn', 'api.main:app', '--reload'], {
      cwd: pythonPath,
      shell: true
    });
  }
  
  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python: ${data}`);
  });
  
  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python error: ${data}`);
  });
  
  // Start Next.js frontend
  const frontendPath = path.join(__dirname, '..', 'frontend');
  nextProcess = spawn('npm', ['run', 'start'], {
    cwd: frontendPath,
    shell: true
  });
  
  nextProcess.stdout.on('data', (data) => {
    console.log(`Next.js: ${data}`);
  });
  
  nextProcess.stderr.on('data', (data) => {
    console.error(`Next.js error: ${data}`);
  });
  
  createWindow();
}

app.on('ready', startApp);

app.on('window-all-closed', function() {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', function() {
  if (mainWindow === null) {
    createWindow();
  }
});

// Clean up child processes before exit
app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  
  if (nextProcess) {
    nextProcess.kill();
  }
});
