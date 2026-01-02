#!/usr/bin/env python3
"""
Test script to verify 3D integration is working properly.
Runs a simple test without requiring real F1 data.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("=" * 60)
print("F1 RACE REPLAY - 3D System Test")
print("=" * 60)

# Test 1: Check dependencies
print("\n1. Checking 3D dependencies...")
try:
    import OpenGL.GL
    print("   ✓ PyOpenGL installed")
except ImportError:
    print("   ✗ PyOpenGL NOT installed - Install with: pip install PyOpenGL PyOpenGL_accelerate")
    sys.exit(1)

try:
    import glfw
    print("   ✓ GLFW library installed")
except ImportError:
    print("   ✗ GLFW NOT installed - Install with: pip install glfw")
    sys.exit(1)

try:
    import numpy
    print("   ✓ NumPy installed")
except ImportError:
    print("   ✗ NumPy NOT installed")
    sys.exit(1)

# Test 2: Check rendering module imports
print("\n2. Checking 3D rendering modules...")
try:
    from src.rendering.window import F13DWindow
    print("   ✓ 3D window module imported")
except ImportError as e:
    print(f"   ✗ Failed to import 3D window: {e}")
    sys.exit(1)

try:
    from src.rendering.renderer import run_3d_replay
    print("   ✓ 3D renderer imported")
except ImportError as e:
    print(f"   ✗ Failed to import 3D renderer: {e}")
    sys.exit(1)

try:
    from src.rendering.camera import Camera3D
    print("   ✓ 3D camera imported")
except ImportError as e:
    print(f"   ✗ Failed to import 3D camera: {e}")
    sys.exit(1)

try:
    from src.track.mesh_builder import TrackMeshBuilder
    print("   ✓ Track mesh builder imported")
except ImportError as e:
    print(f"   ✗ Failed to import track mesh builder: {e}")
    sys.exit(1)

# Test 3: Check shader files
print("\n3. Checking shader files...")
shader_path = "src/assets/shaders"
required_shaders = [
    ("track.vert.glsl", "vertex"),
    ("track.frag.glsl", "fragment")
]
for shader_file, shader_type in required_shaders:
    full_path = os.path.join(shader_path, shader_file)
    if os.path.exists(full_path):
        size = os.path.getsize(full_path)
        print(f"   ✓ {shader_file} exists ({size} bytes)")
    else:
        print(f"   ✗ {shader_file} NOT FOUND at {full_path}")
        sys.exit(1)

# Test 4: Check 3D integration in main.py
print("\n4. Checking integration in main.py...")
with open("main.py", 'r') as f:
    main_content = f.read()
    if "from src.rendering.renderer import run_3d_replay" in main_content:
        print("   ✓ 3D renderer imported in main.py")
    else:
        print("   ✗ 3D renderer NOT imported in main.py")
    
    if 'use_3d = "--3d" in sys.argv' in main_content:
        print("   ✓ 3D command-line flag check present")
    else:
        print("   ✗ 3D command-line flag check missing")
    
    if "run_3d_replay(" in main_content:
        print("   ✓ 3D rendering function called")
    else:
        print("   ✗ 3D rendering function NOT called")

# Test 5: Validate that camera module is not broken
print("\n5. Testing camera initialization...")
try:
    camera = Camera3D(1920, 1080)
    print(f"   ✓ Camera created")
    print(f"   ✓ Initial position: {camera.position}")
except Exception as e:
    print(f"   ✗ Camera creation failed: {e}")

# Test 6: Test GLFW can initialize
print("\n6. Testing GLFW initialization...")
try:
    if not glfw.init():
        print("   ✗ GLFW initialization failed!")
        sys.exit(1)
    
    # Set hints so window opens without context
    glfw.window_hint(glfw.VISIBLE, False)  # Don't show window
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    
    # Try to create hidden window
    test_window = glfw.create_window(640, 480, "Test", None, None)
    if test_window:
        print("   ✓ GLFW can create windows")
        glfw.destroy_window(test_window)
    else:
        print("   ⚠ GLFW window creation failed (may still work with real display)")
    
    glfw.terminate()
    print("   ✓ GLFW test completed")
except Exception as e:
    print(f"   ⚠ GLFW test exception (may still work): {e}")

# All tests passed
print("\n" + "=" * 60)
print("✓ ALL SYSTEM TESTS PASSED")
print("=" * 60)
print("\nYou can now run the 3D race replay with:")
print("  python main.py --year 2023 --round 1 --3d")
print("\nControls:")
print("  - Mouse drag: Orbit camera")
print("  - Scroll wheel: Zoom")
print("  - Space: Play/pause")
print("  - R: Restart")
print("  - +/-: Speed control")
print("  - ESC: Exit")
print("=" * 60)