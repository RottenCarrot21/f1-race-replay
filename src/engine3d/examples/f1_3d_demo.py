"""
Example F1 3D Engine Demo
Demonstrates the new 3D capabilities and migration path from Arcade
"""

import sys
import os
import numpy as np
import time
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.engine3d import Window3D, Camera3D, Renderer3D, SimpleRenderable
from src.engine3d.graphics import create_cube, create_plane, create_sphere, AmbientLight, DirectionalLight, PointLight
from src.f1_data import FPS


class F1_3D_Demo:
    """
    F1 3D Engine demonstration showing advanced 3D rendering capabilities
    """
    
    def __init__(self):
        # Create 3D window
        self.window = Window3D(
            width=1920, 
            height=1200, 
            title="F1 3D Engine Demo - Migration from Arcade"
        )
        
        # Initialize 3D scene
        self.setup_3d_scene()
        
        # F1-specific data (for demonstration)
        self.f1_data = self.generate_demo_f1_data()
        
        # Animation state
        self.animation_time = 0.0
        self.car_positions = []
        self.setup_f1_cars()
        
    def setup_3d_scene(self):
        """Setup a comprehensive 3D scene for F1 visualization"""
        # Get renderer from window
        self.renderer = self.window.renderer
        
        # Create track geometry (3D plane representing the circuit)
        track_mesh = create_plane(size=100.0)
        track = SimpleRenderable(
            mesh=track_mesh,
            color=(0.3, 0.3, 0.3, 1.0),  # Dark gray track
            position=(0, 0, 0),
            rotation=(0, 0, 0),
            scale=(20.0, 1.0, 10.0)  # Wide and long track
        )
        self.renderer.add_renderable(track)
        
        # Create some 3D objects to show lighting effects
        # Grandstand structures
        for i in range(5):
            stand_mesh = create_cube(size=2.0)
            stand = SimpleRenderable(
                mesh=stand_mesh,
                color=(0.8, 0.8, 0.9, 1.0),  # Light blue/white
                position=(-30 + i * 15, 0, 5),
                rotation=(0, 0, 0),
                scale=(1.0, 1.0, 2.5)  # Tall buildings
            )
            self.renderer.add_renderable(stand)
            
        # Create some spheres representing trees/objects around track
        for i in range(8):
            sphere_mesh = create_sphere(radius=1.5)
            sphere = SimpleRenderable(
                mesh=sphere_mesh,
                color=(0.2, 0.8, 0.2, 1.0),  # Green
                position=(25 * np.cos(i * np.pi / 4), 25 * np.sin(i * np.pi / 4), 1.5),
                rotation=(0, 0, 0),
                scale=(1.0, 1.0, 1.0)
            )
            self.renderer.add_renderable(sphere)
            
        # Setup advanced lighting
        self.setup_lighting()
        
        # Position camera for good view
        self.window.camera.move_to(
            position=(50, -50, 30),
            target=(0, 0, 0)
        )
        
    def setup_lighting(self):
        """Setup advanced lighting system"""
        # Clear default lights
        self.renderer.lights.clear()
        
        # Add ambient light
        ambient = AmbientLight(intensity=0.4, color=(1.0, 1.0, 1.0))
        self.renderer.lights.append(ambient)
        
        # Add main sun light
        sun = DirectionalLight(
            direction=(-0.3, -1.0, -0.5),
            intensity=1.2,
            color=(1.0, 1.0, 0.9)  # Slightly warm sunlight
        )
        self.renderer.lights.append(sun)
        
        # Add some colored lights for dramatic effect
        point1 = PointLight(
            position=(-20, 20, 15),
            intensity=3.0,
            color=(1.0, 0.3, 0.3),  # Red
            range=40.0
        )
        self.renderer.lights.append(point1)
        
        point2 = PointLight(
            position=(20, -20, 15),
            intensity=2.5,
            color=(0.3, 0.3, 1.0),  # Blue
            range=35.0
        )
        self.renderer.lights.append(point2)
        
    def setup_f1_cars(self):
        """Setup F1 car representations for animation"""
        car_mesh = create_cube(size=0.8)  # Simplified car shape
        
        # Create 6 F1 cars with team colors
        team_colors = [
            (1.0, 0.0, 0.0, 1.0),  # Red (Ferrari)
            (0.0, 0.0, 1.0, 1.0),  # Blue (McLaren)
            (1.0, 0.8, 0.0, 1.0),  # Yellow (Mercedes)
            (0.0, 1.0, 0.0, 1.0),  # Green (Alpine)
            (1.0, 0.0, 1.0, 1.0),  # Magenta (Red Bull)
            (1.0, 0.5, 0.0, 1.0),  # Orange (AlphaTauri)
        ]
        
        self.f1_cars = []
        for i, color in enumerate(team_colors):
            car = SimpleRenderable(
                mesh=car_mesh,
                color=color,
                position=(0, i * 3 - 7.5, 0.5),  # Staggered starting positions
                rotation=(0, 0, 0),
                scale=(2.0, 4.0, 1.0)  # Car-like proportions
            )
            self.renderer.add_renderable(car)
            self.f1_cars.append(car)
            
    def generate_demo_f1_data(self) -> Dict[str, Any]:
        """Generate demo F1 telemetry data"""
        # Simulate some F1 race data
        return {
            'total_laps': 58,
            'track_length': 5.3,  # km
            'current_lap': 1,
            'race_time': 0.0,
            'weather': {
                'track_temp': 45.0,
                'air_temp': 28.0,
                'humidity': 65.0,
                'wind_speed': 12.0,
                'wind_direction': 270.0
            }
        }
        
    def update_f1_simulation(self, dt: float):
        """Update F1 car positions for animation"""
        self.animation_time += dt
        
        # Simulate cars moving around a circular track
        for i, car in enumerate(self.f1_cars):
            # Different speeds for each car
            base_speed = 1.0 + i * 0.2
            angle = self.animation_time * base_speed + i * np.pi / 3
            
            # Car follows circular path
            radius = 15.0 + i * 0.5  # Slightly different racing lines
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            z = 0.5
            
            # Update car position
            car.set_position((x, y, z))
            
            # Rotate car to face direction of travel
            heading = angle + np.pi / 2
            car.set_rotation((0, 0, heading))
            
    def update_ui_overlay(self):
        """Update UI overlay with F1-specific information"""
        # This would be rendered using pyglet's 2D graphics
        # For now, just update some demo values
        self.f1_data['current_lap'] = int(self.animation_time / 5.0) + 1
        self.f1_data['race_time'] = self.animation_time
        
    def on_update(self, dt: float):
        """Update simulation - called every frame"""
        # Update F1 car simulation
        self.update_f1_simulation(dt)
        
        # Update camera for smooth orbital motion
        if not self.window.is_paused():
            orbit_speed = 0.2
            new_theta = self.window.camera.target_theta + dt * orbit_speed
            self.window.camera.target_theta = new_theta
            
        # Update window's frame index (for F1 telemetry compatibility)
        if not self.window.is_paused():
            self.window.frame_index += dt * FPS * self.window.playback_speed
            
        # Update UI
        self.update_ui_overlay()
        
    def run(self):
        """Run the F1 3D demo"""
        print("\\n=== F1 3D Engine Demo ===")
        print("Controls:")
        print("  SPACE: Pause/Resume")
        print("  MOUSE: Orbit camera")
        print("  SCROLL: Zoom")
        print("  ARROW KEYS: Frame stepping")
        print("  R: Reset camera")
        print("  1-4: Change lighting presets")
        print("\\nFeatures demonstrated:")
        print("  ✓ 3D camera with smooth transitions")
        print("  ✓ Advanced lighting (ambient, directional, point lights)")
        print("  ✓ Phong shading model")
        print("  ✓ PBR-ready rendering pipeline")
        print("  ✓ Batch rendering for performance")
        print("  ✓ Depth testing and proper Z-ordering")
        print("  ✓ Migration compatibility with Arcade")
        print("\\nStarting 3D engine...")
        
        # Schedule updates
        import pyglet
        pyglet.clock.schedule(self.on_update)
        
        # Run the application
        self.window.run()


