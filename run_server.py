#!/usr/bin/env python3
"""
Development server runner for SCIM.Cloud
"""
import argparse
import sys
import os
import time
import signal
import uvicorn
from loguru import logger

# Ensure we're using the virtual environment
def ensure_venv():
    """Ensure we're running in the virtual environment"""
    venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'bin', 'python')
    if os.path.exists(venv_python):
        if sys.executable != venv_python:
            logger.warning(f"Not running in virtual environment. Expected: {venv_python}, Got: {sys.executable}")
            logger.info("Please run with: source .venv/bin/activate && python run_server.py")
            return False
    else:
        logger.warning("Virtual environment not found at .venv/bin/python")
        logger.info("Please create virtual environment with: python -m venv .venv")
        return False
    return True

# Check virtual environment before importing project modules
if not ensure_venv():
    sys.exit(1)

from scim_server.config import settings


def print_help():
    """Print detailed help information"""
    help_text = """
SCIM.Cloud Development Server Runner

This script starts the SCIM 2.0 development server for testing and integration purposes.

USAGE:
    python run_server.py [OPTIONS]

OPTIONS:
    -h, --help          Show this help message and exit
    -p, --port PORT     Specify port number (default: from config)
    -H, --host HOST     Specify host address (default: from config)
    -d, --daemon        Run server in background (daemon mode)
    --pid-file FILE     Specify PID file for daemon mode (default: /tmp/scim_server.pid)
    --reload            Enable auto-reload for development
    --no-reload         Disable auto-reload
    --log-level LEVEL   Set log level (debug, info, warning, error)
    --version           Show version information

EXAMPLES:
    # Start server with default settings
    python run_server.py

    # Start server in background (daemon mode)
    python run_server.py -d

    # Start daemon with custom PID file
    python run_server.py -d --pid-file /var/run/scim_server.pid

    # Start server on specific port
    python run_server.py --port 8080

    # Start server with auto-reload enabled
    python run_server.py --reload

    # Start server with debug logging
    python run_server.py --log-level debug

    # Start server on specific host and port
    python run_server.py --host 0.0.0.0 --port 9000

FEATURES:
    ✅ Multi-server support with virtual SCIM servers
    ✅ RFC 7644 compliant SCIM 2.0 endpoints
    ✅ Okta integration ready
    ✅ Enhanced Application Profiles System
    ✅ Comprehensive test coverage (163/163 tests)

ENDPOINTS:
    /scim-identifier/{server_id}/scim/v2/Users
    /scim-identifier/{server_id}/scim/v2/Groups
    /scim-identifier/{server_id}/scim/v2/Entitlements
    /scim-identifier/{server_id}/scim/v2/Roles
    /scim-identifier/{server_id}/scim/v2/ResourceTypes
    /scim-identifier/{server_id}/scim/v2/Schemas

AUTHENTICATION:
    Use Bearer token authentication with API keys:
    - default_api_key: For normal operations
    - test_api_key: For testing operations

DAEMON MODE:
    When using -d/--daemon, the server runs in the background:
    - PID file is created at /tmp/scim_server.pid (or custom location)
    - Server logs to /tmp/scim_server.log
    - Use 'kill $(cat /tmp/scim_server.pid)' to stop the daemon
    - Use 'ps aux | grep run_server.py' to check if daemon is running

For more information, see the README.md file.
"""
    print(help_text)


