"""3D car rendering system with colored spheres and motion trails."""

import numpy as np
from OpenGL.GL import *
from typing import Dict, List, Tuple, Optional, Any
from ..rendering.utils import create_vao
import logging
import ctypes

logger = logging.getLogger(__name__)


class CarRenderer:
    """Renders cars as 3D spheres with driver-specific colors."""
    
    def __init__(self):
        self.sphere_mesh = None
        self._create_sphere_mesh()
    
    def _create_sphere_mesh(self, rings: int = 8, sectors: int = 12):
        """Create UV-sphere geometry for car representation."""
        vertices = []
        normals = []
        texcoords = []
        indices = []
        
        r = 1.0  # Base radius, will scale based on speed
        
        # Generate vertices
        for ring in range(rings + 1):
            r0 = np.pi * ring / rings
            y0 = np.cos(r0) * r
            
            for sector in range(sectors + 1):
                s0 = 2 * np.pi * sector / sectors
                x0 = np.sin(r0) * np.cos(s0) * r
                z0 = np.sin(r0) * np.sin(s0) * r
                
                vertices.extend([x0, y0, z0])
                normals.extend([np.sin(r0) * np.cos(s0), np.cos(r0), np.sin(r0) * np.sin(s0)])
                texcoords.extend([sector / sectors, ring / rings])
        
        # Generate indices
        for ring in range(rings):
            for sector in range(sectors):
                current = ring * (sectors + 1) + sector
                next_sector = current + sectors + 1
                
                # Two triangles per quad
                indices.extend([
                    current, next_sector, current + 1,
                    next_sector, next_sector + 1, current + 1
                ])
        
        # Create VAO
        vertex_data = []
        for i in range(len(vertices) // 3):
            vertex_data.extend(vertices[i*3:i*3+3])
            vertex_data.extend(normals[i*3:i*3+3])
            vertex_data.extend(texcoords[i*2:i*2+2])
        
        vertices_array = np.array(vertex_data, dtype=np.float32)
        indices_array = np.array(indices, dtype=np.uint32)
        
        self.sphere_vao, self.sphere_vbo, self.sphere_ebo = create_vao(
            vertices_array, 
            indices_array,
            attributes=[(0, 3, 0, 32), (1, 3, 12, 32), (2, 2, 24, 32)]
        )
        self.index_count = len(indices_array)
        logger.info(f"Car sphere mesh created: {len(vertices_array)} vertices, {self.index_count} indices")
    
    def render_cars_instanced(self, car_positions: List[np.ndarray], 
                             car_colors: List[Tuple[float, float, float]],
                             car_scales: List[float],
                             drs_active: List[bool] = None,
                             shader_program: int = None):
        """Render all cars with instancing for performance."""
        if shader_program is None or self.sphere_vao is None:
            logger.warning("Cannot render cars: shader or mesh not available")
            return
        
        if not car_positions or not car_colors:
            return
        
        # Prepare instancing data
        num_cars = len(car_positions)
        instance_data = []
        
        for i in range(num_cars):
            position = car_positions[i]
            color = car_colors[i]
            scale = car_scales[i] if i < len(car_scales) else 1.0
            
            # Adjust scale slightly if DRS is active (visual cue)
            if drs_active and i < len(drs_active) and drs_active[i]:
                scale *= 1.2  # Slightly larger when DRS active
            
            # Instance data format: [position(3), color(3), scale(1), padding(1)]
            instance_data.extend([position[0], position[1], position[2]])
            instance_data.extend([color[0], color[1], color[2]])
            instance_data.extend([scale, 0.0])  # Add padding for alignment
        
        instance_array = np.array(instance_data, dtype=np.float32)
        
        # Create instance buffer
        instance_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, instance_vbo)
        glBufferData(GL_ARRAY_BUFFER, instance_array.nbytes, instance_array, GL_STATIC_DRAW)
        
        glBindVertexArray(self.sphere_vao)
        
        # Set up instanced attributes
        # Location 3: position offset
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))
        glVertexAttribDivisor(3, 1)
        
        # Location 4: color
        glEnableVertexAttribArray(4)
        glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))
        glVertexAttribDivisor(4, 1)
        
        # Location 5: scale
        glEnableVertexAttribArray(5)
        glVertexAttribPointer(5, 1, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(24))
        glVertexAttribDivisor(5, 1)
        
        # Render instanced spheres
        glUseProgram(shader_program)
        glDrawElementsInstanced(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None, num_cars)
        
        # Cleanup
        glBindVertexArray(0)
        glDeleteBuffers(1, [instance_vbo])
    
    def cleanup(self):
        """Clean up OpenGL resources."""
        if hasattr(self, 'sphere_vao') and self.sphere_vao:
            glDeleteVertexArrays(1, [self.sphere_vao])
        if hasattr(self, 'sphere_vbo') and self.sphere_vbo:
            glDeleteBuffers(1, [self.sphere_vbo])
        if hasattr(self, 'sphere_ebo') and self.sphere_ebo:
            glDeleteBuffers(1, [self.sphere_ebo])