def run_basic_3d_demo():
    """Run a basic 3D scene demo"""
    demo = F1_3D_Demo()
    demo.run()


def run_lighting_demo():
    """Demo different lighting configurations"""
    window = Window3D(width=1200, height=800, title="3D Lighting Demo")
    
    # Create test objects
    sphere_mesh = create_sphere(radius=2.0)
    plane_mesh = create_plane(size=20.0)
    
    # Create test objects with different materials
    objects = []
    
    # Red sphere
    red_sphere = SimpleRenderable(sphere_mesh, color=(1.0, 0.0, 0.0, 1.0), position=(-8, 0, 2))
    objects.append(red_sphere)
    
    # Blue cube
    blue_cube = SimpleRenderable(create_cube(size=3.0), color=(0.0, 0.0, 1.0, 1.0), position=(0, 0, 1.5))
    objects.append(blue_cube)
    
    # Green cylinder
    green_cylinder = SimpleRenderable(create_cylinder(radius=1.5, height=4.0), color=(0.0, 1.0, 0.0, 1.0), position=(8, 0, 2))
    objects.append(green_cylinder)
    
    # Add objects to scene
    for obj in objects:
        window.renderer.add_renderable(obj)
    
    # Add ground plane
    ground = SimpleRenderable(plane_mesh, color=(0.5, 0.5, 0.5, 1.0), position=(0, 0, 0))
    window.renderer.add_renderable(ground)
    
    # Position camera
    window.camera.move_to(position=(0, -20, 15), target=(0, 0, 0))
    
    print("\\n=== 3D Lighting Demo ===")
    print("Demonstrating Phong lighting model with different light types")
    
    window.run()


