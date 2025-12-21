"""
Lighting System for 3D Rendering
Provides different types of lights with proper attenuation and intensity controls
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any
from abc import ABC, abstractmethod


class Light(ABC):
    """Abstract base class for all light types"""
    
    @abstractmethod
    def get_light_data(self) -> Dict[str, Any]:
        """Get light data for shader uniforms"""
        pass


class AmbientLight(Light):
    """Ambient light for global illumination"""
    
    def __init__(self, 
                 intensity: float = 0.3,
                 color: Tuple[float, float, float] = (1.0, 1.0, 1.0)):
        self.intensity = np.clip(intensity, 0.0, 2.0)
        self.color = np.array(color, dtype=np.float32)
        
    def get_light_data(self) -> Dict[str, Any]:
        return {
            'type': 'ambient',
            'intensity': self.intensity,
            'color': self.color
        }
        
    def set_intensity(self, intensity: float):
        """Set ambient light intensity"""
        self.intensity = np.clip(intensity, 0.0, 2.0)
        
    def set_color(self, color: Tuple[float, float, float]):
        """Set ambient light color"""
        self.color = np.array(color, dtype=np.float32)


class DirectionalLight(Light):
    """Directional light for sunlight-like illumination"""
    
    def __init__(self,
                 direction: Tuple[float, float, float] = (0.0, -1.0, -0.5),
                 intensity: float = 1.0,
                 color: Tuple[float, float, float] = (1.0, 1.0, 1.0)):
        self.direction = np.array(direction, dtype=np.float32)
        self.intensity = np.clip(intensity, 0.0, 10.0)
        self.color = np.array(color, dtype=np.float32)
        
        # Normalize direction
        self._normalize_direction()
        
    def _normalize_direction(self):
        """Normalize the light direction vector"""
        norm = np.linalg.norm(self.direction)
        if norm > 0:
            self.direction = self.direction / norm
        else:
            self.direction = np.array([0.0, -1.0, 0.0], dtype=np.float32)
            
    def get_light_data(self) -> Dict[str, Any]:
        return {
            'type': 'directional',
            'direction': self.direction,
            'intensity': self.intensity,
            'color': self.color
        }
        
    def set_direction(self, direction: Tuple[float, float, float]):
        """Set light direction (will be normalized)"""
        self.direction = np.array(direction, dtype=np.float32)
        self._normalize_direction()
        
    def set_intensity(self, intensity: float):
        """Set light intensity"""
        self.intensity = np.clip(intensity, 0.0, 10.0)
        
    def set_color(self, color: Tuple[float, float, float]):
        """Set light color"""
        self.color = np.array(color, dtype=np.float32)
        
    def rotate(self, yaw: float = 0.0, pitch: float = 0.0, roll: float = 0.0):
        """Rotate the light direction using Euler angles"""
        # Rotation matrix
        cos_yaw, sin_yaw = np.cos(yaw), np.sin(yaw)
        cos_pitch, sin_pitch = np.cos(pitch), np.sin(pitch)
        cos_roll, sin_roll = np.cos(roll), np.sin(roll)
        
        # Rotation around Y (yaw)
        rotation_y = np.array([
            [cos_yaw, 0, sin_yaw],
            [0, 1, 0],
            [-sin_yaw, 0, cos_yaw]
        ])
        
        # Rotation around X (pitch)
        rotation_x = np.array([
            [1, 0, 0],
            [0, cos_pitch, -sin_pitch],
            [0, sin_pitch, cos_pitch]
        ])
        
        # Rotation around Z (roll)
        rotation_z = np.array([
            [cos_roll, -sin_roll, 0],
            [sin_roll, cos_roll, 0],
            [0, 0, 1]
        ])
        
        # Apply rotations
        new_direction = rotation_z @ rotation_x @ rotation_y @ self.direction
        self.set_direction(tuple(new_direction))


class PointLight(Light):
    """Point light for bulb-like illumination with distance-based attenuation"""
    
    def __init__(self,
                 position: Tuple[float, float, float] = (0.0, 0.0, 5.0),
                 intensity: float = 1.0,
                 color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
                 range: float = 50.0):
        self.position = np.array(position, dtype=np.float32)
        self.intensity = np.clip(intensity, 0.0, 10.0)
        self.color = np.array(color, dtype=np.float32)
        self.range = np.clip(range, 0.1, 1000.0)
        
    def get_light_data(self) -> Dict[str, Any]:
        return {
            'type': 'point',
            'position': self.position,
            'intensity': self.intensity,
            'color': self.color,
            'range': self.range
        }
        
    def set_position(self, position: Tuple[float, float, float]):
        """Set light position"""
        self.position = np.array(position, dtype=np.float32)
        
    def set_intensity(self, intensity: float):
        """Set light intensity"""
        self.intensity = np.clip(intensity, 0.0, 10.0)
        
    def set_color(self, color: Tuple[float, float, float]):
        """Set light color"""
        self.color = np.array(color, dtype=np.float32)
        
    def set_range(self, range: float):
        """Set light range (distance at which light fades to zero)"""
        self.range = np.clip(range, 0.1, 1000.0)
        
    def move_to(self, position: Tuple[float, float, float]):
        """Move light to new position with smooth transition"""
        self.position = np.array(position, dtype=np.float32)
        
    def follow_target(self, target_position: Tuple[float, float, float], offset: Tuple[float, float, float] = (0.0, 0.0, 5.0)):
        """Make light follow a target object with offset"""
        target = np.array(target_position, dtype=np.float32)
        self.position = target + np.array(offset, dtype=np.float32)


class SpotLight(Light):
    """Spot light for focused beam-like illumination"""
    
    def __init__(self,
                 position: Tuple[float, float, float] = (0.0, 0.0, 5.0),
                 direction: Tuple[float, float, float] = (0.0, 0.0, -1.0),
                 intensity: float = 1.0,
                 color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
                 range: float = 50.0,
                 inner_cone: float = 15.0,  # degrees
                 outer_cone: float = 30.0):  # degrees
        self.position = np.array(position, dtype=np.float32)
        self.direction = np.array(direction, dtype=np.float32)
        self.intensity = np.clip(intensity, 0.0, 10.0)
        self.color = np.array(color, dtype=np.float32)
        self.range = np.clip(range, 0.1, 1000.0)
        self.inner_cone = np.clip(inner_cone, 0.0, 89.0)  # degrees
        self.outer_cone = np.clip(outer_cone, self.inner_cone + 1.0, 90.0)  # degrees
        
        # Normalize direction
        self._normalize_direction()
        
    def _normalize_direction(self):
        """Normalize the light direction vector"""
        norm = np.linalg.norm(self.direction)
        if norm > 0:
            self.direction = self.direction / norm
        else:
            self.direction = np.array([0.0, 0.0, -1.0], dtype=np.float32)
            
    def get_light_data(self) -> Dict[str, Any]:
        return {
            'type': 'spot',
            'position': self.position,
            'direction': self.direction,
            'intensity': self.intensity,
            'color': self.color,
            'range': self.range,
            'inner_cone': np.radians(self.inner_cone),
            'outer_cone': np.radians(self.outer_cone)
        }
        
    def set_position(self, position: Tuple[float, float, float]):
        """Set light position"""
        self.position = np.array(position, dtype=np.float32)
        
    def set_direction(self, direction: Tuple[float, float, float]):
        """Set light direction (will be normalized)"""
        self.direction = np.array(direction, dtype=np.float32)
        self._normalize_direction()
        
    def set_intensity(self, intensity: float):
        """Set light intensity"""
        self.intensity = np.clip(intensity, 0.0, 10.0)
        
    def set_color(self, color: Tuple[float, float, float]):
        """Set light color"""
        self.color = np.array(color, dtype=np.float32)
        
    def set_range(self, range: float):
        """Set light range"""
        self.range = np.clip(range, 0.1, 1000.0)
        
    def set_cone_angles(self, inner_cone: float, outer_cone: float):
        """Set inner and outer cone angles in degrees"""
        self.inner_cone = np.clip(inner_cone, 0.0, 89.0)
        self.outer_cone = np.clip(outer_cone, self.inner_cone + 1.0, 90.0)
        
    def look_at(self, target: Tuple[float, float, float]):
        """Make spot light look at a target point"""
        target_vec = np.array(target, dtype=np.float32)
        direction = target_vec - self.position
        self.set_direction(tuple(direction))


class LightManager:
    """Manages multiple lights in a scene"""
    
    def __init__(self):
        self.lights: Dict[str, Light] = {}
        self.ambient_light = AmbientLight(intensity=0.3)
        
    def add_light(self, name: str, light: Light):
        """Add a named light to the scene"""
        self.lights[name] = light
        
    def remove_light(self, name: str):
        """Remove a light from the scene"""
        if name in self.lights:
            del self.lights[name]
            
    def get_light(self, name: str) -> Optional[Light]:
        """Get a light by name"""
        return self.lights.get(name)
        
    def get_all_lights(self) -> Dict[str, Light]:
        """Get all lights in the scene"""
        return self.lights.copy()
        
    def set_ambient_light(self, light: AmbientLight):
        """Set the global ambient light"""
        self.ambient_light = light
        
    def clear_lights(self):
        """Remove all lights except ambient"""
        self.lights.clear()
        
    def get_light_data_for_shader(self) -> Dict[str, Any]:
        """Get all light data formatted for shader uniforms"""
        # Group lights by type
        directional_lights = []
        point_lights = []
        spot_lights = []
        
        for light in self.lights.values():
            data = light.get_light_data()
            if data['type'] == 'directional':
                directional_lights.append(data)
            elif data['type'] == 'point':
                point_lights.append(data)
            elif data['type] == 'spot':
                spot_lights.append(data)
                
        return {
            'ambient_light': self.ambient_light.get_light_data(),
            'directional_lights': directional_lights,
            'point_lights': point_lights,
            'spot_lights': spot_lights,
            'num_directional_lights': len(directional_lights),
            'num_point_lights': len(point_lights),
            'num_spot_lights': len(spot_lights)
        }
        
    def create_sun_light(self, direction: Tuple[float, float, float] = (-0.5, -1.0, -0.3),
                        intensity: float = 1.0,
                        color: Tuple[float, float, float] = (1.0, 1.0, 1.0)) -> DirectionalLight:
        """Create a sun-like directional light"""
        return DirectionalLight(direction=direction, intensity=intensity, color=color)
        
    def create_test_scene_lights(self):
        """Create a standard test scene with multiple lights"""
        # Clear existing lights
        self.clear_lights()
        
        # Add sun
        sun = self.create_sun_light()
        self.add_light('sun', sun)
        
        # Add some point lights for variety
        point1 = PointLight(
            position=(10, 10, 10),
            intensity=2.0,
            color=(1.0, 0.8, 0.6),  # Warm white
            range=30.0
        )
        self.add_light('warm_light', point1)
        
        point2 = PointLight(
            position=(-10, -10, 5),
            intensity=1.5,
            color=(0.6, 0.8, 1.0),  # Cool white
            range=25.0
        )
        self.add_light('cool_light', point2)
        
        # Add a spot light
        spot = SpotLight(
            position=(0, 0, 15),
            direction=(0, 0, -1),
            intensity=3.0,
            color=(1.0, 1.0, 0.9),  # Bright white
            range=40.0,
            inner_cone=10.0,
            outer_cone=25.0
        )
        self.add_light('spot', spot)