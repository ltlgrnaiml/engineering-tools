#!/usr/bin/env python
"""Start Phoenix server on port 6006.

Windows-compatible launcher since env var syntax doesn't work in Procfile.
"""
import os
import sys

# Set port before importing phoenix
os.environ["PHOENIX_PORT"] = "6006"

# Import and run Phoenix server
from phoenix.server.main import main

if __name__ == "__main__":
    sys.argv = ["phoenix", "serve"]
    main()