def run_performance_demo():
    """Demo batch rendering performance"""
    window = Window3D(width=1400, height=900, title="3D Performance Demo")
    
    # Use batch renderer for many objects
    batch_renderer = window.batch_renderer
    
    # Create test mesh
    cube_mesh = create_cube(size=0.5)
    
    # Start batch
    batch_renderer.begin_batch(cube_mesh, 'basic')
    
    # Add many cubes in a grid
    grid_size = 15
    spacing = 1.5
    
    for x in range(-grid_size//2, grid_size//2):
        for z in range(-grid_size//2, grid_size//2):
            height = 0.5 + (np.sin(x * 0.5) + np.cos(z * 0.5)) * 0.5
            position = (x * spacing, z * spacing, height)
            color = (
                0.5 + 0.5 * np.sin(x * 0.3),
                0.5 + 0.5 * np.cos(z * 0.3),
                0.8,
                1.0
            )
            batch_renderer.add_instance(position=position, scale=(1.0, height * 2.0, 1.0), color=color)
    
    # Setup lighting
    window.renderer.lights.clear()
    window.renderer.lights.append(AmbientLight(intensity=0.3))
    window.renderer.lights.append(DirectionalLight(direction=(-1, -1, -1), intensity=1.0))
    
    # Position camera
    window.camera.move_to(position=(20, -20, 25), target=(0, 0, 5))
    
    print("\\n=== 3D Performance Demo ===")
    print(f"Rendering {grid_size * grid_size} cubes using instanced rendering")
    print("Demonstrating efficient batch rendering capabilities")
    
    window.run()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        demo_type = sys.argv[1].lower()
        if demo_type == "lighting":
            run_lighting_demo()
        elif demo_type == "performance":
            run_performance_demo()
        else:
            run_basic_3d_demo()
    else:
        run_basic_3d_demo()