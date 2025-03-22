"""
Platform-specific utility functions for the Time Tracker application.
"""
import os
import sys
import platform
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Setup logger
logger = logging.getLogger(__name__)

def get_active_window_info() -> Dict[str, Any]:
    """
    Get information about the currently active window.
    
    This function uses platform-specific implementations to get the active window
    information, including window title, process name, and executable path.
    
    Returns:
        dict: Information about the active window, including:
            - window_title: Title of the active window
            - process_name: Name of the process
            - executable_path: Path to the executable
            - timestamp: Current timestamp in ISO format
    """
    system = platform.system()
    
    try:
        if system == 'Windows':
            return _get_active_window_windows()
        elif system == 'Darwin':  # macOS
            return _get_active_window_macos()
        elif system == 'Linux':
            return _get_active_window_linux()
        else:
            logger.warning(f"Unsupported platform: {system}")
            return {
                'window_title': 'Unknown',
                'process_name': 'Unknown',
                'executable_path': '',
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting active window info: {str(e)}")
        return {
            'window_title': 'Error',
            'process_name': 'Error',
            'executable_path': '',
            'timestamp': datetime.now().isoformat()
        }

def _get_active_window_windows() -> Dict[str, Any]:
    """
    Get active window information on Windows.
    
    Returns:
        dict: Active window information
    """
    try:
        import win32gui
        import win32process
        import psutil
        
        # Get handle of the active window
        hwnd = win32gui.GetForegroundWindow()
        
        # Get window title
        window_title = win32gui.GetWindowText(hwnd)
        
        # Get process ID and thread ID
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        
        # Get process information
        try:
            process = psutil.Process(pid)
            process_name = process.name()
            executable_path = process.exe()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            process_name = "Unknown"
            executable_path = ""
        
        return {
            'window_title': window_title,
            'process_name': process_name,
            'executable_path': executable_path,
            'pid': pid,
            'timestamp': datetime.now().isoformat()
        }
    except ImportError as e:
        logger.error(f"Required module not found: {str(e)}")
        logger.error("Make sure pywin32 and psutil are installed on Windows")
        raise
    except Exception as e:
        logger.error(f"Error getting Windows active window: {str(e)}")
        raise

def _get_active_window_macos() -> Dict[str, Any]:
    """
    Get active window information on macOS.
    
    Returns:
        dict: Active window information
    """
    try:
        # Try to import AppKit
        # This is the preferred method on macOS
        from AppKit import NSWorkspace
        
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.activeApplication()
        
        window_title = active_app['NSApplicationName']
        process_name = window_title  # On macOS, these are often the same
        executable_path = active_app['NSApplicationPath']
        pid = active_app['NSApplicationProcessIdentifier']
        
        # Try to get more detailed information with psutil
        try:
            import psutil
            process = psutil.Process(pid)
            process_name = process.name()
        except (ImportError, psutil.NoSuchProcess, psutil.AccessDenied):
            pass  # Fall back to the basic info
        
        return {
            'window_title': window_title,
            'process_name': process_name,
            'executable_path': executable_path,
            'pid': pid,
            'timestamp': datetime.now().isoformat()
        }
    except ImportError:
        logger.error("Required module not found: AppKit")
        logger.error("Make sure pyobjc-framework-Cocoa is installed on macOS")
        
        # Fall back to using applescript if AppKit is not available
        try:
            import subprocess
            
            # Use applescript to get active application
            cmd = ['osascript', '-e', 'tell application "System Events" to set frontApp to name of first application process whose frontmost is true']
            app_name = subprocess.check_output(cmd).decode().strip()
            
            return {
                'window_title': app_name,
                'process_name': app_name,
                'executable_path': '',  # Can't easily get this with applescript
                'pid': 0,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting macOS active window with fallback: {str(e)}")
            raise
    except Exception as e:
        logger.error(f"Error getting macOS active window: {str(e)}")
        raise

def _get_active_window_linux() -> Dict[str, Any]:
    """
    Get active window information on Linux.
    
    Returns:
        dict: Active window information
    """
    try:
        # Try to use xdotool (common on many Linux distributions)
        import subprocess
        import psutil
        
        # Get window ID of active window
        try:
            window_id = subprocess.check_output(['xdotool', 'getactivewindow']).decode().strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("Error using xdotool. Make sure it is installed.")
            return {
                'window_title': 'Unknown',
                'process_name': 'Unknown',
                'executable_path': '',
                'timestamp': datetime.now().isoformat()
            }
        
        # Get window name
        try:
            window_title = subprocess.check_output(['xdotool', 'getwindowname', window_id]).decode().strip()
        except subprocess.SubprocessError:
            window_title = 'Unknown'
        
        # Get window PID
        try:
            pid = int(subprocess.check_output(['xdotool', 'getwindowpid', window_id]).decode().strip())
        except subprocess.SubprocessError:
            pid = None
        
        # Get process information if PID is available
        process_name = 'Unknown'
        executable_path = ''
        
        if pid:
            try:
                process = psutil.Process(pid)
                process_name = process.name()
                executable_path = process.exe()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        return {
            'window_title': window_title,
            'process_name': process_name,
            'executable_path': executable_path,
            'pid': pid,
            'timestamp': datetime.now().isoformat()
        }
    except ImportError:
        logger.error("Required module not found: psutil")
        logger.error("Make sure psutil is installed on Linux")
        raise
    except Exception as e:
        logger.error(f"Error getting Linux active window: {str(e)}")
        raise

def get_system_info() -> Dict[str, Any]:
    """
    Get system information.
    
    Returns:
        dict: System information, including:
            - system: Operating system name
            - node: Computer name
            - release: OS release
            - version: OS version
            - machine: Machine hardware
            - processor: Processor type
            - python_version: Python version
    """
    try:
        import psutil
        
        # Get memory information
        memory = psutil.virtual_memory()
        
        # Get disk information
        disk = psutil.disk_usage('/')
        
        return {
            'system': platform.system(),
            'node': platform.node(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'memory_total': memory.total,
            'memory_available': memory.available,
            'disk_total': disk.total,
            'disk_free': disk.free,
            'timestamp': datetime.now().isoformat()
        }
    except ImportError:
        logger.error("Required module not found: psutil")
        
        # Return basic information without psutil
        return {
            'system': platform.system(),
            'node': platform.node(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return {
            'system': platform.system(),
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_system_metrics() -> Dict[str, Any]:
    """
    Get current system metrics.
    
    Returns:
        dict: System metrics, including:
            - cpu_percent: CPU usage percentage
            - memory_percent: Memory usage percentage
            - battery_percent: Battery percentage (if available)
            - battery_charging: Whether the battery is charging (if available)
            - timestamp: Current timestamp in ISO format
    """
    try:
        import psutil
        
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Get battery information
        battery_percent = None
        battery_charging = None
        
        if hasattr(psutil, 'sensors_battery'):
            battery = psutil.sensors_battery()
            if battery:
                battery_percent = battery.percent
                battery_charging = battery.power_plugged
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'battery_percent': battery_percent,
            'battery_charging': battery_charging,
            'timestamp': datetime.now().isoformat()
        }
    except ImportError:
        logger.error("Required module not found: psutil")
        return {
            'cpu_percent': 0,
            'memory_percent': 0,
            'battery_percent': None,
            'battery_charging': None,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}")
        return {
            'cpu_percent': 0,
            'memory_percent': 0,
            'battery_percent': None,
            'battery_charging': None,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_idle_time() -> float:
    """
    Get the number of seconds the system has been idle.
    
    This function uses platform-specific implementations to get the idle time.
    
    Returns:
        float: Idle time in seconds
    """
    system = platform.system()
    
    try:
        if system == 'Windows':
            return _get_idle_time_windows()
        elif system == 'Darwin':  # macOS
            return _get_idle_time_macos()
        elif system == 'Linux':
            return _get_idle_time_linux()
        else:
            logger.warning(f"Unsupported platform for idle time: {system}")
            return 0
    except Exception as e:
        logger.error(f"Error getting idle time: {str(e)}")
        return 0

def _get_idle_time_windows() -> float:
    """
    Get idle time on Windows.
    
    Returns:
        float: Idle time in seconds
    """
    try:
        import ctypes
        
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [
                ('cbSize', ctypes.c_uint),
                ('dwTime', ctypes.c_uint)
            ]
        
        lastInputInfo = LASTINPUTINFO()
        lastInputInfo.cbSize = ctypes.sizeof(lastInputInfo)
        
        # Get last input time
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo))
        
        # Get tick count
        millis = ctypes.windll.kernel32.GetTickCount()
        
        # Calculate idle time
        return (millis - lastInputInfo.dwTime) / 1000.0
    except ImportError:
        logger.error("Required module not found: ctypes")
        return 0
    except Exception as e:
        logger.error(f"Error getting Windows idle time: {str(e)}")
        return 0

def _get_idle_time_macos() -> float:
    """
    Get idle time on macOS.
    
    Returns:
        float: Idle time in seconds
    """
    try:
        import subprocess
        
        # Use ioreg to get the HIDIdleTime
        cmd = ['ioreg', '-c', 'IOHIDSystem', '|', 'grep', 'HIDIdleTime']
        output = subprocess.check_output(['bash', '-c', ' '.join(cmd)]).decode().strip()
        
        # Extract the idle time value
        idle_time_ns = int(output.split('=')[-1].strip())
        
        # Convert from nanoseconds to seconds
        return idle_time_ns / 1000000000.0
    except subprocess.SubprocessError:
        logger.error("Error running ioreg command on macOS")
        return 0
    except Exception as e:
        logger.error(f"Error getting macOS idle time: {str(e)}")
        return 0

def _get_idle_time_linux() -> float:
    """
    Get idle time on Linux.
    
    Returns:
        float: Idle time in seconds
    """
    try:
        import subprocess
        
        # Try using xprintidle if available (common on many Linux distributions)
        try:
            idle_time_ms = int(subprocess.check_output(['xprintidle']).decode().strip())
            return idle_time_ms / 1000.0
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("xprintidle not available, trying xssstate")
            
            # Try using xssstate as an alternative
            try:
                idle_time_ms = int(subprocess.check_output(['xssstate', '-i']).decode().strip())
                return idle_time_ms / 1000.0
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("xssstate not available, idle time detection not supported")
                return 0
    except Exception as e:
        logger.error(f"Error getting Linux idle time: {str(e)}")
        return 0

def get_app_data_dir() -> str:
    """
    Get the application data directory based on the platform.
    
    Returns:
        str: The application data directory path
    """
    system = platform.system()
    
    if system == 'Windows':
        app_data = os.environ.get('APPDATA')
        return os.path.join(app_data, 'TimeTracker')
    elif system == 'Darwin':  # macOS
        return os.path.expanduser('~/Library/Application Support/TimeTracker')
    elif system == 'Linux':
        return os.path.expanduser('~/.timetracker')
    else:
        return os.path.expanduser('~/.timetracker')
