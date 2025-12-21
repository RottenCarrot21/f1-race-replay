"""
Geometry generation and mesh management for 3D rendering
"""

import moderngl
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import math


class Mesh:
    """3D mesh with vertex data and OpenGL vertex array"""
    
    def __init__(self, ctx: moderngl.Context, vertices: np.ndarray, indices: Optional[np.ndarray] = None):
        self.ctx = ctx
        self.vertices = vertices
        self.indices = indices
        
        # Create OpenGL buffers
        self._create_gl_buffers()
        
    def _create_gl_buffers(self):
        """Create OpenGL vertex buffer objects"""
        # Vertex data layout: position (3), normal (3), uv (2) = 8 floats per vertex
        vertex_format = '3f 3f 2f'
        
        # Create vertex buffer
        self.vbo = self.ctx.buffer(self.vertices.tobytes())
        
        # Create index buffer if indices provided
        if self.indices is not None:
            self.ibo = self.ctx.buffer(self.indices.tobytes())
            self.num_vertices = len(self.indices)
        else:
            self.num_vertices = len(self.vertices)
            
        # Create vertex array object
        self.vao = self.ctx.vertex_array(
            self.ctx.program(
                vertex_shader="""
                    #version 330
                    
                    in vec3 in_position;
                    in vec3 in_normal;
                    in vec2 in_uv;
                    
                    uniform mat4 model_matrix;
                    uniform mat4 view_matrix;
                    uniform mat4 projection_matrix;
                    
                    out vec3 v_normal;
                    out vec2 v_uv;
                    
                    void main() {
                        // Calculate world position
                        vec4 world_pos = model_matrix * vec4(in_position, 1.0);
                        gl_Position = projection_matrix * view_matrix * world_pos;
                        
                        // Calculate normal (simplified - assumes uniform scaling)
                        v_normal = mat3(model_matrix) * in_normal;
                        v_uv = in_uv;
                    }
                """,
                fragment_shader="""
                    #version 330
                    
                    in vec3 v_normal;
                    in vec2 v_uv;
                    
                    uniform vec4 object_color;
                    uniform float ambient_light_intensity;
                    uniform vec3 ambient_light_color;
                    
                    // Directional light uniforms
                    #define MAX_DIR_LIGHTS 4
                    uniform int num_directional_lights;
                    uniform struct {
                        vec3 direction;
                        float intensity;
                        vec3 color;
                    } directional_lights[MAX_DIR_LIGHTS];
                    
                    // Point light uniforms
                    #define MAX_POINT_LIGHTS 4
                    uniform int num_point_lights;
                    uniform struct {
                        vec3 position;
                        float intensity;
                        vec3 color;
                    } point_lights[MAX_POINT_LIGHTS];
                    
                    out vec4 fragColor;
                    
                    void main() {
                        vec3 normal = normalize(v_normal);
                        vec3 lighting = ambient_light_color * ambient_light_intensity;
                        
                        // Directional lights
                        for (int i = 0; i < num_directional_lights && i < MAX_DIR_LIGHTS; i++) {
                            vec3 light_dir = normalize(-directional_lights[i].direction);
                            float diff = max(dot(normal, light_dir), 0.0);
                            lighting += directional_lights[i].color * diff * directional_lights[i].intensity;
                        }
                        
                        // Point lights (simplified distance calculation)
                        for (int i = 0; i < num_point_lights && i < MAX_POINT_LIGHTS; i++) {
                            vec3 light_dir = normalize(point_lights[i].position - vec3(0.0)); // Assuming object at origin for now
                            float diff = max(dot(normal, light_dir), 0.0);
                            float distance = length(point_lights[i].position - vec3(0.0));
                            float attenuation = 1.0 / (1.0 + 0.1 * distance + 0.01 * distance * distance);
                            lighting += point_lights[i].color * diff * point_lights[i].intensity * attenuation;
                        }
                        
                        vec3 final_color = object_color.rgb * lighting;
                        fragColor = vec4(final_color, object_color.a);
                    }
                """
            ),
            [
                (self.vbo, vertex_format, 'in_position', 'in_normal', 'in_uv')
            ]
        )