class TrailRenderer:
    """Renders motion trails behind cars."""
    
    def __init__(self, max_trail_length: int = 100, fade_time: float = 2.0):
        self.max_trail_length = max_trail_length
        self.fade_time = fade_time
        self.trail_data: Dict[str, list] = {}
        self.trail_vao = None
        self.trail_vbo = None
        
    def update_trail(self, driver_id: str, position: np.ndarray, 
                    speed: float = 0.0, drs_active: bool = False,
                    timestamp: float = 0.0):
        """Add a new position to driver's trail."""
        if driver_id not in self.trail_data:
            self.trail_data[driver_id] = {
                'positions': [],
                'speeds': [],
                'drs_active': [],
                'timestamps': []
            }
        
        trail = self.trail_data[driver_id]
        
        # Add new position
        trail['positions'].append(position.copy())
        trail['speeds'].append(speed)
        trail['drs_active'].append(drs_active)
        trail['timestamps'].append(timestamp)
        
        # Keep only max_trail_length recent positions
        if len(trail['positions']) > self.max_trail_length:
            trail['positions'].pop(0)
            trail['speeds'].pop(0)
            trail['drs_active'].pop(0)
            trail['timestamps'].pop(0)
    
    def render_trails(self, current_time: float, shader_program: int,
                     view_matrix: np.ndarray, projection_matrix: np.ndarray):
        """Render all active trails."""
        if not self.trail_data or shader_program == 0:
            return
        
        # Prepare trail data for rendering
        all_vertices = []
        all_colors = []
        all_ages = []
        
        for driver_id, trail in self.trail_data.items():
            positions = trail['positions']
            if len(positions) < 2:
                continue
            
            # Generate trail vertices (line strip)
            segment_verts = []
            segment_colors = []
            segment_ages = []
            
            for i in range(len(positions) - 1):
                pos1 = positions[i]
                pos2 = positions[i + 1]
                
                # Calculate midpoint for vertex
                mid_pos = (pos1 + pos2) / 2.0
                segment_verts.extend(mid_pos)
                
                # Color based on DRS and speed
                speed = trail['speeds'][i]
                drs_active = trail['drs_active'][i]
                timestamp = trail['timestamps'][i]
                
                # Speed to color (green slow → red fast)
                speed_ratio = min(speed / 300.0, 1.0)  # 300 kph = max red
                r = speed_ratio
                g = 1.0 - speed_ratio
                b = 0.2
                
                # Boost brightness if DRS active
                if drs_active:
                    r = min(r * 1.5, 1.0)
                    b = min(b * 2.0, 1.0)
                
                segment_colors.extend([r, g, b])
                
                # Age/distance calculation
                age = current_time - timestamp
                segment_ages.append(age)
            
            all_vertices.extend(segment_verts)
            all_colors.extend(segment_colors)
            all_ages.extend(segment_ages)
        
        if not all_vertices:
            return
        
        # Create VAO/VBO for trail rendering
        if self.trail_vao is None:
            self.trail_vao = glGenVertexArrays(1)
            self.trail_vbo = glGenBuffers(1)
        
        # Combine all data
        total_floats = len(all_vertices) + len(all_colors) + len(all_ages)
        trail_data = np.zeros(total_floats, dtype=np.float32)
        
        # Fill interleaved data [pos(3), color(3), age(1), padding(1)]
        idx = 0
        for i in range(len(all_vertices) // 3):
            trail_data[idx:idx+3] = all_vertices[i*3:i*3+3]  # position
            idx += 3
            trail_data[idx:idx+3] = all_colors[i*3:i*3+3]    # color
            idx += 3
            trail_data[idx] = all_ages[i] / self.fade_time   # age normalized
            idx += 2  # padding
        
        # Upload to GPU
        glBindVertexArray(self.trail_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.trail_vbo)
        glBufferData(GL_ARRAY_BUFFER, trail_data.nbytes, trail_data, GL_DYNAMIC_DRAW)
        
        # Setup attributes
        stride = 36  # 9 floats * 4 bytes
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(0))
        
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(12))
        
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, 36, ctypes.c_void_p(24))
        
        # Set uniforms
        glUseProgram(shader_program)
        glUniformMatrix4fv(glGetUniformLocation(shader_program, "view"), 1, GL_FALSE, view_matrix)
        glUniformMatrix4fv(glGetUniformLocation(shader_program, "projection"), 1, GL_FALSE, projection_matrix)
        
        # Render points (will be expanded by geometry shader into quads)
        num_points = len(all_vertices) // 3
        glDrawArrays(GL_POINTS, 0, num_points)
        
        glBindVertexArray(0)
    
    def clear_trail(self, driver_id: str):
        """Clear a specific driver's trail."""
        if driver_id in self.trail_data:
            self.trail_data[driver_id] = {
                'positions': [],
                'speeds': [],
                'drs_active': [],
                'timestamps': []
            }
    
    def clear_all_trails(self):
        """Clear all trails."""
        self.trail_data.clear()
    
    def cleanup(self):
        """Clean up OpenGL resources."""
        if self.trail_vao:
            glDeleteVertexArrays(1, [self.trail_vao])
        if self.trail_vbo:
            glDeleteBuffers(1, [self.trail_vbo])


