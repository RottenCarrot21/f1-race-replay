"""3D camera system for track visualization."""

import numpy as np
from typing import Tuple

try:
    import glm  # Optional: GLM library for better matrix math performance
    HAS_GLM = True
except ImportError:
    HAS_GLM = False  # Fall back to numpy operations


def perspective(fov: float, aspect: float, near: float, far: float) -> np.ndarray:
    """Create a perspective projection matrix."""
    f = 1.0 / np.tan(fov / 2.0)
    return np.array([
        [f / aspect, 0, 0, 0],
        [0, f, 0, 0],
        [0, 0, (far + near) / (near - far), (2 * far * near) / (near - far)],
        [0, 0, -1, 0]
    ], dtype=np.float32)


def look_at(eye: np.ndarray, center: np.ndarray, up: np.ndarray) -> np.ndarray:
    """Create a view matrix looking from eye to center."""
    f = center - eye
    f = f / np.linalg.norm(f)
    
    s = np.cross(f, up)
    s = s / np.linalg.norm(s)
    
    u = np.cross(s, f)
    
    return np.array([
        [s[0], s[1], s[2], -np.dot(s, eye)],
        [u[0], u[1], u[2], -np.dot(u, eye)],
        [-f[0], -f[1], -f[2], np.dot(f, eye)],
        [0, 0, 0, 1]
    ], dtype=np.float32)


