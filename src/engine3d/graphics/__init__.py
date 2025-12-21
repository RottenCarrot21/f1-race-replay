"""
3D Graphics Rendering Package
Provides advanced 3D rendering capabilities with ModernGL
"""

from .renderer import Renderer3D, SimpleRenderable, Renderable3D
from .geometry import Mesh, create_cube, create_plane, create_sphere, create_cylinder
from .shaders import ShaderManager, Shader, ShaderConfig
from .lighting import Light, AmbientLight, DirectionalLight, PointLight, SpotLight, LightManager
from .batch_renderer import BatchRenderer3D

__all__ = [
    'Renderer3D',
    'SimpleRenderable', 
    'Renderable3D',
    'Mesh',
    'create_cube',
    'create_plane', 
    'create_sphere',
    'create_cylinder',
    'ShaderManager',
    'Shader',
    'ShaderConfig',
    'Light',
    'AmbientLight',
    'DirectionalLight',
    'PointLight',
    'SpotLight',
    'LightManager',
    'BatchRenderer3D'
]