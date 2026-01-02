"""3D track mesh generation from F1 telemetry data."""

import numpy as np
from OpenGL.GL import *
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class TrackMeshBuilder:
    """Generates 3D track mesh from 2D telemetry boundaries."""
    
    def __init__(self):
        self.vertices = []
        self.indices = []
        self.normals = []
        self.texcoords = []
        self.vertex_array = None  # OpenGL VAO
        self.index_count = 0
        
    def build_from_boundaries(self, middle_line: np.ndarray, 
                             inner_boundary: np.ndarray, 
                             outer_boundary: np.ndarray,
                             track_width: float = 15.0,
                             add_sidewalls: bool = True,
                             add_terrain: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        Build 3D track mesh from 2D boundary data.
        
        Args:
            middle_line: Nx2 array of track centerline points
            inner_boundary: Nx2 array of inner track boundary
            outer_boundary: Nx2 array of outer track boundary  
            track_width: Average track width for elevation modeling
            add_sidewalls: Whether to add vertical track walls
            add_terrain: Whether to add surrounding terrain
            
        Returns:
            Tuple of (vertices, indices) arrays
        """
        logger.info("Building 3D track mesh from telemetry data")
        
        # Interpolate boundaries to ensure consistent point counts
        inner_interp = self._interpolate_boundary(inner_boundary, num_points=2000)
        outer_interp = self._interpolate_boundary(outer_boundary, num_points=2000)
        
        # Generate track surface mesh (main racing surface)
        self._generate_track_surface(inner_interp, outer_interp)
        
        # Generate curbs (raised sections at track edges)
        self._generate_curbs(inner_interp, outer_interp)
        
        # Add vertical walls if requested
        if add_sidewalls:
            self._generate_sidewalls(inner_interp, outer_boundary)
        
        # Add surrounding terrain
        if add_terrain:
            self._generate_terrain(outer_boundary)
        
        # Convert to numpy arrays
        vertices = np.array(self.vertices, dtype=np.float32)
        indices = np.array(self.indices, dtype=np.uint32)
        
        # Create OpenGL buffers only if we have valid geometry
        if len(vertices) > 0 and len(indices) > 0:
            self._create_opengl_buffers(vertices, indices)
        
        self.index_count = len(indices)
        logger.info(f"Track mesh created: {len(vertices)} vertices, {len(indices)} indices")
        
        return vertices, indices
    
    def _interpolate_boundary(self, boundary: np.ndarray, num_points: int = 2000) -> np.ndarray:
        """Interpolate boundary to have consistent number of points."""
        if len(boundary) == 0:
            logger.warning("Empty boundary provided")
            return boundary
            
        # Remove duplicates and ensure it's a proper 2D array
        boundary = np.unique(boundary, axis=0)
        
        if len(boundary) < 2:
            logger.warning(f"Boundary has insufficient points: {len(boundary)}")
            return boundary
        
        # Calculate cumulative distance along boundary
        distances = np.sqrt(np.sum(np.diff(boundary, axis=0)**2, axis=1))
        cum_dist = np.concatenate([[0], np.cumsum(distances)])
        
        # Interpolate to target number of points
        target_dist = np.linspace(0, cum_dist[-1], num_points)
        
        # Interpolate x and y separately
        x_interp = np.interp(target_dist, cum_dist, boundary[:, 0])
        y_interp = np.interp(target_dist, cum_dist, boundary[:, 1])
        
        return np.column_stack([x_interp, y_interp])
    
    def _generate_track_surface(self, inner_boundary: np.ndarray, 
                               outer_boundary: np.ndarray):
        """Generate main track surface mesh."""
        logger.debug("Generating track surface")
        
        # Track is relatively flat, add slight elevation for banking
        vertices = []
        base_height = 0.0  # Base elevation
        
        # Generate vertices for inner and outer boundaries
        for i, (inner_point, outer_point) in enumerate(zip(inner_boundary, outer_boundary)):
            # Calculate along-track progress for texture coordinates
            progress = i / len(inner_boundary)
            
            # Add some banking based on curvature (simple approximation)
            banking = self._calculate_banking(i, inner_boundary, outer_boundary)
            
            # Inner boundary vertex
            inner_pos = np.array([
                inner_point[0], 
                base_height + banking,  
                inner_point[1]
            ], dtype=np.float32)
            inner_normal = self._calculate_normal(inner_point, outer_point)
            
            # Outer boundary vertex  
            outer_pos = np.array([
                outer_point[0], 
                base_height + banking,
                outer_point[1]
            ], dtype=np.float32)
            outer_normal = self._calculate_normal(outer_point, inner_point, invert=True)
            
            # Multi-texture coordinates
            inner_tex = np.array([progress, 0.0], dtype=np.float32)  # Along track, inner edge
            outer_tex = np.array([progress, 1.0], dtype=np.float32)  # Along track, outer edge
            
            vertices.append({
                'position': inner_pos,
                'normal': inner_normal,
                'texcoord': inner_tex
            })
            vertices.append({
                'position': outer_pos,
                'normal': outer_normal, 
                'texcoord': outer_tex
            })
        
        # Generate triangle strips
        vertex_offset = len(self.vertices) // 8  # 8 floats per vertex (3 pos, 3 norm, 2 tex)
        
        for i in range(0, len(inner_boundary) - 1):
            # Two triangles per quad
            # Triangle 1: current inner, current outer, next inner
            self.indices.extend([
                vertex_offset + i * 2,      # current inner
                vertex_offset + i * 2 + 1,  # current outer  
                vertex_offset + (i + 1) * 2  # next inner
            ])
            
            # Triangle 2: current outer, next outer, next inner
            self.indices.extend([
                vertex_offset + i * 2 + 1,      # current outer
                vertex_offset + (i + 1) * 2 + 1,  # next outer
                vertex_offset + (i + 1) * 2       # next inner
            ])
        
        # Add vertices to main list (flattened)
        for v in vertices:
            self.vertices.extend(v['position'])
            self.vertices.extend(v['normal'])
            self.vertices.extend(v['texcoord'])
            self.normals.extend(v['normal'])
            self.texcoords.extend(v['texcoord'])
    
    def _generate_curbs(self, inner_boundary: np.ndarray, 
                       outer_boundary: np.ndarray, curb_height: float = 0.15):
        """Generate raised curb geometry at track edges."""
        logger.debug("Generating curbs")
        
        vertex_offset = len(self.vertices) // 8
        
        for i, (inner_point, outer_point) in enumerate(zip(inner_boundary, outer_boundary)):
            progress = i / len(inner_boundary)
            
            # Inner curb
            inner_pos_base = np.array([inner_point[0], 0.0, inner_point[1]], dtype=np.float32)
            inner_pos_top = np.array([inner_point[0], curb_height, inner_point[1]], dtype=np.float32)
            
            # Outer curb
            outer_pos_base = np.array([outer_point[0], 0.0, outer_point[1]], dtype=np.float32)
            outer_pos_top = np.array([outer_point[0], curb_height, outer_point[1]], dtype=np.float32)
            
            # Add curb vertices (simplified as planes)
            # TODO: Add proper curb geometry with chamfers
            if i % 10 == 0:  # Sampled to reduce vertex count
                self.vertices.extend(inner_pos_top)
                self.vertices.extend([0.0, 1.0, 0.0])  # normal
                self.vertices.extend([progress, 0.0])  # texcoord
    
    def _generate_sidewalls(self, inner_boundary: np.ndarray, 
                           outer_boundary: np.ndarray, wall_height: float = 3.0):
        """Generate vertical walls for track boundary definition."""
        logger.debug("Generating sidewalls")
        
        # Add barrier walls at track edges
        for i, (inner_point, outer_point) in enumerate(zip(inner_boundary, outer_boundary)):
            if i % 20 == 0:  # Sampled for performance
                progress = i / len(inner_boundary)
                
                # Inner wall
                inner_bottom = np.array([inner_point[0], 0.0, inner_point[1]], dtype=np.float32)
                inner_top = np.array([inner_point[0], wall_height, inner_point[1]], dtype=np.float32)
                
                # Add wall vertices
                self.vertices.extend(inner_bottom)
                self.vertices.extend([1.0, 0.0, 0.0])  # normal pointing outward
                self.vertices.extend([progress, 0.0])
                
                self.vertices.extend(inner_top)
                self.vertices.extend([1.0, 0.0, 0.0])  # normal
                self.vertices.extend([progress, 1.0])
    
    def _generate_terrain(self, outer_boundary: np.ndarray, 
                         terrain_width: float = 50.0):
        """Generate simple surrounding terrain."""
        logger.debug("Generating terrain")
        
        # Create ground plane around track
        min_x = np.min(outer_boundary[:, 0]) - terrain_width
        max_x = np.max(outer_boundary[:, 0]) + terrain_width
        min_z = np.min(outer_boundary[:, 1]) - terrain_width
        max_z = np.max(outer_boundary[:, 1]) + terrain_width
        
        terrain_vertices = [
            # Ground plane
            [min_x, -2.0, min_z], [0.0, 1.0, 0.0], [0.0, 0.0],
            [max_x, -2.0, min_z], [0.0, 1.0, 0.0], [1.0, 0.0],
            [max_x, -2.0, max_z], [0.0, 1.0, 0.0], [1.0, 1.0],
            [min_x, -2.0, max_z], [0.0, 1.0, 0.0], [0.0, 1.0],
        ]
        
        # Add terrain vertices (appending to existing geometry)
        vertex_offset = len(self.vertices) // 8
        
        for vertex_data in terrain_vertices:
            self.vertices.extend(vertex_data)
        
        # Add indices for terrain quad
        self.indices.extend([
            vertex_offset, vertex_offset + 1, vertex_offset + 2,
            vertex_offset, vertex_offset + 2, vertex_offset + 3
        ])
    
    def _calculate_normal(self, point1: np.ndarray, point2: np.ndarray, 
                         invert: bool = False) -> np.ndarray:
        """Calculate normal vector between two points."""
        # For track surface, normal is mostly upward
        # Calculate sideways direction
        direction = point2 - point1
        normal = np.array([direction[1], 0.0, -direction[0]], dtype=np.float32)
        normal = normal / np.linalg.norm(normal)
        
        if invert:
            normal = -normal
        
        # Mix with upward direction for track surface
        normal = normal * 0.3 + np.array([0.0, 1.0, 0.0], dtype=np.float32) * 0.7
        return normal / np.linalg.norm(normal)
    
    def _calculate_banking(self, index: int, inner_boundary: np.ndarray, 
                          outer_boundary: np.ndarray) -> float:
        """Approximate track banking based on curvature."""
        # Look ahead and behind for curvature estimation
        look_ahead = 10
        look_behind = 10
        
        idx_ahead = min(index + look_ahead, len(inner_boundary) - 1)
        idx_behind = max(index - look_behind, 0)
        
        # Calculate vectors
        if idx_ahead == idx_behind:
            return 0.0
            
        direction_ahead = inner_boundary[idx_ahead] - inner_boundary[index]
        direction_behind = inner_boundary[index] - inner_boundary[idx_behind]
        
        # Calculate curvature (cross product magnitude)
        curvature = np.abs(np.cross(direction_ahead, direction_behind))
        
        # Convert to banking (simplified physics model)
        banking = np.tanh(curvature * 0.01) * 0.5  # Max 0.5m banking
        
        return banking
    
    def _create_opengl_buffers(self, vertices: np.ndarray, indices: np.ndarray):
        """Create OpenGL VAO/VBO for rendering."""
        try:
            # Create VAO
            self.vertex_array = glGenVertexArrays(1)
            glBindVertexArray(self.vertex_array)
            
            # Create VBO
            vbo = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
            
            # Create EBO
            ebo = glGenBuffers(1)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
            
            # Set up vertex attributes
            # Position (location 0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * 4, ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            
            # Normal (location 1)
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 8 * 4, ctypes.c_void_p(3 * 4))
            glEnableVertexAttribArray(1)
            
            # TexCoord (location 2)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 8 * 4, ctypes.c_void_p(6 * 4))
            glEnableVertexAttribArray(2)
            
            glBindVertexArray(0)  # Unbind
            
            logger.info("OpenGL buffers created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create OpenGL buffers: {e}")
    
    def render(self):
        """Render the track mesh."""
        if self.vertex_array:
            glBindVertexArray(self.vertex_array)
            glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
            glBindVertexArray(0)
    
    def cleanup(self):
        """Clean up OpenGL resources."""
        if self.vertex_array:
            glDeleteVertexArrays(1, [self.vertex_array])
            self.vertex_array = 0
        
        # Note: VBOs are automatically deleted when VAO is deleted
        # But if we stored them separately, we should delete them here
    
    def get_bounds(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get AABB bounds of the track."""
        vertices = np.array(self.vertices, dtype=np.float32)
        if len(vertices) == 0:
            return np.array([0, 0, 0]), np.array([1, 1, 1])
        
        vertices_3d = vertices.reshape(-1, 8)[:, :3]  # Extract position components
        min_bounds = np.min(vertices_3d, axis=0)
        max_bounds = np.max(vertices_3d, axis=0)
        
        return min_bounds, max_bounds
