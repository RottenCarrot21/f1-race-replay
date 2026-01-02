#!/usr/bin/env python3
"""Debug script to check why 3D mode might not be working."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing 3D mode detection...")
print(f"Command line args: {sys.argv}")

# Mock sys.argv to include --3d
test_argv = ["main.py", "--year", "2023", "--round", "1", "--3d"]
original_argv = sys.argv
sys.argv = test_argv

# Now test the 3d detection logic
use_3d = "--3d" in sys.argv
print(f"--3d flag detected: {use_3d}")

# Put original argv back
sys.argv = original_argv

# Try to import the rendering modules
print("\nImporting 3D rendering modules...")
try:
    from src.rendering.renderer import run_3d_replay
    print("✓ Successfully imported run_3d_replay")
except ImportError as e:
    print(f"✗ Failed to import run_3d_replay: {e}")
    import traceback
    traceback.print_exc()

try:
    from src.rendering.window import create_3d_window
    print("✓ Successfully imported create_3d_window")
except ImportError as e:
    print(f"✗ Failed to import create_3d_window: {e}")
    import traceback
    traceback.print_exc()

print("\nChecking if 3d module can be accessed from main...")
try:
    # Try what main.py does
    from src.rendering.renderer import run_3d_replay
    print("✓ run_3d_replay is accessible")
except ImportError as e:
    print(f"✗ run_3d_replay is NOT accessible: {e}")

print("\nTesting 3d window creation (basic test)...")
try:
    from src.rendering.window import create_3d_window
    # We won't actually create a window, just see if the function exists
    print(f"✓ create_3d_window function exists: {callable(create_3d_window)}")
except Exception as e:
    print(f"✗ Error accessing create_3d_window: {e}")

print("\nVerifying main.py changes...")
with open("main.py", 'r') as f:
    content = f.read()
    if "from src.rendering.renderer import run_3d_replay" in content:
        print("✓ 3D import found in main.py")
    else:
        print("✗ 3D import NOT found in main.py")
    
    if "run_3d_replay(" in content:
        print("✓ 3D function call found in main.py")
    else:
        print("✗ 3D function call NOT found in main.py")
    
    if 'use_3d = "--3d" in sys.argv' in content:
        print("✓ 3D flag detection found in main.py")
    else:
        print("✗ 3D flag detection NOT found in main.py")

print("\n" + "="*60)
print("Debug complete!")
print("="*60)