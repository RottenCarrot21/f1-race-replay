"""
Batch Renderer for efficient rendering of multiple similar objects
Optimizes rendering by combining geometry and using instanced rendering
"""

import moderngl
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from .renderer import SimpleRenderable
from .shaders import ShaderManager


class BatchRenderer3D:
    """
    Batch renderer for efficiently rendering many similar objects using instanced rendering
    """
    
    def __init__(self, ctx: moderngl.Context):
        self.ctx = ctx
        self.shader_manager = ShaderManager()
        
        # Batch data storage
        self.batch_data: List[Dict[str, Any]] = []
        self.current_mesh = None
        self.current_material = None
        
        # OpenGL buffers
        self.instance_vbo = None
        self.instance_vao = None
        
        # Current shader
        self.current_shader = None
        self.set_shader('instanced')
        
    def set_shader(self, shader_name: str):
        """Set the shader for instanced rendering"""
        self.current_shader = self.shader_manager.get_shader(shader_name, self.ctx)
        if not self.current_shader:
            self.current_shader = self.shader_manager.get_shader('basic_lighting', self.ctx)
            
    def begin_batch(self, mesh, material_type: str = 'basic'):
        """Start a new batch with specified mesh and material type"""
        self.current_mesh = mesh
        self.current_material = {
            'type': material_type,
            'properties': {}
        }
        self.batch_data = []
        
    def add_instance(self, 
                    position: Tuple[float, float, float] = (0, 0, 0),
                    rotation: Tuple[float, float, float] = (0, 0, 0),
                    scale: Tuple[float, float, float] = (1, 1, 1),
                    color: Tuple[float, float, float, float] = (1, 1, 1, 1)):
        """Add an instance to the current batch"""
        if self.current_mesh is None:
            return
            
        instance_data = {
            'position': np.array(position, dtype=np.float32),
            'rotation': np.array(rotation, dtype=np.float32),
            'scale': np.array(scale, dtype=np.float32),
            'color': np.array(color, dtype=np.float32)
        }
        
        self.batch_data.append(instance_data)
        
    def add_grid_instances(self, 
                          grid_size: int = 10,
                          spacing: float = 2.0,
                          position_offset: Tuple[float, float, float] = (0, 0, 0),
                          rotation_offset: Tuple[float, float, float] = (0, 0, 0),
                          scale: Tuple[float, float, float] = (1, 1, 1),
                          color: Tuple[float, float, float, float] = (1, 1, 1, 1)):
        """Add a grid of instances efficiently"""
        if self.current_mesh is None:
            return
            
        half_size = grid_size // 2
        
        for x in range(-half_size, half_size):
            for z in range(-half_size, half_size):
                position = (
                    position_offset[0] + x * spacing,
                    position_offset[1],
                    position_offset[2] + z * spacing
                )
                self.add_instance(position, rotation_offset, scale, color)
                
    def add_circle_instances(self,
                            center: Tuple[float, float, float] = (0, 0, 0),
                            radius: float = 10.0,
                            count: int = 20,
                            rotation_offset: Tuple[float, float, float] = (0, 0, 0),
                            scale: Tuple[float, float, float] = (1, 1, 1),
                            color: Tuple[float, float, float, float] = (1, 1, 1, 1)):
        """Add instances arranged in a circle"""
        if self.current_mesh is None:
            return
            
        import math
        
        for i in range(count):
            angle = 2 * math.pi * i / count
            x = center[0] + radius * math.cos(angle)
            y = center[1]
            z = center[2] + radius * math.sin(angle)
            
            position = (x, y, z)
            self.add_instance(position, rotation_offset, scale, color)
            
    def end_batch(self, camera):
        """End current batch and render all instances"""
        if not self.batch_data or self.current_mesh is None:
            return
            
        self._create_instance_buffers()
        self._render_batch(camera)
        
    def _create_instance_buffers(self):
        """Create OpenGL buffers for instanced data"""
        # Instance data layout: position(3), rotation(3), scale(3), color(4) = 13 floats per instance
        num_instances = len(self.batch_data)
        instance_data = np.zeros((num_instances, 13), dtype=np.float32)
        
        for i, data in enumerate(self.batch_data):
            instance_data[i, 0:3] = data['position']      # position
            instance_data[i, 3:6] = data['rotation']      # rotation
            instance_data[i, 6:9] = data['scale']         # scale
            instance_data[i, 9:13] = data['color']        # color
            
        # Create instance buffer
        if self.instance_vbo:
            self.instance_vbo.release()
            
        self.instance_vbo = self.ctx.buffer(instance_data.tobytes())
        
    def _render_batch(self, camera):
        """Render the current batch using instanced rendering"""
        if not self.current_shader or not self.instance_vbo:
            return
            
        # Bind shader
        self.current_shader.use()
        
        # Set camera uniforms
        self.current_shader['view_matrix'].write(camera.get_view_matrix().tobytes())
        self.current_shader['projection_matrix'].write(camera.get_projection_matrix().tobytes())
        
        # Create vertex array with instance data
        if self.instance_vao:
            self.instance_vao.release()
            
        # Format: position(3), normal(3), uv(2) for vertices, then instance data (13 floats)
        vertex_format = '3f 3f 2f 3f 3f 3f 4f'
        
        # Create VAO
        self.instance_vao = self.ctx.vertex_array(
            self.current_shader.program,
            [
                (self.current_mesh.vbo, vertex_format, 'in_position', 'in_normal', 'in_uv'),
                (self.instance_vbo, '3f 3f 3f 4f', 'instance_position', 'instance_rotation', 'instance_scale', 'instance_color')
            ]
        )
        
        # Render instances
        self.instance_vao.render(instances=len(self.batch_data))
        
    def render_immediate(self, renderables: List[SimpleRenderable], camera):
        """Render a list of renderables immediately (non-batched)"""
        if not renderables:
            return
            
        # Set shader
        if not self.current_shader:
            self.current_shader = self.shader_manager.get_shader('basic_lighting', self.ctx)
            
        self.current_shader.use()
        
        # Set camera uniforms
        self.current_shader['view_matrix'].write(camera.get_view_matrix().tobytes())
        self.current_shader['projection_matrix'].write(camera.get_projection_matrix().tobytes())
        
        # Render each renderable
        for renderable in renderables:
            if renderable.get_mesh():
                mesh = renderable.get_mesh()
                model_matrix = renderable.get_transform()
                material = renderable.get_material()
                
                # Set model matrix and color
                self.current_shader['model_matrix'].write(model_matrix.tobytes())
                self.current_shader['object_color'].write(material['color'])
                
                # Render mesh
                mesh.vao.render(moderngl.TRIANGLES)
                
    def clear(self):
        """Clear all batch data and buffers"""
        self.batch_data = []
        self.current_mesh = None
        self.current_material = None
        
        if self.instance_vbo:
            self.instance_vbo.release()
            self.instance_vbo = None
            
        if self.instance_vao:
            self.instance_vao.release()
            self.instance_vao = None
            
    def get_stats(self) -> Dict[str, Any]:
        """Get batch rendering statistics"""
        return {
            'num_instances_in_batch': len(self.batch_data),
            'current_shader': self.current_shader.name if self.current_shader else 'None',
            'has_active_batch': self.current_mesh is not None
        }
        
    def __del__(self):
        """Cleanup OpenGL resources"""
        if hasattr(self, 'instance_vbo') and self.instance_vbo:
            self.instance_vbo.release()
        if hasattr(self, 'instance_vao') and self.instance_vao:
            self.instance_vao.release()