def daemonize(pid_file="/tmp/scim_server.pid", log_file="/tmp/scim_server.log"):
    """Daemonize the process"""
    # Store the original working directory
    original_cwd = os.getcwd()
    
    try:
        # First fork
        pid = os.fork()
        if pid > 0:
            # Parent process, exit
            sys.exit(0)
    except OSError as err:
        logger.error(f"Fork #1 failed: {err}")
        sys.exit(1)
    
    # Decouple from parent environment
    # Don't change to root directory - keep original working directory
    os.umask(0)
    os.setsid()
    
    try:
        # Second fork
        pid = os.fork()
        if pid > 0:
            # Parent process, exit
            sys.exit(0)
    except OSError as err:
        logger.error(f"Fork #2 failed: {err}")
        sys.exit(1)
    
    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    
    with open('/dev/null', 'r') as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    
    with open(log_file, 'a+') as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())
    
    # Write PID file
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    logger.info(f"Daemon started with PID {os.getpid()}")
    logger.info(f"PID file: {pid_file}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Working directory: {original_cwd}")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main function to parse arguments and start the server"""
    parser = argparse.ArgumentParser(
        description="SCIM.Cloud Development Server Runner",
        add_help=False  # We'll handle help manually for better formatting
    )
    
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show detailed help information"
    )
    
    parser.add_argument(
        "-p", "--port",
        type=int,
        help="Port number to run the server on"
    )
    
    parser.add_argument(
        "-H", "--host",
        type=str,
        help="Host address to bind to"
    )
    
    parser.add_argument(
        "-d", "--daemon",
        action="store_true",
        help="Run server in background (daemon mode)"
    )
    
    parser.add_argument(
        "--pid-file",
        type=str,
        default="/tmp/scim_server.pid",
        help="PID file for daemon mode"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        help="Set log level"
    )
    
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information"
    )
    
    args = parser.parse_args()
    
    # Handle help
    if args.help:
        print_help()
        sys.exit(0)
    
    # Handle version
    if args.version:
        print("SCIM.Cloud Development Server v1.0.0")
        print("Built with AI - Standards Compliant SCIM 2.0 Server")
        sys.exit(0)
    
    # Check if daemon is already running
    if args.daemon and os.path.exists(args.pid_file):
        with open(args.pid_file, 'r') as f:
            old_pid = f.read().strip()
        try:
            # Check if process is still running
            os.kill(int(old_pid), 0)
            logger.error(f"Daemon already running with PID {old_pid}")
            logger.error(f"Use 'kill {old_pid}' to stop it or remove {args.pid_file}")
            sys.exit(1)
        except (OSError, ValueError):
            # Process not running, remove stale PID file
            os.remove(args.pid_file)
    
    # Daemonize if requested
    if args.daemon:
        log_file = "/tmp/scim_server.log"
        daemonize(args.pid_file, log_file)
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    # Prepare server configuration
    server_config = {
        "app": "scim_server.main:app",
        "host": args.host or settings.host,
        "port": args.port or settings.port,
        "log_level": args.log_level or settings.log_level
    }
    
    # Handle reload configuration
    if args.reload:
        server_config["reload"] = True
    elif args.no_reload:
        server_config["reload"] = False
    else:
        # Disable reload in daemon mode to prevent directory scanning issues
        if args.daemon:
            server_config["reload"] = False
        else:
            server_config["reload"] = settings.reload
    
    # Display startup information
    if not args.daemon:
        logger.info("Starting SCIM.Cloud development server...")
        logger.info(f"Host: {server_config['host']}")
        logger.info(f"Port: {server_config['port']}")
        logger.info(f"Reload: {server_config['reload']}")
        logger.info(f"Log Level: {server_config['log_level']}")
        logger.info("")
        logger.info("Available endpoints:")
        logger.info("  /scim-identifier/{server_id}/scim/v2/Users")
        logger.info("  /scim-identifier/{server_id}/scim/v2/Groups")
        logger.info("  /scim-identifier/{server_id}/scim/v2/Entitlements")
        logger.info("  /scim-identifier/{server_id}/scim/v2/Roles")
        logger.info("  /scim-identifier/{server_id}/scim/v2/ResourceTypes")
        logger.info("  /scim-identifier/{server_id}/scim/v2/Schemas")
        logger.info("")
        logger.info("Use --help for more options")
        logger.info("")
    else:
        logger.info("SCIM.Cloud daemon started successfully")
        logger.info(f"Server running on {server_config['host']}:{server_config['port']}")
        logger.info(f"PID file: {args.pid_file}")
        logger.info(f"Log file: /tmp/scim_server.log")
        logger.info("Use 'kill $(cat /tmp/scim_server.pid)' to stop the daemon")
    
    # Start the server
    uvicorn.run(**server_config)


if __name__ == "__main__":
    main() 