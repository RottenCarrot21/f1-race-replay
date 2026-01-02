"""GLFW-based 3D rendering window for F1 race replay."""

import glfw
import numpy as np
from OpenGL.GL import *
from typing import Dict, List, Optional, Any
import logging

from .camera import Camera3D
from .shaders import ShaderManager
from .utils import check_gl_error
from ..track.mesh_builder import TrackMeshBuilder

logger = logging.getLogger(__name__)


class F13DWindow:
    """3D rendering window for F1 race replay visualization."""
    
    def __init__(self, width: int = 1920, height: int = 1080, 
                 title: str = "F1 Race Replay 3D"):
        self.width = width
        self.height = height
        self.title = title
        
        # Initialize GLFW
        if not glfw.init():
            raise RuntimeError("Failed to initialize GLFW")
        
        # Configure OpenGL context
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, True)  # For macOS
        
        # Create window
        self.window = glfw.create_window(width, height, title, None, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError("Failed to create GLFW window")
        
        # Make context current
        glfw.make_context_current(self.window)
        
        # Enable VSync
        glfw.swap_interval(1)
        
        # Setup callbacks
        self._setup_callbacks()
        
        # Initialize OpenGL state
        self._init_opengl_state()
        
        # Initialize components
        self.camera = Camera3D(width, height)
        self.shader_manager = ShaderManager()
        self.track_mesh = None
        self.track_bounds = None
        
        # Create fallback shader for testing
        self._create_fallback_shaders()
        
        # Data
        self.frames = []
        self.driver_data = {}
        self.current_frame = 0
        self.is_playing = False
        self.playback_speed = 1.0
        
        # Timing
        self.last_time = glfw.get_time()
        self.frame_time = 0.0
        
        # Track loading status
        self.track_loaded = False
        
        logger.info(f"3D window created: {width}x{height}")
    
    def _setup_callbacks(self):
        """Setup GLFW input callbacks."""
        glfw.set_window_size_callback(self.window, self._on_resize)
        glfw.set_key_callback(self.window, self._on_key)
        glfw.set_mouse_button_callback(self.window, self._on_mouse_button)
        glfw.set_cursor_pos_callback(self.window, self._on_mouse_move)
        glfw.set_scroll_callback(self.window, self._on_scroll)
    
    def _init_opengl_state(self):
        """Initialize OpenGL rendering state."""
        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        
        # Enable blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Enable face culling (for performance)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        
        # Set clear color (dark sky)
        glClearColor(0.05, 0.05, 0.1, 1.0)
    
    def _on_resize(self, window, width, height):
        """Handle window resize."""
        self.width = width
        self.height = height
        glViewport(0, 0, width, height)
        self.camera.update_projection(width, height)
    
    def _on_key(self, window, key, scancode, action, mods):
        """Handle keyboard input."""
        if action == glfw.PRESS or action == glfw.REPEAT:
            if key == glfw.KEY_SPACE:
                self.is_playing = not self.is_playing
            elif key == glfw.KEY_R:
                self.current_frame = 0
            elif key == glfw.KEY_ESCAPE:
                glfw.set_window_should_close(window, True)
            elif key == glfw.KEY_EQUAL or key == glfw.KEY_KP_ADD:
                self.playback_speed = min(self.playback_speed * 1.5, 8.0)
            elif key == glfw.KEY_MINUS or key == glfw.KEY_KP_SUBTRACT:
                self.playback_speed = max(self.playback_speed / 1.5, 0.1)
    
    def _on_mouse_button(self, window, button, action, mods):
        """Handle mouse button input."""
        if button == glfw.MOUSE_BUTTON_LEFT:
            self.camera_dragging = (action == glfw.PRESS)
            if self.camera_dragging:
                self.last_mouse_pos = glfw.get_cursor_pos(window)
    
    def _on_mouse_move(self, window, xpos, ypos):
        """Handle mouse movement."""
        if hasattr(self, 'camera_dragging') and self.camera_dragging:
            if hasattr(self, 'last_mouse_pos'):
                dx = xpos - self.last_mouse_pos[0]
                dy = ypos - self.last_mouse_pos[1]
                
                # Orbit camera
                self.camera.orbit(dx * 0.01, dy * 0.01)
                
                self.last_mouse_pos = (xpos, ypos)
    
    def _on_scroll(self, window, xoffset, yoffset):
        """Handle scroll wheel for zoom."""
        zoom_factor = 1.0 - yoffset * 0.1
        self.camera.zoom(zoom_factor)
    
    def load_track_from_example(self, example_lap):
        """Load and build 3D track from example lap telemetry."""
        logger.info("Loading track data from example lap")
        
        try:
            # Extract track boundaries from existing data
            middle_line = np.column_stack([example_lap['X'].values, 
                                          example_lap['Y'].values])
            
            # For now, use simple track width estimation
            # In a full implementation, we'd use x_inner/y_inner, x_outer/y_outer
            track_width = 15.0  # Typical F1 track width
            
            # Generate inner and outer boundaries
            normals = self._calculate_normals(middle_line)
            inner_boundary = middle_line - normals * (track_width / 2.0)
            outer_boundary = middle_line + normals * (track_width / 2.0)
            
            # Create track mesh
            self.track_mesh = TrackMeshBuilder()
            verts, idxs = self.track_mesh.build_from_boundaries(
                middle_line, inner_boundary, outer_boundary
            )
            
            # Set camera track bounds
            self.camera.set_track_bounds(middle_line)
            
            self.track_loaded = True
            logger.info("Track mesh loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load track: {e}")
            self.track_loaded = False
    
    def _calculate_normals(self, points: np.ndarray) -> np.ndarray:
        """Calculate perpendicular vectors (normals) for each point."""
        normals = []
        
        for i in range(len(points)):
            # Get neighboring points for direction calculation
            prev_idx = max(0, i - 1)
            next_idx = min(len(points) - 1, i + 1)
            
            # Calculate direction vector
            direction = points[next_idx] - points[prev_idx]
            direction = direction / (np.linalg.norm(direction) + 0.001)
            
            # Perpendicular (normal) vector
            normal = np.array([-direction[1], direction[0]])
            normal = normal / (np.linalg.norm(normal) + 0.001)
            
            normals.append(normal)
        
        return np.array(normals)
    
    def load_race_data(self, frames: List[Dict], driver_colors: Dict[str, tuple]):
        """Load race telemetry data."""
        self.frames = frames
        self.driver_colors = driver_colors
        
        # Initialize driver data
        for frame in frames:
            for driver_no, data in frame.items():
                if driver_no not in self.driver_data:
                    self.driver_data[driver_no] = {
                        'positions': [],
                        'speeds': [],
                        'drs_active': [],
                        'colors': driver_colors.get(driver_no, (1.0, 0.0, 0.0))
                    }
        
        logger.info(f"Loaded {len(frames)} frames for {len(self.driver_data)} drivers")
    
    def _update_playback(self):
        """Update animation playback."""
        if self.is_playing and self.frames:
            self.current_frame += self.playback_speed * self.frame_time * 25.0  # 25 FPS
            
            if self.current_frame >= len(self.frames):
                self.current_frame = 0
            elif self.current_frame < 0:
                self.current_frame = len(self.frames) - 1
    
    def render_frame(self):
        """Render a single frame."""
        # Clear buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Update time
        current_time = glfw.get_time()
        self.frame_time = current_time - self.last_time
        self.last_time = current_time
        
    def _create_fallback_shaders(self):
        """Create basic fallback shaders for testing if track shader fails to load."""
        try:
            # Try to load track shader
            import os
            shader_dir = "src/assets/shaders"
            track_vert_path = os.path.join(shader_dir, "track.vert.glsl")
            track_frag_path = os.path.join(shader_dir, "track.frag.glsl")
            
            if os.path.exists(track_vert_path) and os.path.exists(track_frag_path):
                program = self.shader_manager.load_program(
                    "track", "track.vert.glsl", "track.frag.glsl"
                )
                if program > 0:
                    logger.info("Track shader loaded successfully")
                    return
            else:
                logger.warning("Track shader files not found, falling back to basic shader")
                
        except Exception as e:
            logger.warning(f"Failed to load track shader: {e}, using fallback")
        
        # Create simple fallback shader using the shader manager's loading mechanism
        # but with embedded source code
        try:
            # Simple fallback shaders
            fallback_vert = "#version 330 core\nlayout(location = 0) in vec3 aPos;\nuniform mat4 mvp;\nvoid main() { gl_Position = mvp * vec4(aPos, 1.0); }"
            fallback_frag = "#version 330 core\nout vec4 FragColor;\nvoid main() { FragColor = vec4(0.3, 0.3, 0.3, 1.0); }"
            
            # Use utility function to create program
            from .utils import create_program
            program = create_program(fallback_vert, fallback_frag)
            if program > 0:
                self.shader_manager.programs["track"] = program
                logger.info("Fallback shader created successfully")
            else:
                logger.error("Failed to create fallback shader via create_program")
        except Exception as e:
            logger.error(f"Failed to create fallback shader with error: {e}")
    
    def _update_playback(self):
        
        # Render track
        if self.track_mesh and self.track_loaded:
            self._render_track()
        
        # Render cars
        if self.frames and self.current_frame < len(self.frames):
            self._render_cars()
        
        # Render UI overlay
        self._render_ui()
    
    def _render_track(self):
        """Render the 3D track."""
        # TODO: Load and use proper track shader
        # For now, use a simple default shader
        program = self.shader_manager.get_program("track")
        if program == 0:
            logger.warning("Track shader not available, skipping track render")
            return
        
        glUseProgram(program)
        
        # Set uniforms
        vp_matrix = self.camera.get_view_projection()
        model_matrix = np.eye(4, dtype=np.float32)
        
        glUniformMatrix4fv(glGetUniformLocation(program, "projection"), 1, GL_FALSE, 
                          self.camera.get_projection_matrix())
        glUniformMatrix4fv(glGetUniformLocation(program, "view"), 1, GL_FALSE, 
                          self.camera.get_view_matrix())
        glUniformMatrix4fv(glGetUniformLocation(program, "model"), 1, GL_FALSE, model_matrix)
        
        # Lighting
        glUniform3f(glGetUniformLocation(program, "cameraPos"), 
                   self.camera.position[0], self.camera.position[1], self.camera.position[2])
        glUniform1f(glGetUniformLocation(program, "time"), self.last_time)
        
        # Render track mesh
        self.track_mesh.render()
        
        glUseProgram(0)
    
    def _render_cars(self):
        """Render cars as spheres."""
        current_frame_data = self.frames[int(self.current_frame)]
        
        # TODO: Implement instanced car rendering
        # For now, just draw debug points
        glPointSize(8.0)
        glBegin(GL_POINTS)
        
        for driver_no, data in current_frame_data.items():
            if driver_no in ("weather", "track_status"):
                continue
                
            if "X" in data and "Y" in data:
                color = self.driver_colors.get(driver_no, (1.0, 1.0, 1.0))
                glColor3f(*color)
                glVertex3f(data["X"], 1.0, data["Y"])  # Y is height, Z is track Y
        
        glEnd()
    
    def _render_ui(self):
        """Render UI overlay."""
        # TODO: Implement proper text rendering
        # For now, just set up for future UI
        pass
    
    def should_close(self) -> bool:
        """Check if window should close."""
        return glfw.window_should_close(self.window)
    
    def swap_buffers(self):
        """Swap front and back buffers."""
        glfw.swap_buffers(self.window)
    
    def poll_events(self):
        """Process pending events."""
        glfw.poll_events()
    
    def close(self):
        """Clean up and close window."""
        if hasattr(self, 'track_mesh'):
            self.track_mesh.cleanup()
        
        if hasattr(self, 'shader_manager'):
            self.shader_manager.cleanup()
        
        if hasattr(self, 'window'):
            glfw.destroy_window(self.window)
        
        glfw.terminate()
        logger.info("3D window closed")


def create_3d_window(**kwargs) -> F13DWindow:
    """Factory function to create a 3D rendering window."""
    return F13DWindow(**kwargs)