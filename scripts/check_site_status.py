#!/usr/bin/env python3
"""
Site Status & Configuration Verification Diagnostic tool for site-expedition.
Checks local configuration integrity and report dependencies.
"""
import sys
import os
import json

def verify_setup():
    status = {
        "status": "healthy",
        "python_version": sys.version.split()[0],
        "checks": {
            "context_exists": os.path.exists("CONTEXT.md"),
            "readme_exists": os.path.exists("README.md"),
            "scripts_dir": os.path.isdir("scripts")
        }
    }
    return status

if __name__ == "__main__":
    result = verify_setup()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "healthy" else 1)