def create_cube(size: float = 1.0) -> Mesh:
    """Create a basic cube mesh"""
    # Cube vertices (position, normal, uv)
    vertices = np.array([
        # Front face
        [-size, -size,  size,  0, 0, 1,  0, 0],  # 0
        [ size, -size,  size,  0, 0, 1,  1, 0],  # 1
        [ size,  size,  size,  0, 0, 1,  1, 1],  # 2
        [-size,  size,  size,  0, 0, 1,  0, 1],  # 3
        
        # Back face
        [-size, -size, -size,  0, 0, -1,  0, 0],  # 4
        [-size,  size, -size,  0, 0, -1,  0, 1],  # 5
        [ size,  size, -size,  0, 0, -1,  1, 1],  # 6
        [ size, -size, -size,  0, 0, -1,  1, 0],  # 7
        
        # Top face
        [-size,  size,  size,  0, 1, 0,  0, 0],  # 8
        [ size,  size,  size,  0, 1, 0,  1, 0],  # 9
        [ size,  size, -size,  0, 1, 0,  1, 1],  # 10
        [-size,  size, -size,  0, 1, 0,  0, 1],  # 11
        
        # Bottom face
        [-size, -size,  size,  0, -1, 0,  0, 0],  # 12
        [-size, -size, -size,  0, -1, 0,  0, 1],  # 13
        [ size, -size, -size,  0, -1, 0,  1, 1],  # 14
        [ size, -size,  size,  0, -1, 0,  1, 0],  # 15
        
        # Right face
        [ size, -size,  size,  1, 0, 0,  0, 0],  # 16
        [ size, -size, -size,  1, 0, 0,  1, 0],  # 17
        [ size,  size, -size,  1, 0, 0,  1, 1],  # 18
        [ size,  size,  size,  1, 0, 0,  0, 1],  # 19
        
        # Left face
        [-size, -size,  size,  -1, 0, 0,  0, 0],  # 20
        [-size,  size,  size,  -1, 0, 0,  0, 1],  # 21
        [-size,  size, -size,  -1, 0, 0,  1, 1],  # 22
        [-size, -size, -size,  -1, 0, 0,  1, 0],  # 23
    ], dtype=np.float32)
    
    # Cube indices
    indices = np.array([
        # Front
        0, 1, 2, 0, 2, 3,
        # Back
        4, 5, 6, 4, 6, 7,
        # Top
        8, 9, 10, 8, 10, 11,
        # Bottom
        12, 13, 14, 12, 14, 15,
        # Right
        16, 17, 18, 16, 18, 19,
        # Left
        20, 21, 22, 20, 22, 23
    ], dtype=np.uint32)
    
    return Mesh(vertices=vertices, indices=indices)


def create_plane(size: float = 10.0) -> Mesh:
    """Create a basic plane mesh"""
    half_size = size / 2
    
    # Plane vertices (position, normal, uv)
    vertices = np.array([
        [-half_size, -half_size, 0,  0, 0, 1,  0, 0],  # Bottom left
        [ half_size, -half_size, 0,  0, 0, 1,  1, 0],  # Bottom right
        [ half_size,  half_size, 0,  0, 0, 1,  1, 1],  # Top right
        [-half_size,  half_size, 0,  0, 0, 1,  0, 1],  # Top left
    ], dtype=np.float32)
    
    # Plane indices
    indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
    
    return Mesh(vertices=vertices, indices=indices)


def create_sphere(radius: float = 1.0, rings: int = 16, sectors: int = 32) -> Mesh:
    """Create a sphere mesh"""
    vertices = []
    indices = []
    
    for ring in range(rings + 1):
        phi = math.pi * ring / rings
        cos_phi = math.cos(phi)
        sin_phi = math.sin(phi)
        
        for sector in range(sectors + 1):
            theta = 2 * math.pi * sector / sectors
            cos_theta = math.cos(theta)
            sin_theta = math.sin(theta)
            
            x = radius * sin_phi * cos_theta
            y = radius * sin_phi * sin_theta
            z = radius * cos_phi
            
            vertices.append([x, y, z, x/radius, y/radius, z/radius, sector/sectors, ring/rings])
    
    # Convert to numpy array
    vertices = np.array(vertices, dtype=np.float32)
    
    # Create indices
    for ring in range(rings):
        for sector in range(sectors):
            first = ring * (sectors + 1) + sector
            second = first + sectors + 1
            
            indices.extend([first, second, first + 1])
            indices.extend([second, second + 1, first + 1])
    
    indices = np.array(indices, dtype=np.uint32)
    
    return Mesh(vertices=vertices, indices=indices)


def create_cylinder(radius: float = 1.0, height: float = 2.0, segments: int = 32) -> Mesh:
    """Create a cylinder mesh"""
    vertices = []
    indices = []
    
    # Create vertices for the cylinder sides
    for i in range(segments + 1):
        theta = 2 * math.pi * i / segments
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        
        x = radius * cos_theta
        y = radius * sin_theta
        
        # Bottom vertex
        vertices.append([x, y, -height/2, cos_theta, sin_theta, 0, i/segments, 0])
        # Top vertex
        vertices.append([x, y, height/2, cos_theta, sin_theta, 0, i/segments, 1])
    
    # Create indices for the cylinder sides
    for i in range(segments):
        bottom1 = i * 2
        top1 = i * 2 + 1
        bottom2 = (i + 1) * 2
        top2 = (i + 1) * 2 + 1
        
        indices.extend([bottom1, top1, bottom2])
        indices.extend([top1, top2, bottom2])
    
    # Convert to numpy arrays
    vertices = np.array(vertices, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)
    
    return Mesh(vertices=vertices, indices=indices)