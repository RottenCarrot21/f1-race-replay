#!/usr/bin/env python3
"""
F1 3D Engine Migration Script
This script demonstrates the migration from Arcade to 3D OpenGL rendering
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from engine3d.examples.f1_3d_demo import run_basic_3d_demo, run_lighting_demo, run_performance_demo


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    F1 3D Engine Migration                   ║
║                  Arcade → OpenGL/ModernGL                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  The 3D engine provides:                                     ║
║  • Advanced lighting models (Phong, PBR)                    ║
║  • Shader support for custom effects                        ║
║  • Camera system with smooth transitions                    ║
║  • Depth testing and proper Z-ordering                     ║
║  • Batch rendering for performance                          ║
║  • Migration compatibility layer                            ║
║                                                              ║
║  Choose a demo to run:                                       ║
║  1. Basic 3D Scene (F1 cars on track)                       ║
║  2. Lighting Demo (Phong/PBR models)                        ║
║  3. Performance Demo (Batch rendering)                      ║
║  4. Exit                                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    while True:
        try:
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == '1':
                print("\\nStarting F1 3D Basic Demo...")
                print("Controls: SPACE (pause), MOUSE (orbit), SCROLL (zoom)")
                run_basic_3d_demo()
                break
                
            elif choice == '2':
                print("\\nStarting 3D Lighting Demo...")
                print("Demonstrating Phong lighting with different light types")
                run_lighting_demo()
                break
                
            elif choice == '3':
                print("\\nStarting 3D Performance Demo...")
                print("Rendering hundreds of objects with instanced rendering")
                run_performance_demo()
                break
                
            elif choice == '4':
                print("Exiting...")
                break
                
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")
                
        except KeyboardInterrupt:
            print("\\n\\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("Make sure all dependencies are installed:")
            print("  pip install -r requirements.txt")


def check_dependencies():
    """Check if required dependencies are installed"""
    required_modules = [
        'moderngl',
        'pyglet',
        'numpy',
        'arcade'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("Missing required modules:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\\nPlease install them with:")
        print("  pip install -r requirements.txt")
        return False
    
    return True


if __name__ == "__main__":
    print("F1 3D Engine Migration Tool")
    print("=" * 40)
    
    if check_dependencies():
        main()
    else:
        sys.exit(1)