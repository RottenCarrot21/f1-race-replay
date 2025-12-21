"""
3D Graphics Rendering System
Provides basic rendering capabilities with support for different shaders and lighting models
"""

import moderngl
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from abc import ABC, abstractmethod
from .shaders import ShaderManager, get_default_shaders
from .geometry import Mesh, create_cube, create_plane, create_sphere
from .lighting import Light, DirectionalLight, PointLight, AmbientLight


class Renderable3D(ABC):
    """Abstract base class for 3D objects that can be rendered"""
    
    @abstractmethod
    def get_mesh(self) -> Mesh:
        """Get the mesh data for this object"""
        pass
        
    @abstractmethod
    def get_material(self) -> Dict[str, Any]:
        """Get material properties (color, texture, etc.)"""
        pass
        
    @abstractmethod
    def get_transform(self) -> np.ndarray:
        """Get transformation matrix (model matrix)"""
        pass


class SimpleRenderable(Renderable3D):
    """Simple renderable object with basic properties"""
    
    def __init__(self, 
                 mesh: Mesh,
                 color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
                 position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                 rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                 scale: Tuple[float, float, float] = (1.0, 1.0, 1.0)):
        
        self.mesh = mesh
        self.color = color
        self.position = np.array(position, dtype=np.float32)
        self.rotation = np.array(rotation, dtype=np.float32)
        self.scale = np.array(scale, dtype=np.float32)
        
        # Transformation matrix cache
        self._model_matrix = None
        
    def get_mesh(self) -> Mesh:
        return self.mesh
        
    def get_material(self) -> Dict[str, Any]:
        return {
            'color': self.color,
            'texture': None,
            'material_type': 'basic'
        }
        
    def get_transform(self) -> np.ndarray:
        if self._model_matrix is None:
            self._model_matrix = self._calculate_model_matrix()
        return self._model_matrix
        
    def _calculate_model_matrix(self) -> np.ndarray:
        """Calculate the model transformation matrix"""
        # Translation matrix
        translation = np.array([
            [1, 0, 0, self.position[0]],
            [0, 1, 0, self.position[1]],
            [0, 0, 1, self.position[2]],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        # Rotation matrices (X, Y, Z)
        cos_x, sin_x = np.cos(self.rotation[0]), np.sin(self.rotation[0])
        cos_y, sin_y = np.cos(self.rotation[1]), np.sin(self.rotation[1])
        cos_z, sin_z = np.cos(self.rotation[2]), np.sin(self.rotation[2])
        
        rotation_x = np.array([
            [1, 0, 0, 0],
            [0, cos_x, -sin_x, 0],
            [0, sin_x, cos_x, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        rotation_y = np.array([
            [cos_y, 0, sin_y, 0],
            [0, 1, 0, 0],
            [-sin_y, 0, cos_y, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        rotation_z = np.array([
            [cos_z, -sin_z, 0, 0],
            [sin_z, cos_z, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        # Scale matrix
        scale_matrix = np.array([
            [self.scale[0], 0, 0, 0],
            [0, self.scale[1], 0, 0],
            [0, 0, self.scale[2], 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        # Combine transformations: Model = T * R * S
        model_matrix = translation @ rotation_z @ rotation_y @ rotation_x @ scale_matrix
        
        return model_matrix
        
    def set_position(self, position: Tuple[float, float, float]):
        """Update position and invalidate cache"""
        self.position = np.array(position, dtype=np.float32)
        self._model_matrix = None
        
    def set_rotation(self, rotation: Tuple[float, float, float]):
        """Update rotation and invalidate cache"""
        self.rotation = np.array(rotation, dtype=np.float32)
        self._model_matrix = None
        
    def set_scale(self, scale: Tuple[float, float, float]):
        """Update scale and invalidate cache"""
        self.scale = np.array(scale, dtype=np.float32)
        self._model_matrix = None
        
    def set_color(self, color: Tuple[float, float, float, float]):
        """Update color"""
        self.color = color


class Renderer3D:
    """
    Main 3D renderer that handles rendering multiple objects with different shaders and lighting
    """
    
    def __init__(self, ctx: moderngl.Context):
        self.ctx = ctx
        self.shader_manager = ShaderManager()
        self.renderables: List[Renderable3D] = []
        self.lights: List[Light] = []
        
        # Default lighting setup
        self._setup_default_lighting()
        
        # Default shaders
        self.current_shader = None
        self.set_shader('basic_lighting')
        
    def _setup_default_lighting(self):
        """Setup default lighting for the scene"""
        # Add ambient light
        ambient = AmbientLight(intensity=0.3, color=(1.0, 1.0, 1.0))
        self.lights.append(ambient)
        
        # Add a directional light (like the sun)
        directional = DirectionalLight(
            direction=(-0.5, -1.0, -0.3),
            intensity=0.8,
            color=(1.0, 1.0, 1.0)
        )
        self.lights.append(directional)
        
    def set_shader(self, shader_name: str):
        """Set the current shader program"""
        if shader_name in self.shader_manager.shaders:
            self.current_shader = self.shader_manager.get_shader(shader_name)
        else:
            print(f"Warning: Shader '{shader_name}' not found, using basic_lighting")
            self.current_shader = self.shader_manager.get_shader('basic_lighting')
            
    def add_renderable(self, renderable: Renderable3D):
        """Add a 3D object to the scene"""
        self.renderables.append(renderable)
        
    def remove_renderable(self, renderable: Renderable3D):
        """Remove a 3D object from the scene"""
        if renderable in self.renderables:
            self.renderables.remove(renderable)
            
    def add_light(self, light: Light):
        """Add a light to the scene"""
        self.lights.append(light)
        
    def remove_light(self, light: Light):
        """Remove a light from the scene"""
        if light in self.lights:
            self.lights.remove(light)
            
    def clear_renderables(self):
        """Remove all renderable objects"""
        self.renderables.clear()
        
    def clear_lights(self):
        """Remove all lights"""
        self.lights.clear()
        
    def render(self, camera):
        """Render the entire 3D scene"""
        if not self.current_shader:
            return
            
        # Bind shader program
        self.current_shader.use()
        
        # Set camera uniforms
        self._set_camera_uniforms(camera)
        
        # Set lighting uniforms
        self._set_lighting_uniforms()
        
        # Render each object
        for renderable in self.renderables:
            self._render_object(renderable)
            
    def _set_camera_uniforms(self, camera):
        """Set camera-related uniforms in the shader"""
        self.current_shader['view_matrix'].write(camera.get_view_matrix().tobytes())
        self.current_shader['projection_matrix'].write(camera.get_projection_matrix().tobytes())
        
    def _set_lighting_uniforms(self):
        """Set lighting uniforms in the shader"""
        # Set ambient light
        if self.lights:
            ambient_light = next((light for light in self.lights if isinstance(light, AmbientLight)), None)
            if ambient_light:
                self.current_shader['ambient_light_intensity'].value = ambient_light.intensity
                self.current_shader['ambient_light_color'].write(ambient_light.color)
                
        # Set directional lights
        directional_lights = [light for light in self.lights if isinstance(light, DirectionalLight)]
        for i, light in enumerate(directional_lights[:4]):  # Limit to 4 directional lights
            prefix = f'directional_lights[{i}]'
            self.current_shader[f'{prefix}.direction'].write(light.direction)
            self.current_shader[f'{prefix}.intensity'].value = light.intensity
            self.current_shader[f'{prefix}.color'].write(light.color)
            
        # Set point lights
        point_lights = [light for light in self.lights if isinstance(light, PointLight)]
        for i, light in enumerate(point_lights[:4]):  # Limit to 4 point lights
            prefix = f'point_lights[{i}]'
            self.current_shader[f'{prefix}.position'].write(light.position)
            self.current_shader[f'{prefix}.intensity'].value = light.intensity
            self.current_shader[f'{prefix}.color'].write(light.color)
            
        # Set number of active lights
        self.current_shader['num_directional_lights'].value = len(directional_lights)
        self.current_shader['num_point_lights'].value = len(point_lights)
        
    def _render_object(self, renderable: Renderable3D):
        """Render a single 3D object"""
        mesh = renderable.get_mesh()
        material = renderable.get_material()
        model_matrix = renderable.get_transform()
        
        # Set model matrix
        self.current_shader['model_matrix'].write(model_matrix.tobytes())
        
        # Set material properties
        self.current_shader['object_color'].write(material['color'])
        
        # Bind vertex array and render
        mesh.vao.render(moderngl.TRIANGLES)
        
    def create_basic_scene(self):
        """Create a basic 3D scene for testing"""
        # Create some basic geometry
        cube_mesh = create_cube()
        plane_mesh = create_plane()
        sphere_mesh = create_sphere()
        
        # Create renderable objects
        cube = SimpleRenderable(cube_mesh, color=(1.0, 0.0, 0.0, 1.0), position=(0, 0, 2))
        plane = SimpleRenderable(plane_mesh, color=(0.5, 0.5, 0.5, 1.0), position=(0, 0, 0))
        sphere = SimpleRenderable(sphere_mesh, color=(0.0, 1.0, 0.0, 1.0), position=(3, 0, 2))
        
        # Add to scene
        self.add_renderable(plane)
        self.add_renderable(cube)
        self.add_renderable(sphere)
        
    def get_render_stats(self) -> Dict[str, int]:
        """Get rendering statistics"""
        return {
            'num_renderables': len(self.renderables),
            'num_lights': len(self.lights),
            'current_shader': self.current_shader.name if self.current_shader else 'None'
        }