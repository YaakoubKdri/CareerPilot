#!/usr/bin/env python3
"""Run both backend and frontend servers"""

import subprocess
import sys
import os
import time

def run_command(cmd, name):
    """Run a command in a subprocess"""
    print(f"Starting {name}...")
    proc = subprocess.Popen(cmd, shell=True)
    return proc

if __name__ == "__main__":
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Prefer the project venv Python if present (ensures Python 3.12 env is used)
    venv_py = os.path.join(script_dir, ".venv", "Scripts", "python.exe")
    py_cmd = f'"{venv_py}"' if os.path.exists(venv_py) else "py"

    # Start backend
    # Use module execution so it works even when the uvicorn entrypoint isn't on PATH
    backend_cmd = f"cd backend && {py_cmd} -m uvicorn main:app --reload --port 8000"
    backend_proc = run_command(backend_cmd, "Backend (FastAPI)")

    # Wait a moment for backend to start
    time.sleep(2)

    # Start frontend
    frontend_dir = os.path.join(script_dir, "frontend")
    frontend_cmd = f'cd "{frontend_dir}" && {py_cmd} -m http.server 3000'
    frontend_proc = run_command(frontend_cmd, "Frontend (HTTP Server)")

    print("\n" + "="*50)
    print("CareerPilot is running!")
    print("Backend API:  http://localhost:8000")
    print("Frontend UI:  http://localhost:3000")
    print("="*50 + "\n")

    try:
        # Keep running until Ctrl+C
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(0)