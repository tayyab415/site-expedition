#!/usr/bin/env python3
"""
Diagnostic utility to validate environment variables, port configurations,
and required directories for Mireye Site Expedition.
"""

import os
import sys

def check_env():
    print("=== Mireye Site Expedition Environment Check ===")
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    port = os.environ.get("PORT", "8080")
    bind_host = os.environ.get("EXPEDITION_BIND_HOST", "0.0.0.0")
    
    print(f"[✓] EXPEDITION_BIND_HOST: {bind_host}")
    print(f"[✓] PORT: {port}")
    
    required_dirs = ["expedition", "harness"]
    for d in required_dirs:
        path = os.path.join(project_root, d)
        if os.path.isdir(path):
            print(f"[✓] Directory verified: {d}/")
        else:
            print(f"[!] Warning: missing directory {d}/")

    print(f"[✓] Python version: {sys.version.split()[0]}")
    print("=== Environment Check Complete ===")

if __name__ == "__main__":
    check_env()