class Camera3D:
    """3D camera with orbit controls for track viewing."""
    
    def __init__(self, width: int = 1920, height: int = 1080):
        self.position = np.array([0.0, 50.0, 100.0], dtype=np.float32)
        self.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        
        self.fov = np.radians(60.0)
        self.aspect = width / height
        self.near = 0.1
        self.far = 10000.0
        
        self.track_center = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.track_radius = 100.0
        
        self._update_vectors()
    
    def _update_vectors(self):
        """Update forward/right vectors from position and target."""
        self.forward = self.target - self.position
        self.forward = self.forward / np.linalg.norm(self.forward)
        
        self.right = np.cross(self.forward, self.up)
        self.right = self.right / np.linalg.norm(self.right)
    
    def set_track_bounds(self, points: np.ndarray):
        """Set track center and radius from track points."""
        self.track_center = np.mean(points, axis=0)
        distances = np.linalg.norm(points - self.track_center, axis=1)
        self.track_radius = np.max(distances) * 1.5
        
        # Set initial camera position
        self.position = self.track_center + np.array([
            self.track_radius, 
            self.track_radius * 0.3, 
            self.track_radius * 0.8
        ])
        self.target = self.track_center.copy()
    
    def orbit(self, delta_azimuth: float, delta_elevation: float):
        """
        Orbit camera around track center.
        
        Args:
            delta_azimuth: Horizontal rotation in radians
            delta_elevation: Vertical rotation in radians
        """
        # Get current offset from center
        offset = self.position - self.track_center
        distance = np.linalg.norm(offset)
        
        # Convert to spherical coordinates
        # Current angles
        current_azimuth = np.arctan2(offset[0], offset[2])
        current_elevation = np.arcsin(offset[1] / distance)
        
        # New angles
        new_azimuth = current_azimuth + delta_azimuth
        new_elevation = np.clip(current_elevation + delta_elevation, 
                              np.radians(-80), np.radians(80))
        
        # Convert back to cartesian
        self.position[0] = self.track_center[0] + distance * np.cos(new_elevation) * np.sin(new_azimuth)
        self.position[1] = self.track_center[1] + distance * np.sin(new_elevation)
        self.position[2] = self.track_center[2] + distance * np.cos(new_elevation) * np.cos(new_azimuth)
        
        # Keep target at track center
        self.target = self.track_center.copy()
        self._update_vectors()
    
    def zoom(self, factor: float):
        """
        Zoom camera by scaling distance from target.
        
        Args:
            factor: Zoom factor (< 1 = zoom in, > 1 = zoom out)
        """
        direction = self.position - self.target
        distance = np.linalg.norm(direction)
        new_distance = np.clip(distance * factor, 10.0, self.track_radius * 3.0)
        
        if distance > 0:
            self.position = self.target + direction * (new_distance / distance)
            self._update_vectors()
    
    def pan(self, delta_right: float, delta_up: float):
        """
        Pan camera parallel to view plane.
        
        Args:
            delta_right: Movement in view right direction
            delta_up: Movement in view up direction
        """
        move_vector = self.right * delta_right + self.up * delta_up
        self.position += move_vector
        self.target += move_vector
        self.track_center += move_vector
        
        self._update_vectors()
    
    def follow_car(self, car_position: np.ndarray, time_delta: float, 
                   follow_speed: float = 2.0):
        """
        Smoothly follow a car position.
        
        Args:
            car_position: Current car world position
            time_delta: Frame time delta
            follow_speed: How quickly camera follows (higher = faster)
        """
        # Target position: above and behind car
        desired_offset = np.array([-20.0, 10.0, -10.0], dtype=np.float32)
        desired_position = car_position + desired_offset
        
        # Smooth interpolation
        lerp_factor = 1.0 - np.exp(-follow_speed * time_delta)
        self.position = self.position + (desired_position - self.position) * lerp_factor
        
        # Look at car
        self.target = car_position
        self.track_center = car_position  # Update track center for orbit reference
        
        self._update_vectors()
    
    def update_projection(self, width: int, height: int):
        """Update aspect ratio when window resizes."""
        self.aspect = width / height if height > 0 else 1.0
    
    def get_view_matrix(self) -> np.ndarray:
        """Get current view matrix."""
        return look_at(self.position, self.target, self.up)
    
    def get_projection_matrix(self) -> np.ndarray:
        """Get current projection matrix."""
        return perspective(self.fov, self.aspect, self.near, self.far)
    
    def get_view_projection(self) -> np.ndarray:
        """Get combined view-projection matrix."""
        view = self.get_view_matrix()
        proj = self.get_projection_matrix()
        return proj @ view
    
    def screen_to_world(self, screen_x: float, screen_y: float, 
                       screen_width: int, screen_height: int,
                       depth: float = 0.0) -> np.ndarray:
        """
        Convert screen coordinates to world space.
        
        Args:
            screen_x: X coordinate in screen space
            screen_y: Y coordinate in screen space
            screen_width: Window width
            screen_height: Window height
            depth: Distance from camera plane
            
        Returns:
            World space position
        """
        # Normalize screen coordinates
        x = (2.0 * screen_x) / screen_width - 1.0
        y = 1.0 - (2.0 * screen_y) / screen_height
        
        # Combine matrices
        vp = self.get_view_projection()
        inv_vp = np.linalg.inv(vp)
        
        # Create clip space point
        clip_pos = np.array([x * depth, y * depth, depth, 1.0], dtype=np.float32)
        
        # Transform to world space
        world_pos = inv_vp @ clip_pos
        world_pos = world_pos / world_pos[3]  # Perspective divide
        
        return world_pos[:3]


class DebugCamera(Camera3D):
    """Camera with debug visualization capabilities."""
    
    def draw_frustum(self):
        """Draw camera frustum for debugging (can be used with debug draw)."""
        # Calculate frustum corners
        corners = self._calculate_frustum_corners()
        
        # This would integrate with a debug drawing system
        # For now, return the corner data
        return corners
    
    def _calculate_frustum_corners(self) -> np.ndarray:
        """Calculate frustum corner positions in world space."""
        # Get inverse VP matrix
        vp = self.get_view_projection()
        inv_vp = np.linalg.inv(vp)
        
        corners = []
        for x in [-1, 1]:
            for y in [-1, 1]:
                for z in [0, 1]:  # Near and far planes
                    clip_pos = np.array([x, y, z, 1.0], dtype=np.float32)
                    world_pos = inv_vp @ clip_pos
                    world_pos = world_pos / world_pos[3]
                    corners.append(world_pos[:3])
        
        return np.array(corners)
