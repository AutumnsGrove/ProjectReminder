#!/usr/bin/env python3
"""
Development Server Launcher
Starts both FastAPI backend and UI server with proper initialization.

Usage:
    python run_dev.py           # Start both servers
    python run_dev.py --init    # Force reinitialize database
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_colored(message, color):
    """Print colored message to terminal"""
    print(f"{color}{message}{RESET}")

def check_secrets():
    """Check if secrets.json is configured"""
    secrets_path = Path(__file__).parent / "secrets.json"
    if not secrets_path.exists():
        print_colored("\n❌ ERROR: secrets.json not found!", RED)
        print(f"   Copy secrets_template.json to secrets.json and configure your API keys:")
        print(f"   cp secrets_template.json secrets.json")
        print(f"\n   Required keys:")
        print(f"   - mapbox_access_token (get from https://account.mapbox.com/)")
        print(f"   - api_token (generate a strong random token)\n")
        return False
    return True

def init_database(force=False):
    """Initialize the database"""
    print_colored("\n🗄️  Initializing database...", BLUE)
    try:
        cmd = ["uv", "run", "python", "-m", "server.database"]
        if force:
            cmd.append("--force")

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Database initialization failed: {e}", RED)
        print(e.stderr)
        return False

def main():
    """Main launcher"""
    print_colored(f"\n{'='*60}", BLUE)
    print_colored("🎤 ADHD-Friendly Reminders System - Development Server", BOLD)
    print_colored(f"{'='*60}\n", BLUE)

    # Check for force init flag
    force_init = "--init" in sys.argv

    # Step 1: Check secrets
    if not check_secrets():
        sys.exit(1)

    # Step 2: Initialize database
    db_path = Path(__file__).parent / "reminders.db"
    if not db_path.exists() or db_path.stat().st_size == 0 or force_init:
        if not init_database(force=force_init):
            sys.exit(1)
    else:
        print_colored("✅ Database already initialized", GREEN)

    # Step 3: Start servers
    print_colored("\n🚀 Starting servers...\n", BLUE)

    processes = []

    try:
        # Start backend (FastAPI)
        print_colored("   Starting FastAPI backend on http://localhost:8000", YELLOW)
        backend_process = subprocess.Popen(
            ["uv", "run", "uvicorn", "server.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(backend_process)

        # Give backend time to start
        time.sleep(2)

        # Start frontend (simple HTTP server)
        print_colored("   Starting UI server on http://localhost:3077", YELLOW)
        frontend_process = subprocess.Popen(
            ["python", "serve_ui.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(frontend_process)

        # Wait for frontend to start
        time.sleep(1)

        # Success message
        print_colored(f"\n{'='*60}", GREEN)
        print_colored("✅ Servers running!", BOLD)
        print_colored(f"{'='*60}", GREEN)
        print_colored("\n📱 Open in your browser:", BOLD)
        print_colored(f"   🌐 UI:       http://localhost:3077", BLUE)
        print_colored(f"   📚 API Docs: http://localhost:8000/docs", BLUE)
        print_colored(f"   ❤️  Health:   http://localhost:8000/api/health", BLUE)
        print_colored("\n⌨️  Press Ctrl+C to stop both servers\n", YELLOW)

        # Keep running and show backend logs
        while True:
            line = backend_process.stdout.readline()
            if line:
                print(line.strip())
            if backend_process.poll() is not None:
                break

    except KeyboardInterrupt:
        print_colored("\n\n🛑 Stopping servers...", YELLOW)
    finally:
        # Cleanup: kill all processes
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()

        print_colored("✅ All servers stopped. Goodbye!\n", GREEN)

if __name__ == "__main__":
    main()
