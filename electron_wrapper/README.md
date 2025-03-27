# TimeTracker Desktop App Wrapper

This is a simple Electron wrapper for the TimeTracker application that automates starting both the backend and frontend servers, then opens the app in an Electron window.

## Installation

1. Make sure you've already set up the Python backend and Next.js frontend properly
2. Install the Electron wrapper dependencies:

```bash
cd electron_wrapper
npm install
```

## Usage

To start the TimeTracker desktop app:

```bash
cd electron_wrapper
npm start
```

This will:
1. Kill any existing processes on ports 3000 and 8000
2. Start the Python backend with uvicorn
3. Start the Next.js frontend
4. Open the app in an Electron window

## Notes

- The app automatically kills any processes running on ports 3000 and 8000 before starting to avoid conflicts
- When you close the Electron window, it will automatically shut down both the backend and frontend servers
- If you need to debug, you can uncomment the line in main.js that opens the DevTools

## Configuration

If needed, you can adjust the paths to the Python backend and frontend in the `main.js` file. The default assumes:

- Python backend is in `../python` directory relative to the electron_wrapper
- Next.js frontend is in `../frontend` directory relative to the electron_wrapper
