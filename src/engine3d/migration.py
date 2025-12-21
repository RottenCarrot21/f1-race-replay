"""
Migration utilities for transitioning from Arcade to 3D Engine
Provides compatibility functions and examples for gradual migration
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from .core.window import Window3D
from .graphics import SimpleRenderable, create_cube, create_plane, create_sphere


class MigrationHelper:
    """
    Helper class to ease migration from Arcade-based 2D rendering
    to the new 3D engine
    """
    
    def __init__(self, window3d: Window3D):
        self.window = window3d
        self.renderables_2d: List[Dict[str, Any]] = []
        self.renderables_3d: List[SimpleRenderable] = []
        
    def convert_arcade_2d_to_3d_plane(self, 
                                     points_2d: List[Tuple[float, float]], 
                                     color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
                                     z_level: float = 0.0) -> SimpleRenderable:
        """
        Convert 2D Arcade points to a 3D plane for the track
        
        Args:
            points_2d: List of (x, y) points from Arcade rendering
            color: RGBA color for the plane
            z_level: Z coordinate for the plane
            
        Returns:
            SimpleRenderable object representing the 2D geometry in 3D
        """
        # Create a simple plane mesh
        plane_mesh = create_plane(size=10.0)
        
        # Calculate bounding box of 2D points
        xs = [p[0] for p in points_2d]
        ys = [p[1] for p in points_2d]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        # Scale and center the plane to match the 2D bounds
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        width = max_x - min_x
        height = max_y - min_y
        
        # Create the 3D plane
        plane = SimpleRenderable(
            mesh=plane_mesh,
            color=color,
            position=(center_x, center_y, z_level),
            rotation=(0, 0, 0),
            scale=(width / 10.0, height / 10.0, 1.0)  # Scale to match 2D bounds
        )
        
        return plane
        
    def convert_car_positions_2d_to_3d(self, 
                                      car_positions_2d: Dict[str, Dict[str, float]], 
                                      car_colors: Dict[str, Tuple[float, float, float, float]] = None,
                                      car_size: float = 1.0) -> List[SimpleRenderable]:
        """
        Convert 2D car positions to 3D car objects
        
        Args:
            car_positions_2d: Dictionary of {driver_code: {'x': float, 'y': float, 'rotation': float}}
            car_colors: Optional mapping of driver codes to colors
            car_size: Size scale for the cars
            
        Returns:
            List of SimpleRenderable objects representing the cars
        """
        car_mesh = create_cube(size=0.5)  # Basic car representation
        cars_3d = []
        
        for driver_code, pos_2d in car_positions_2d.items():
            x = pos_2d.get('x', 0.0)
            y = pos_2d.get('y', 0.0)
            rotation = pos_2d.get('rotation', 0.0)
            
            # Get color (default to white if not specified)
            color = car_colors.get(driver_code, (1.0, 1.0, 1.0, 1.0)) if car_colors else (1.0, 1.0, 1.0, 1.0)
            
            # Convert 2D rotation to 3D (2D rotation around Z axis)
            car_3d = SimpleRenderable(
                mesh=car_mesh,
                color=color,
                position=(x, y, car_size/2),  # Sit on the track plane
                rotation=(0, 0, rotation),
                scale=(car_size, car_size * 2.0, car_size)  # Car-like proportions
            )
            
            cars_3d.append(car_3d)
            
        return cars_3d
        
    def create_2d_ui_overlay_3d(self, 
                               ui_elements_2d: List[Dict[str, Any]], 
                               screen_width: float = 1920,
                               screen_height: float = 1200) -> SimpleRenderable:
        """
        Create 3D representations of 2D UI elements as billboards or planes
        
        Args:
            ui_elements_2d: List of 2D UI element definitions
            screen_width: Width of the screen in pixels
            screen_height: Height of the screen in pixels
            
        Returns:
            SimpleRenderable representing the UI as a 3D overlay
        """
        # Create a large plane for the UI overlay
        ui_plane_mesh = create_plane(size=1.0)
        
        ui_plane = SimpleRenderable(
            mesh=ui_plane_mesh,
            color=(0.0, 0.0, 0.0, 0.7),  # Semi-transparent black
            position=(0, 0, 100),  # Place in front of the 3D scene
            rotation=(0, 0, 0),
            scale=(screen_width / 100.0, screen_height / 100.0, 1.0)  # Scale to screen size
        )
        
        return ui_plane
        
    def setup_mixed_2d_3d_scene(self, 
                               track_2d_points: List[Tuple[float, float]],
                               car_positions_2d: Dict[str, Dict[str, float]],
                               track_color: Tuple[float, float, float, float] = (0.3, 0.3, 0.3, 1.0),
                               car_colors: Dict[str, Tuple[float, float, float, float]] = None):
        """
        Setup a mixed 2D-3D scene that renders 2D elements in 3D space
        This provides a gradual migration path from pure 2D Arcade rendering
        
        Args:
            track_2d_points: Track boundary points from original 2D rendering
            car_positions_2d: Current car positions in 2D
            track_color: Color for the track
            car_colors: Colors for each car
        """
        # Convert track to 3D plane
        if track_2d_points:
            track_3d = self.convert_arcade_2d_to_3d_plane(track_2d_points, track_color, z_level=0)
            self.window.renderer.add_renderable(track_3d)
            self.renderables_3d.append(track_3d)
            
        # Convert cars to 3D
        cars_3d = self.convert_car_positions_2d_to_3d(car_positions_2d, car_colors)
        for car in cars_3d:
            self.window.renderer.add_renderable(car)
            self.renderables_3d.append(car)
            
    def update_car_positions_3d(self, car_positions_2d: Dict[str, Dict[str, float]]):
        """
        Update 3D car positions based on 2D positions
        
        Args:
            car_positions_2d: Current 2D car positions
        """
        # Update the position of existing 3D cars
        car_index = 0
        for driver_code, pos_2d in car_positions_2d.items():
            if car_index < len(self.renderables_3d):
                car = self.renderables_3d[car_index + 1]  # +1 because track is first
                
                x = pos_2d.get('x', 0.0)
                y = pos_2d.get('y', 0.0)
                rotation = pos_2d.get('rotation', 0.0)
                
                car.set_position((x, y, 0.25))  # Keep cars on track level
                car.set_rotation((0, 0, rotation))
                
            car_index += 1
            
    def add_depth_testing_support(self):
        """Enable depth testing and proper Z-ordering"""
        # Depth testing is already enabled in Window3D constructor
        # This is here for reference and future customization
        pass
        
    def add_lighting_to_2d_elements(self, 
                                   ambient_intensity: float = 0.4,
                                   light_direction: Tuple[float, float, float] = (-0.5, -1.0, -0.3)):
        """
        Add lighting to formerly 2D elements
        
        Args:
            ambient_intensity: Ambient light intensity
            light_direction: Direction of main light source
        """
        # Add lighting to the scene
        from .graphics import AmbientLight, DirectionalLight
        
        # Clear existing lights and add new ones
        self.window.renderer.lights.clear()
        
        ambient = AmbientLight(intensity=ambient_intensity)
        self.window.renderer.lights.append(ambient)
        
        directional = DirectionalLight(direction=light_direction, intensity=1.0)
        self.window.renderer.lights.append(directional)


class ArcadeCompatibilityLayer:
    """
    Provides compatibility functions to help migrate Arcade-based code
    to work with the new 3D engine
    """
    
    @staticmethod
    def arcade_color_to_rgba(arcade_color: Tuple[int, int, int]) -> Tuple[float, float, float, float]:
        """Convert Arcade color tuple (0-255) to RGBA (0.0-1.0)"""
        return (
            arcade_color[0] / 255.0,
            arcade_color[1] / 255.0,
            arcade_color[2] / 255.0,
            1.0  # Full alpha
        )
        
    @staticmethod
    def rgba_to_arcade_color(rgba: Tuple[float, float, float, float]) -> Tuple[int, int, int]:
        """Convert RGBA (0.0-1.0) to Arcade color tuple (0-255)"""
        return (
            int(rgba[0] * 255),
            int(rgba[1] * 255),
            int(rgba[2] * 255)
        )
        
    @staticmethod
    def create_world_to_screen_converter(window3d: Window3D):
        """Create a world-to-screen coordinate converter"""
        def world_to_screen(x: float, y: float, z: float = 0.0) -> Tuple[float, float]:
            """Convert world coordinates to screen coordinates"""
            # Use the camera's world_to_screen method
            world_point = np.array([x, y, z])
            return window3d.camera.world_to_screen(world_point)
            
        return world_to_screen
        
    @staticmethod
    def create_screen_to_world_converter(window3d: Window3D):
        """Create a screen-to-world coordinate converter"""
        def screen_to_world(screen_x: float, screen_y: float, depth: float = 0.0) -> np.ndarray:
            """Convert screen coordinates to world coordinates"""
            return window3d.camera.screen_to_world(screen_x, screen_y, depth)
            
        return screen_to_world


# Migration example function
def create_migration_example():
    """Create an example showing how to migrate from Arcade to 3D"""
    
    def arcade_style_rendering_example():
        """Example of old Arcade-style rendering"""
        # This represents old Arcade code
        old_arcade_data = {
            'track_points': [(100, 100), (200, 100), (200, 200), (100, 200)],
            'car_positions': {
                'HAM': {'x': 150, 'y': 150, 'rotation': 0},
                'VER': {'x': 160, 'y': 150, 'rotation': 0}
            },
            'car_colors': {
                'HAM': (220, 20, 60),    # Red
                'VER': (30, 144, 255)    # Blue
            }
        }
        
        return old_arcade_data
        
    def migrate_to_3d(window3d: Window3D, arcade_data: Dict[str, Any]):
        """Example migration function"""
        migration_helper = MigrationHelper(window3d)
        
        # Convert color format
        car_colors_3d = {}
        for driver, color in arcade_data.get('car_colors', {}).items():
            car_colors_3d[driver] = ArcadeCompatibilityLayer.arcade_color_to_rgba(color)
            
        # Setup mixed 2D-3D scene
        migration_helper.setup_mixed_2d_3d_scene(
            track_2d_points=arcade_data['track_points'],
            car_positions_2d=arcade_data['car_positions'],
            car_colors=car_colors_3d
        )
        
        # Add lighting
        migration_helper.add_lighting_to_2d_elements()
        
        return migration_helper
        
    return arcade_style_rendering_example, migrate_to_3d