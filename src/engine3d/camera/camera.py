"""
3D Camera System with smooth transitions and orbital controls
Provides perspective projection and camera manipulation for 3D scenes
"""

import numpy as np
import math
from typing import Tuple, Optional
from typing import Union


class Camera3D:
    """
    3D Camera with orbital controls, smooth transitions, and proper projection matrices.
    Supports both perspective and orthographic projection for 2D/3D hybrid rendering.
    """
    
    def __init__(self, 
                 aspect_ratio: float = 1920/1200,
                 fov: float = 60.0,  # Field of view in degrees
                 near: float = 0.1,
                 far: float = 10000.0,
                 position: Tuple[float, float, float] = (0, -200, 400),
                 target: Tuple[float, float, float] = (0, 0, 0),
                 up: Tuple[float, float, float] = (0, 0, 1)):
        
        # Projection parameters
        self.aspect_ratio = aspect_ratio
        self.fov = fov
        self.near = near
        self.far = far
        
        # Camera position and orientation (spherical coordinates for orbital camera)
        self.distance = self._calculate_distance(position, target)
        self.theta = self._calculate_theta(position, target)  # Horizontal angle
        self.phi = self._calculate_phi(position, target)      # Vertical angle
        
        self.target = np.array(target, dtype=np.float32)
        self.up = np.array(up, dtype=np.float32)
        
        # Target values for smooth interpolation
        self.target_position = np.array(position, dtype=np.float32)
        self.target_theta = self.theta
        self.target_phi = self.phi
        self.target_distance = self.distance
        
        # Smoothing parameters
        self.smoothing_factor = 0.1
        self.smooth_transition = True
        
        # Update matrices
        self.update_matrices()
        
    def _calculate_distance(self, pos: Tuple[float, float, float], target: Tuple[float, float, float]) -> float:
        """Calculate distance from position to target"""
        pos_array = np.array(pos)
        target_array = np.array(target)
        return np.linalg.norm(pos_array - target_array)
        
    def _calculate_theta(self, pos: Tuple[float, float, float], target: Tuple[float, float, float]) -> float:
        """Calculate horizontal angle from position to target"""
        pos_array = np.array(pos)
        target_array = np.array(target)
        relative = pos_array - target_array
        return math.atan2(relative[1], relative[0])  # atan2(y, x)
        
    def _calculate_phi(self, pos: Tuple[float, float, float], target: Tuple[float, float, float]) -> float:
        """Calculate vertical angle from position to target"""
        pos_array = np.array(pos)
        target_array = np.array(target)
        relative = pos_array - target_array
        horizontal_dist = math.sqrt(relative[0]**2 + relative[1]**2)
        return math.atan2(relative[2], horizontal_dist)  # atan2(z, horizontal_dist)
        
    def spherical_to_cartesian(self, distance: float, theta: float, phi: float) -> np.ndarray:
        """Convert spherical coordinates to Cartesian"""
        x = distance * math.cos(phi) * math.cos(theta)
        y = distance * math.cos(phi) * math.sin(theta)
        z = distance * math.sin(phi)
        return np.array([x, y, z], dtype=np.float32)
        
    def get_position(self) -> np.ndarray:
        """Get current camera position"""
        return self.target + self.spherical_to_cartesian(self.distance, self.theta, self.phi)
        
    def get_target_position(self) -> np.ndarray:
        """Get target camera position for smooth transitions"""
        return self.target + self.spherical_to_cartesian(self.target_distance, self.target_theta, self.target_phi)
        
    def update_matrices(self):
        """Update projection and view matrices"""
        position = self.get_position()
        
        # View matrix (camera space to world space transformation)
        self.view_matrix = self._look_at(position, self.target, self.up)
        
        # Projection matrix
        self.projection_matrix = self._perspective(self.fov, self.aspect_ratio, self.near, self.far)
        
        # Combined matrix for shader transforms
        self.view_projection_matrix = self.projection_matrix @ self.view_matrix
        
    def _look_at(self, eye: np.ndarray, center: np.ndarray, up: np.ndarray) -> np.ndarray:
        """Create view matrix using look-at transformation"""
        f = center - eye
        f = f / np.linalg.norm(f)
        
        s = np.cross(f, up)
        s = s / np.linalg.norm(s)
        
        u = np.cross(s, f)
        
        # View matrix
        view = np.array([
            [ s[0],  s[1],  s[2], -np.dot(s, eye)],
            [ u[0],  u[1],  u[2], -np.dot(u, eye)],
            [-f[0], -f[1], -f[2],  np.dot(f, eye)],
            [    0,     0,     0,              1]
        ], dtype=np.float32)
        
        return view
        
    def _perspective(self, fov: float, aspect: float, near: float, far: float) -> np.ndarray:
        """Create perspective projection matrix"""
        f = 1.0 / math.tan(math.radians(fov) / 2.0)
        
        projection = np.array([
            [f / aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far + near) / (near - far), (2 * far * near) / (near - far)],
            [0, 0, -1, 0]
        ], dtype=np.float32)
        
        return projection
        
    def update(self):
        """Update camera for smooth transitions"""
        if self.smooth_transition:
            # Smoothly interpolate towards target values
            lerp_factor = self.smoothing_factor
            
            # Interpolate angles (handle wrap-around)
            theta_diff = self.target_theta - self.theta
            if theta_diff > math.pi:
                self.theta += (theta_diff - 2 * math.pi) * lerp_factor
            elif theta_diff < -math.pi:
                self.theta += (theta_diff + 2 * math.pi) * lerp_factor
            else:
                self.theta += theta_diff * lerp_factor
                
            # Interpolate phi and distance
            self.phi += (self.target_phi - self.phi) * lerp_factor
            self.distance += (self.target_distance - self.distance) * lerp_factor
            
        # Update matrices
        self.update_matrices()
        
    def set_position(self, position: Tuple[float, float, float]):
        """Set camera position (immediate update)"""
        self.target_position = np.array(position, dtype=np.float32)
        self.target_distance = self._calculate_distance(position, tuple(self.target))
        self.target_theta = self._calculate_theta(position, tuple(self.target))
        self.target_phi = self._calculate_phi(position, tuple(self.target))
        self.update()
        
    def set_target(self, target: Tuple[float, float, float]):
        """Set camera target point"""
        self.target = np.array(target, dtype=np.float32)
        
    def move_to(self, position: Tuple[float, float, float], target: Optional[Tuple[float, float, float]] = None):
        """Smoothly move camera to new position and target"""
        self.target_position = np.array(position, dtype=np.float32)
        
        if target is not None:
            self.target = np.array(target, dtype=np.float32)
            # Recalculate target angles based on new position and target
            self.target_distance = self._calculate_distance(position, target)
            self.target_theta = self._calculate_theta(position, target)
            self.target_phi = self._calculate_phi(position, target)
        else:
            # Maintain current target, just change position
            target_tuple = tuple(self.target)
            self.target_distance = self._calculate_distance(position, target_tuple)
            self.target_theta = self._calculate_theta(position, target_tuple)
            self.target_phi = self._calculate_phi(position, target_tuple)
            
    def rotate_around_target(self, delta_theta: float, delta_phi: float):
        """Rotate camera around target point (in radians)"""
        self.target_theta += delta_theta
        
        # Clamp phi to avoid camera flipping
        max_phi = math.pi / 2 - 0.1  # Slightly less than 90 degrees
        min_phi = -max_phi
        self.target_phi = max(min_phi, min(max_phi, self.target_phi))
        
    def pan(self, delta_x: float, delta_y: float):
        """Pan camera by moving target point"""
        # Convert screen delta to world delta
        scale = self.distance * 0.001  # Adjust sensitivity based on distance
        self.target[0] += delta_x * scale
        self.target[1] += delta_y * scale
        
    def zoom(self, zoom_factor: float):
        """Zoom in/out by changing distance"""
        # Limit zoom range
        min_distance = 10.0
        max_distance = 5000.0
        self.target_distance = max(min_distance, min(max_distance, self.target_distance * (1.0 - zoom_factor)))
        
    def set_aspect_ratio(self, aspect_ratio: float):
        """Update aspect ratio (call on window resize)"""
        self.aspect_ratio = aspect_ratio
        
    def get_view_matrix(self) -> np.ndarray:
        """Get view matrix for shaders"""
        return self.view_matrix
        
    def get_projection_matrix(self) -> np.ndarray:
        """Get projection matrix for shaders"""
        return self.projection_matrix
        
    def get_view_projection_matrix(self) -> np.ndarray:
        """Get combined view-projection matrix for shaders"""
        return self.view_projection_matrix
        
    def world_to_screen(self, world_point: np.ndarray) -> Tuple[float, float]:
        """Convert world coordinates to screen coordinates"""
        # Transform to clip space
        clip_space = self.view_projection_matrix @ np.append(world_point, 1.0)
        
        # Transform to normalized device coordinates
        ndc = clip_space[:3] / clip_space[3]
        
        # Transform to screen coordinates (assuming standard viewport)
        # This is a simplified conversion - actual implementation would need viewport info
        screen_x = (ndc[0] + 1.0) * 0.5 * 1920  # Assuming 1920 width
        screen_y = (ndc[1] + 1.0) * 0.5 * 1200  # Assuming 1200 height
        
        return screen_x, screen_y
        
    def screen_to_world(self, screen_x: float, screen_y: float, depth: float = 0.0) -> np.ndarray:
        """Convert screen coordinates to world coordinates (simplified)"""
        # This is a basic implementation - a full implementation would involve ray casting
        # For now, assume depth is in camera space
        ndc_x = (screen_x / 1920.0) * 2.0 - 1.0
        ndc_y = (screen_y / 1200.0) * 2.0 - 1.0
        
        # Transform back to world space (simplified)
        inverse_view_proj = np.linalg.inv(self.view_projection_matrix)
        world_point = inverse_view_proj @ np.array([ndc_x, ndc_y, depth, 1.0])
        
        return world_point[:3]