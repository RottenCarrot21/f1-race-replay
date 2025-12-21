"""
F1 3D Integration Utilities
Provides seamless integration between the existing F1 data system and the new 3D engine
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.engine3d import Window3D, SimpleRenderable
from src.engine3d.graphics import create_plane, create_cube, create_sphere, create_cylinder, AmbientLight, DirectionalLight, PointLight
from src.engine3d.migration import MigrationHelper, ArcadeCompatibilityLayer


class F1_3D_Integrator:
    """
    Integrates F1 telemetry data with the 3D engine
    Provides seamless conversion from existing F1 data structures to 3D
    """
    
    def __init__(self, window3d: Window3D):
        self.window = window3d
        self.renderer = window3d.renderer
        self.migration_helper = MigrationHelper(window3d)
        
        # F1-specific 3D objects
        self.track_3d = None
        self.f1_cars = {}
        self.environment_objects = []
        
    def create_3d_f1_track(self, 
                          example_lap: Any,
                          track_width: float = 15.0,
                          track_color: Tuple[float, float, float, float] = (0.2, 0.2, 0.2, 1.0),
                          track_height: float = 0.1) -> SimpleRenderable:
        """
        Create a 3D F1 track from example lap data
        
        Args:
            example_lap: FastF1 lap telemetry data
            track_width: Width of the track in world units
            track_color: RGBA color for the track
            track_height: Height/thickness of the track surface
            
        Returns:
            SimpleRenderable object representing the 3D track
        """
        try:
            # Extract position data from FastF1 telemetry
            x_coords = example_lap['X'].values
            y_coords = example_lap['Y'].values
            
            # Calculate track bounds
            x_min, x_max = np.min(x_coords), np.max(x_coords)
            y_min, y_max = np.min(y_coords), np.max(y_coords)
            
            # Calculate track dimensions
            track_length = np.max([x_max - x_min, y_max - y_min])
            
            # Create track plane
            track_mesh = create_plane(size=track_length)
            
            # Center the track and scale appropriately
            center_x = (x_min + x_max) / 2
            center_y = (y_min + y_max) / 2
            
            # Scale the track to desired width
            scale_x = track_width / 10.0  # Base plane is 10 units
            scale_y = track_length / 10.0
            scale_z = track_height
            
            self.track_3d = SimpleRenderable(
                mesh=track_mesh,
                color=track_color,
                position=(center_x, center_y, 0),
                rotation=(0, 0, 0),
                scale=(scale_x, scale_y, scale_z)
            )
            
            self.renderer.add_renderable(self.track_3d)
            return self.track_3d
            
        except Exception as e:
            print(f"Error creating 3D track: {e}")
            # Fallback to simple track
            return self.create_fallback_track()
            
    def create_fallback_track(self) -> SimpleRenderable:
        """Create a fallback track if main creation fails"""
        track_mesh = create_plane(size=100.0)
        self.track_3d = SimpleRenderable(
            mesh=track_mesh,
            color=(0.3, 0.3, 0.3, 1.0),
            position=(0, 0, 0),
            scale=(5.0, 10.0, 0.1)
        )
        self.renderer.add_renderable(self.track_3d)
        return self.track_3d
        
    def create_f1_car(self, 
                     driver_code: str,
                     car_color: Tuple[float, float, float, float],
                     position_2d: Tuple[float, float],
                     rotation_2d: float = 0.0,
                     scale: float = 1.0) -> SimpleRenderable:
        """
        Create a 3D F1 car representation
        
        Args:
            driver_code: Driver identifier (e.g., 'HAM', 'VER')
            car_color: RGBA color for the car
            position_2d: (x, y) position from F1 telemetry
            rotation_2d: Rotation angle in radians
            scale: Scale factor for the car
            
        Returns:
            SimpleRenderable object representing the F1 car
        """
        # Create car body (cube)
        car_mesh = create_cube(size=0.8)
        
        # Create F1 car with realistic proportions
        car = SimpleRenderable(
            mesh=car_mesh,
            color=car_color,
            position=(position_2d[0], position_2d[1], scale/2),
            rotation=(0, 0, rotation_2d),
            scale=(scale * 0.5, scale * 1.5, scale * 0.3)  # F1 car proportions
        )
        
        self.f1_cars[driver_code] = car
        self.renderer.add_renderable(car)
        
        # Add car details (optional)
        self._add_car_details(car, car_color)
        
        return car
        
    def _add_car_details(self, car: SimpleRenderable, color: Tuple[float, float, float, float]):
        """Add additional details to make cars look more realistic"""
        # Add front wing
        wing_mesh = create_cylinder(radius=0.3, height=0.1, segments=8)
        wing = SimpleRenderable(
            mesh=wing_mesh,
            color=color,
            position=(car.position[0], car.position[1] + 0.4, car.position[2] + 0.1),
            rotation=(0, 0, 0),
            scale=(0.8, 0.1, 0.1)
        )
        self.renderer.add_renderable(wing)
        
    def update_car_position(self, 
                           driver_code: str, 
                           position_2d: Tuple[float, float],
                           rotation_2d: float = 0.0):
        """
        Update car position in 3D space
        
        Args:
            driver_code: Driver identifier
            position_2d: New (x, y) position
            rotation_2d: New rotation angle
        """
        if driver_code in self.f1_cars:
            car = self.f1_cars[driver_code]
            car.set_position((position_2d[0], position_2d[1], 0.25))
            car.set_rotation((0, 0, rotation_2d))
            
    def create_racing_environment(self, 
                                 weather_conditions: Optional[Dict[str, Any]] = None):
        """
        Create 3D environment objects based on race conditions
        
        Args:
            weather_conditions: Weather data for environmental effects
        """
        # Clear existing environment
        for obj in self.environment_objects:
            if obj in self.renderer.renderables:
                self.renderer.renderables.remove(obj)
        self.environment_objects.clear()
        
        # Create grandstands
        self._create_grandstands()
        
        # Create environmental objects based on weather
        if weather_conditions:
            self._create_weather_effects(weather_conditions)
            
    def _create_grandstands(self):
        """Create 3D grandstand structures"""
        stand_mesh = create_cube(size=2.0)
        
        # Create stands around the track
        for i in range(-3, 4):
            for j in range(-2, 3):
                if abs(i) > 2 or abs(j) > 1:  # Leave space for track
                    stand = SimpleRenderable(
                        mesh=stand_mesh,
                        color=(0.8, 0.8, 0.9, 1.0),
                        position=(i * 25, j * 25, 5),
                        scale=(2.0, 2.0, 5.0)
                    )
                    self.renderer.add_renderable(stand)
                    self.environment_objects.append(stand)
                    
    def _create_weather_effects(self, weather: Dict[str, Any]):
        """Create weather-based visual effects"""
        # Add lights based on weather conditions
        if weather.get('rain_state', 'Dry') != 'Dry':
            # Add additional lights for rainy conditions
            rain_light = PointLight(
                position=(0, 0, 20),
                intensity=2.0,
                color=(0.8, 0.9, 1.0),  # Cool blue light
                range=80.0
            )
            self.renderer.lights.append(rain_light)
            
        # Adjust ambient lighting based on air temperature
        air_temp = weather.get('air_temp', 20.0)
        if air_temp > 30:
            # Hot conditions - warmer lighting
            ambient = next((light for light in self.renderer.lights if isinstance(light, AmbientLight)), None)
            if ambient:
                ambient.set_color((1.0, 0.95, 0.9))  # Warm tint
                
    def setup_f1_lighting(self, 
                         time_of_day: str = "afternoon",
                         weather: Optional[Dict[str, Any]] = None) -> None:
        """
        Setup lighting appropriate for F1 racing
        
        Args:
            time_of_day: "morning", "afternoon", "evening", or "night"
            weather: Optional weather conditions
        """
        # Clear existing lights
        self.renderer.lights.clear()
        
        # Set ambient lighting based on time of day
        ambient_configs = {
            "morning": (0.6, (1.0, 0.95, 0.9)),
            "afternoon": (0.4, (1.0, 1.0, 1.0)),
            "evening": (0.3, (1.0, 0.9, 0.8)),
            "night": (0.2, (0.8, 0.9, 1.0))
        }
        
        ambient_intensity, ambient_color = ambient_configs.get(time_of_day, ambient_configs["afternoon"])
        ambient = AmbientLight(intensity=ambient_intensity, color=ambient_color)
        self.renderer.lights.append(ambient)
        
        # Add main sunlight
        sun_configs = {
            "morning": ((-0.8, -1.0, -0.3), 1.5),
            "afternoon": ((-0.5, -1.0, -0.5), 1.2),
            "evening": ((-0.3, -0.8, -0.5), 1.0),
            "night": ((0.2, -1.0, -0.2), 0.3)
        }
        
        sun_direction, sun_intensity = sun_configs.get(time_of_day, sun_configs["afternoon"])
        sun = DirectionalLight(direction=sun_direction, intensity=sun_intensity)
        self.renderer.lights.append(sun)
        
        # Add weather-specific lighting
        if weather:
            track_temp = weather.get('track_temp', 30.0)
            if track_temp > 40:
                # Hot track - add heat shimmer effect (simulated with point lights)
                heat_light = PointLight(
                    position=(0, 0, 5),
                    intensity=1.5,
                    color=(1.0, 0.8, 0.6),
                    range=30.0
                )
                self.renderer.lights.append(heat_light)
                
    def migrate_from_arcade_replay(self, arcade_data: Dict[str, Any]):
        """
        Migrate from existing Arcade-based race replay data
        
        Args:
            arcade_data: Dictionary containing track points, car positions, etc.
        """
        # Convert track points if available
        if 'track_points' in arcade_data:
            self.migration_helper.setup_mixed_2d_3d_scene(
                track_2d_points=arcade_data['track_points'],
                car_positions_2d=arcade_data.get('car_positions', {}),
                car_colors={k: ArcadeCompatibilityLayer.arcade_color_to_rgba(v) 
                           for k, v in arcade_data.get('car_colors', {}).items()}
            )
            
        # Add lighting to migrated elements
        self.migration_helper.add_lighting_to_2d_elements()
        
    def get_f1_scene_stats(self) -> Dict[str, Any]:
        """Get statistics about the current F1 3D scene"""
        return {
            'num_cars': len(self.f1_cars),
            'has_track': self.track_3d is not None,
            'num_environment_objects': len(self.environment_objects),
            'num_lights': len(self.renderer.lights),
            'renderables_count': len(self.renderer.renderables)
        }


def create_3d_f1_window(width: int = 1920, height: int = 1200, title: str = "F1 3D Race Replay") -> Tuple[Window3D, F1_3D_Integrator]:
    """
    Create a 3D F1 window with integrator
    
    Returns:
        Tuple of (Window3D, F1_3D_Integrator)
    """
    window = Window3D(width=width, height=height, title=title)
    integrator = F1_3D_Integrator(window)
    
    return window, integrator


# Example usage function
def example_integration():
    """Example of how to integrate F1 data with 3D engine"""
    window, integrator = create_3d_f1_window(title="F1 3D Integration Demo")
    
    # Setup F1-specific scene
    integrator.setup_f1_lighting("afternoon")
    
    # Create example cars with team colors
    team_colors = {
        'HAM': (1.0, 0.0, 0.0, 1.0),      # Ferrari Red
        'VER': (0.0, 0.2, 1.0, 1.0),      # Red Bull Blue
        'HAM': (0.0, 1.0, 0.0, 1.0),      # Mercedes Green
        'LEC': (1.0, 0.0, 1.0, 1.0),      # Ferrari Purple (for LeClerc)
    }
    
    # Create cars
    positions = [(0, 0), (2, 1), (4, 2), (6, 3)]
    for i, (driver, color) in enumerate(team_colors.items()):
        pos = positions[i] if i < len(positions) else (i * 2, i)
        integrator.create_f1_car(driver, color, pos)
    
    # Position camera for good F1 view
    window.camera.move_to(
        position=(20, -20, 15),
        target=(0, 0, 0)
    )
    
    print("F1 3D Integration Example")
    print("=" * 30)
    print("Features:")
    print("✓ F1 car creation and positioning")
    print("✓ Racing environment setup")
    print("✓ Weather-based lighting")
    print("✓ Migration from Arcade data")
    print("\\nStarting 3D window...")
    
    return window


if __name__ == "__main__":
    example_window = example_integration()
    example_window.run()