class VehicleManager:
    """Manages all vehicle rendering (cars + trails)."""
    
    def __init__(self, car_shader: int, trail_shader: int):
        self.car_renderer = CarRenderer()
        self.trail_renderer = TrailRenderer()
        self.car_shader = car_shader
        self.trail_shader = trail_shader
        
    def render(self, frame_data: Dict[str, Any], current_time: float,
               view_matrix: np.ndarray, projection_matrix: np.ndarray):
        """Render cars and their trails for current frame."""
        # Extract data for rendering
        car_positions = []
        car_colors = []
        car_scales = []
        drs_active = []
        
        for driver_id, car_data in frame_data.items():
            if driver_id in ("weather", "track_status") or "X" not in car_data:
                continue
            
            # Position (Y is height)
            pos = np.array([car_data["X"], 1.0, car_data["Y"]], dtype=np.float32)
            car_positions.append(pos)
            
            # Color
            color = car_data.get("color", (1.0, 0.0, 0.0))
            car_colors.append(color)
            
            # Scale based on speed
            speed = car_data.get("Speed", 0.0)
            scale = 0.5 + (speed / 300.0) * 0.5  # 0.5 to 1.0 based on speed
            car_scales.append(scale)
            
            # DRS status
            drs = car_data.get("DRS", False)
            drs_active.append(drs)
            
            # Update trail
            self.trail_renderer.update_trail(
                driver_id, pos, speed, drs, current_time
            )
        
        # Render trails first (behind cars)
        self.trail_renderer.render_trails(
            current_time, self.trail_shader, 
            view_matrix, projection_matrix
        )
        
        # Render cars
        self.car_renderer.render_cars_instanced(
            car_positions, car_colors, car_scales, 
            drs_active, self.car_shader
        )
    
    def cleanup(self):
        """Clean up all resources."""
        self.car_renderer.cleanup()
        self.trail_renderer.cleanup()
