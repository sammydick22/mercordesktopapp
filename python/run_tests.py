#!/usr/bin/env python
"""
Script to run tests with the correct Python path.
"""
import os
import sys
import asyncio

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Print Python path for debugging
print("Python path:")
for path in sys.path:
    print(f"  - {path}")

# Import and run test
from test_activity_tracking import main

if __name__ == "__main__":
    # Run the test
    print("\nRunning activity tracking tests...\n")
    asyncio.run(main())
